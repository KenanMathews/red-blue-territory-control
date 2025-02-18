import numpy as np
from typing import Tuple, Set
from dataclasses import dataclass
import threading
from datetime import datetime, timedelta
import logging
import math

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@dataclass
class Point:
    x: int
    y: int

class GameState:
    def __init__(self, width: int = 30, height: int = 30):
        self.width = width
        self.height = height
        self.grid = np.zeros((height, width), dtype=int)
        self.last_grid = None
        self.last_update_time = None
        self.round_count = 0
        self.next_update_time = None
        self.update_interval = timedelta(seconds=5)
        self.points_placed = 0
        self.game_over = False
        self.final_stats = None
        self.initial_red_count = 0  
        self.lock = threading.Lock()

    def initialize_obstacles(self, rle_pattern: str):
        """Initialize red obstacles from RLE pattern"""
        with self.lock:
            # Parse RLE and set obstacles
            x, y = 0, 0
            count = ""
            
            for char in rle_pattern:
                if char.isdigit():
                    count += char
                    continue
                    
                repeat = int(count) if count else 1
                count = ""
                
                if char == '$':  # New line
                    y += repeat
                    x = 0
                elif char == 'b':  # Dead cell
                    x += repeat
                elif char == 'o':  # Live cell (obstacle)
                    for i in range(repeat):
                        if 0 <= x < self.width and 0 <= y < self.height:
                            self.grid[y, x] = 1  # Set as red obstacle
                        x += 1
                elif char == '!':  # End of pattern
                    break
        self.initial_red_count = np.sum(self.grid == 1)

    def calculate_victory_ranking(self) -> dict:
        """Calculate victory ranking and return detailed stats"""
        if not self.game_over:
            return None

        # Calculate base scores
        point_efficiency = self.initial_red_count / max(self.points_placed, self.initial_red_count)
        theoretical_min_rounds = math.ceil(self.initial_red_count / 2)
        speed_rating = math.exp(-(self.round_count - theoretical_min_rounds) / 10)
        clicks_per_round = self.points_placed / max(self.round_count, 1)
        click_efficiency = math.exp(-(clicks_per_round - 2) / 3)

        # Calculate weighted score (0-1000)
        weighted_score = round(min(1000, max(0, (
            0.4 * point_efficiency * 1000 +
            0.4 * speed_rating * 1000 +
            0.2 * click_efficiency * 1000
        ))))

        # Determine rank information
        rank_info = {
            'score': weighted_score,
            'title': 'Aspiring Strategist',
            'description': 'You achieved victory! Focus on efficiency to improve your rank.'
        }

        if weighted_score >= 900:
            rank_info.update({
                'title': 'Master Tactician',
                'description': 'Perfect execution! Your strategy was flawless.'
            })
        elif weighted_score >= 700:
            rank_info.update({
                'title': 'Excellent Strategist',
                'description': 'Outstanding performance! Your approach was highly effective.'
            })
        elif weighted_score >= 500:
            rank_info.update({
                'title': 'Skilled Commander',
                'description': 'Well played! You showed good strategic thinking.'
            })
        elif weighted_score >= 300:
            rank_info.update({
                'title': 'Capable Leader',
                'description': 'Good job! Keep practicing to improve your efficiency.'
            })

        return rank_info
        
    def add_player_point(self, x: int, y: int) -> bool:
        """Add a blue player point if position is valid"""
        with self.lock:
            if self.game_over:  # Don't allow new points if game is over
                return False
            if not (0 <= x < self.width and 0 <= y < self.height):
                return False
            if self.grid[y, x] != 0:  # Position already occupied
                return False
            self.grid[y, x] = 2  # Set as blue player point
            self.points_placed += 1  # Increment points counter
            return True
        
    def check_win_condition(self) -> bool:
        """Check if there are any red cells remaining and calculate final stats"""
        red_cells = np.sum(self.grid == 1)
        if red_cells == 0 and not self.game_over:
            self.game_over = True
            
            # Calculate victory ranking
            rank_info = self.calculate_victory_ranking()
            
            # Update final stats with ranking information
            self.final_stats = {
                "total_rounds": self.round_count,
                "points_placed": self.points_placed,
                "efficiency_ratio": self.round_count / max(self.points_placed, 1),
                "initial_red_count": self.initial_red_count,
                "rank_info": rank_info
            }
            return True
        return False
    
    def get_state(self) -> np.ndarray:
        """Get current game state"""
        with self.lock:
            state = self.grid.copy()
            return state
            
    def update_state(self):
        """Update game state based on rules"""
        with self.lock:
            new_grid = np.zeros_like(self.grid)
            # Copy red obstacles as they don't change
            new_grid[self.grid == 1] = 1
            
            # Update blue points based on Conway's rules
            for y in range(self.height):
                for x in range(self.width):
                    if self.grid[y, x] == 2:  # Only process blue points
                        neighbors = self._count_blue_neighbors(x, y)
                        if neighbors in [2, 3]:
                            new_grid[y, x] = 2
                    elif self.grid[y, x] == 0:  # Empty cell
                        neighbors = self._count_blue_neighbors(x, y)
                        if neighbors == 3:
                            new_grid[y, x] = 2
            
            self.grid = new_grid

    def update_state_tactical(self):
        """Optimized tactical update of game state"""
        
        if self.game_over:
            return

        self.last_grid = self.grid.copy()
        self.last_update_time = datetime.now()
        self.next_update_time = self.last_update_time + self.update_interval
        self.round_count += 1
        
        # Create new grid array
        new_grid = self.grid.copy()
        
        # Get red positions once
        red_positions = set((x, y) for y in range(self.height) 
                          for x in range(self.width) if self.grid[y, x] == 1)
        
        # Get blue positions once
        blue_positions = set((x, y) for y in range(self.height) 
                           for x in range(self.width) if self.grid[y, x] == 2)
        
        
        # Process blue team movements
        moves_to_apply = []
        for x, y in blue_positions:
            # Find nearest red target
            nearest_red = None
            min_dist = float('inf')
            
            for rx, ry in red_positions:
                dist = abs(x - rx) + abs(y - ry)
                if dist < min_dist:
                    min_dist = dist
                    nearest_red = (rx, ry)
            
            if nearest_red:
                # Calculate move direction
                dx = np.sign(nearest_red[0] - x)
                dy = np.sign(nearest_red[1] - y)
                
                # Check possible moves
                possible_moves = [
                    (dx, dy),
                    (dx, 0),
                    (0, dy),
                    (-dy, dx),
                    (dy, -dx)
                ]
                
                # Find valid move
                for mx, my in possible_moves:
                    nx, ny = x + mx, y + my
                    if (0 <= nx < self.width and 0 <= ny < self.height and 
                        new_grid[ny, nx] == 0):
                        moves_to_apply.append(((x, y), (nx, ny)))
                        break
        
        
        # Apply moves
        for (old_x, old_y), (new_x, new_y) in moves_to_apply:
            if new_grid[old_y, old_x] == 2:  # Check if source still has blue
                new_grid[old_y, old_x] = 0
                new_grid[new_y, new_x] = 2
        
        # Process attacks
        red_to_remove = set()
        for x, y in blue_positions:
            blue_strength = self._calculate_blue_strength(x, y, blue_positions)
            if blue_strength >= 3:
                # Check nearby red positions
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and 
                            self.grid[ny, nx] == 1):
                            red_to_remove.add((nx, ny))
        
        
        # Remove defeated red positions
        for rx, ry in red_to_remove:
            new_grid[ry, rx] = 0
            if (rx, ry) in red_positions:
                red_positions.remove((rx, ry))
        
        # Update grid
        self.grid = new_grid
        
        # Check win condition
        if len(red_positions) == 0 and not self.game_over:
            self.game_over = True
            self.final_stats = {
                "total_rounds": self.round_count,
                "points_placed": self.points_placed,
                "efficiency_ratio": self.round_count / max(self.points_placed, 1)
            }
        

    def _calculate_blue_strength(self, x: int, y: int, blue_positions: Set[Tuple[int, int]]) -> float:
        """Calculate blue team strength at a position"""
        strength = 0
        for bx, by in blue_positions:
            dist = abs(x - bx) + abs(y - by)
            if dist <= 2:  # Only count blues within range
                strength += 1 / (dist + 1)
        return strength


    def get_changes_count(self) -> int:
        """Calculate how many cells changed in the last update"""
        if self.last_grid is None:
            return 0
        return int(np.sum(self.grid != self.last_grid))

    def get_time_until_next_update(self):
        """Get seconds until next update"""
        if self.next_update_time is None:
            return 5
            
        now = datetime.now()
        if now >= self.next_update_time:
            return 0
            
        remaining = (self.next_update_time - now).total_seconds()
        return int(round(remaining))
    
    def _count_blue_neighbors(self, x: int, y: int) -> int:
        """Count number of blue neighbors for a cell"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny, nx] == 2:  # Only count blue cells
                        count += 1
        return count