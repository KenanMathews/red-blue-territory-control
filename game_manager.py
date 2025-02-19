from fastapi import WebSocket
from typing import Set, Dict, Optional
from game_logic import GameState
import asyncio
import logging
from starlette.websockets import WebSocketState
import logging
from pattern_manager import PatternManager
import random

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
        self.game_loop: Optional[asyncio.Task] = None

        self.current_pattern = self.game_state.initialize_obstacles(random.randint(1, 8))['rle']

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
        self.current_pattern = self.game_state.initialize_obstacles(random.randint(1, 8))['rle']
        
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
        """Handle new WebSocket connection and start game loop if first connection"""
        await websocket.accept()
        self.connections[websocket] = True
        config_message = {
            "type": "grid_config",
            "grid_size": self.game_state.grid_size,
        }
        await websocket.send_json(config_message)
        
        # Start game loop if this is the first connection
        if len(self.connections) == 1 and (self.game_loop is None or self.game_loop.done()):
            self.game_loop = asyncio.create_task(self.update_game_loop())
        
        try:
            await self.send_state_update(websocket)
        except Exception as e:
            logging.error(f"Error in initial state update: {e}")
            await self.handle_disconnect(websocket)

    
    async def handle_disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection and cleanup game loop if no connections remain"""
        if websocket in self.connections:
            self.connections[websocket] = False
            del self.connections[websocket]
            
            # If this was the last connection, cancel the game loop
            if not self.connections and self.game_loop and not self.game_loop.done():
                self.game_loop.cancel()
                try:
                    await self.game_loop
                except asyncio.CancelledError:
                    pass
                self.game_loop = None
    
    async def update_game_loop(self):
        """Main game loop that updates game state and timer"""
        while True:
            try:
                # Count down from 5 to 0
                for i in range(5, -1, -1):
                    await self.update_timer(i)
                    if i > 0:  # Only sleep if not at 0
                        await asyncio.sleep(1)
                
                # When timer hits 0, update game state
                try:
                    if self.game_state.game_over:
                        async with asyncio.timeout(5.0):
                            await self.reset_game()
                    else:
                        async with asyncio.timeout(2.0):
                            await self.update_game()
                            
                            if self.game_state.game_over:
                                await self.broadcast_state()
                                await asyncio.sleep(5)
                                async with asyncio.timeout(5.0):
                                    await self.reset_game()
                            
                except TimeoutError as e:
                    logging.error(f"Operation timed out: {str(e)}")
                    if self.game_state.game_over:
                        try:
                            async with asyncio.timeout(5.0):
                                await self.force_reset()
                        except Exception as reset_error:
                            logging.error(f"Failed to force reset: {reset_error}")
                except Exception as e:
                    logging.error(f"Error in game update: {e}")
                    
            except asyncio.CancelledError:
                logging.info("Game loop cancelled")
                break
            except Exception as e:
                logging.error(f"Unexpected error in game loop: {e}")
                await asyncio.sleep(0.5)
    
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
            # Convert numpy arrays and values to Python native types
            state = self.game_state.get_state().tolist()
            
            # Calculate stats once, converting numpy values to native Python types
            red_score = int(sum(row.count(1) for row in state))
            blue_score = int(sum(row.count(2) for row in state))
            total_cells = int(len(state) * len(state[0]))
            occupied_cells = int(red_score + blue_score)
            territory_control = float((occupied_cells / total_cells) * 100 if total_cells > 0 else 0)
            
            red_clusters = int(self._count_clusters(state, 1))
            blue_clusters = int(self._count_clusters(state, 2))
            
            # Prepare message with all numeric values converted to native Python types
            message = {
                "type": "grid_update",
                "grid": state,
                "grid_size": self.game_state.grid_size,
                "scores": {
                    "red": red_score,
                    "blue": blue_score
                },
                "stats": {
                    "territory_control": round(float(territory_control), 2),
                    "red_clusters": red_clusters,
                    "blue_clusters": blue_clusters,
                    "activity": int(self.game_state.get_changes_count()),
                    "current_round": int(self.game_state.round_count),
                    "points_placed": int(self.game_state.points_placed),
                    "last_update": self.game_state.last_update_time.isoformat() if self.game_state.last_update_time else None
                },
                "timer": int(self.timer),
                "game_over": bool(self.game_state.game_over)
            }
            
            if self.game_state.game_over and self.game_state.final_stats:
                # Convert all numeric values in final_stats to native Python types
                final_stats = self.game_state.final_stats.copy()
                if "stats" in final_stats:
                    stats = final_stats["stats"]
                    final_stats["stats"] = {
                        "total_rounds": int(stats["total_rounds"]),
                        "points_placed": int(stats["points_placed"]),
                        "efficiency_ratio": float(stats["efficiency_ratio"]),
                        "speed_rating": float(stats["speed_rating"]),
                        "clicks_per_round": float(stats["clicks_per_round"]),
                        "click_efficiency": float(stats["click_efficiency"]),
                        "initial_red_count": int(stats["initial_red_count"])
                    }
                message["final_stats"] = final_stats
            
            # Create a list of connections to avoid modification during iteration
            connections = list(self.connections.keys())
            
            # Use gather with return_exceptions=True for parallel sends
            tasks = []
            for websocket in connections:
                if self.is_connected(websocket):
                    tasks.append(self.send_message_to_client(websocket, message))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any failed sends
                for websocket, result in zip(connections, results):
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
            
        # Create a list of connections to avoid modification during iteration
        connections = list(self.connections.keys())
        dead_connections = set()
        
        for websocket in connections:
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