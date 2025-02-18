from fastapi import WebSocket
from typing import Set, Dict
from game_logic import GameState
import asyncio
import logging
from starlette.websockets import WebSocketState
import logging
from pattern_manager import PatternManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class GameManager:
    def __init__(self):
        self.game_state = GameState()
        self.connections: Dict[WebSocket, bool] = {}  # WebSocket -> active state
        self.timer = 5
        self.timer_lock = asyncio.Lock()
        self.state_lock = asyncio.Lock()
        self.pattern_manager = PatternManager()

        pattern = self.pattern_manager.get_random_pattern(min_difficulty=1, max_difficulty=5)
        self.game_state.initialize_obstacles(pattern.rle)

        self.current_pattern = pattern

    async def reset_game(self):
        """Reset the game with a new random pattern and broadcast the reset"""
        try:
            # First acquire state lock
            async with self.state_lock:
                await self._perform_reset()
                # Broadcast reset in separate try block to ensure game state is reset even if broadcast fails
                try:
                    await self._broadcast_reset()
                except Exception as broadcast_error:
                    logging.error(f"Error broadcasting reset: {broadcast_error}")
                    # Continue even if broadcast fails - game state is still reset
                    
        except Exception as e:
            logging.error(f"Error in reset_game: {e}")
            raise

    async def force_reset(self):
        """Emergency reset without broadcasting - used for recovery"""
        async with self.state_lock:
            await self._perform_reset()
            logging.info("Forced game reset completed")

    async def _perform_reset(self):
        """Internal method to perform the actual reset operations"""
        # Create new game state
        self.game_state = GameState()
        
        # Get new random pattern
        pattern = self.pattern_manager.get_random_pattern(min_difficulty=1, max_difficulty=5)
        self.game_state.initialize_obstacles(pattern.rle)
        self.current_pattern = pattern
        
        # Reset timer
        async with self.timer_lock:
            self.timer = 5

    async def _broadcast_reset(self):
        """Internal method to handle reset broadcasting"""
        # Prepare reset message
        reset_message = {
            "type": "game_reset",
            "pattern_info": {
                "name": self.current_pattern.name,
                "description": self.current_pattern.description,
                "difficulty": self.current_pattern.difficulty
            }
        }
        
        # Broadcast messages with individual timeouts
        broadcast_timeout = 2.0  # 2 second timeout for each broadcast
        
        try:
            # Send reset notification
            async with asyncio.timeout(broadcast_timeout):
                await self.broadcast_message(reset_message)
            
            # Short delay to ensure clients process reset
            await asyncio.sleep(0.1)
            
            async with asyncio.timeout(broadcast_timeout):
                await self.broadcast_state()
                
        except TimeoutError as e:
            logging.error(f"Broadcast timeout during reset: {e}")
        except Exception as e:
            logging.error(f"Error broadcasting reset: {e}")

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        self.connections[websocket] = True
        try:
            await self.send_state_update(websocket)
        except Exception as e:
            logging.error(f"Error in initial state update: {e}")
            await self.handle_disconnect(websocket)
    
    async def handle_disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.connections:
            self.connections[websocket] = False
            del self.connections[websocket]
    
    def is_connected(self, websocket: WebSocket) -> bool:
        """Check if a WebSocket is still connected"""
        return (websocket in self.connections and 
                self.connections[websocket] and 
                websocket.client_state == WebSocketState.CONNECTED)
    
    async def add_player_point(self, x: int, y: int):
        """Add player point and broadcast update if successful"""
        async with self.state_lock:
            if self.game_state.add_player_point(x, y):
                await self.broadcast_state()
    
    async def update_game(self):
        """Update game state with proper locking and logging"""
        try:
            async with asyncio.timeout(1.0):  # 1 second timeout for acquiring lock
                async with self.state_lock:
                    try:
                        self.game_state.update_state_tactical()
                        
                        async with self.timer_lock:
                            self.timer = 5
                        
                        await self.broadcast_state()
                        
                    except Exception as e:
                        logging.error(f"Error in game state update: {e}")
                        raise
                    
        except TimeoutError:
            logging.error("Timeout while acquiring state lock")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in update_game: {e}")
            raise
    
    async def update_timer(self, time: int):
        """Update timer value with proper error handling"""
        try:
            async with self.timer_lock:
                self.timer = time
            await self.broadcast_timer()
        except Exception as e:
            logging.error(f"Error updating timer: {e}")
            raise
    
    async def broadcast_timer(self):
        """Light-weight broadcast of just the timer"""
        message = {
            "type": "timer_update",
            "timer": self.timer
        }
        await self.broadcast_message(message)
    
    async def broadcast_state(self):
        """Send full state update to all clients with improved performance"""
        if not self.connections:
            return
            
        try:
            # Prepare message outside of the connection loop
            state = self.game_state.get_state().tolist()
            
            # Calculate stats once
            red_score = sum(row.count(1) for row in state)
            blue_score = sum(row.count(2) for row in state)
            total_cells = len(state) * len(state[0])
            occupied_cells = red_score + blue_score
            territory_control = (occupied_cells / total_cells) * 100 if total_cells > 0 else 0
            
            red_clusters = self._count_clusters(state, 1)
            blue_clusters = self._count_clusters(state, 2)
            
            message = {
                "type": "grid_update",
                "grid": state,
                "scores": {
                    "red": red_score,
                    "blue": blue_score
                },
                "stats": {
                    "territory_control": round(territory_control, 2),
                    "red_clusters": red_clusters,
                    "blue_clusters": blue_clusters,
                    "activity": self.game_state.get_changes_count(),
                    "current_round": self.game_state.round_count,
                    "points_placed": self.game_state.points_placed,
                    "last_update": self.game_state.last_update_time.isoformat() if self.game_state.last_update_time else None
                },
                "timer": self.timer,
                "game_over": self.game_state.game_over
            }
            
            if self.game_state.game_over and self.game_state.final_stats:
                message["final_stats"] = self.game_state.final_stats
            
            # Use gather with return_exceptions=True for parallel sends
            tasks = []
            for websocket in list(self.connections.keys()):
                if self.is_connected(websocket):
                    tasks.append(self.send_message_to_client(websocket, message))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any failed sends
                for websocket, result in zip(self.connections.keys(), results):
                    if isinstance(result, Exception):
                        logging.error(f"Failed to send to client: {result}")
                        await self.handle_disconnect(websocket)
                        
        except Exception as e:
            logging.error(f"Error in broadcast_state: {e}")
            raise

    async def send_message_to_client(self, websocket: WebSocket, message):
        """Helper method to send a message to a single client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logging.error(f"Error sending to client: {e}")
            raise


    async def broadcast_message(self, message):
        """Generic broadcast helper with improved WebSocket state handling"""
        if not self.connections:
            return
            
        dead_connections = set()
        for websocket in self.connections.keys():
            if not self.is_connected(websocket):
                dead_connections.add(websocket)
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                logging.error(f"Error sending to client: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            await self.handle_disconnect(websocket)
    
    async def send_state_update(self, websocket: WebSocket):
        """Send current game state to specific client with error handling"""
        if not self.is_connected(websocket):
            await self.handle_disconnect(websocket)
            return
            
        try:
            state = self.game_state.get_state().tolist()
            await websocket.send_json({
                "type": "grid_update",
                "grid": state,
                "timer": self.timer
            })
        except Exception as e:
            logging.error(f"Error in send_state_update: {e}")
            await self.handle_disconnect(websocket)

    def _count_clusters(self, state, cell_type):
        """Count number of connected clusters of the given cell type"""
        if not state or not state[0]:
            return 0
            
        height = len(state)
        width = len(state[0])
        visited = set()
        clusters = 0

        def explore_cluster(y, x):
            if (y, x) in visited:
                return
            
            visited.add((y, x))
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    new_y, new_x = y + dy, x + dx
                    if (0 <= new_y < height and 
                        0 <= new_x < width and 
                        state[new_y][new_x] == cell_type and 
                        (new_y, new_x) not in visited):
                        explore_cluster(new_y, new_x)

        for y in range(height):
            for x in range(width):
                if state[y][x] == cell_type and (y, x) not in visited:
                    clusters += 1
                    explore_cluster(y, x)

        return clusters