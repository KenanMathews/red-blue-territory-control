from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random

@dataclass
class GamePattern:
    id: int
    name: str
    description: str
    difficulty: int  # 1-5
    rle: str
    min_grid_size: tuple[int, int]
    tactical_notes: Optional[str] = None  # Additional tactical information
    next_pattern_id: Optional[int] = None

class PatternManager:
    def __init__(self):
        self.patterns: Dict[int, GamePattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize all game patterns optimized for tactical gameplay"""
        from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random

@dataclass
class GamePattern:
    id: int
    name: str
    description: str
    difficulty: int  # 1-5
    rle: str
    min_grid_size: tuple[int, int]
    tactical_notes: Optional[str] = None
    next_pattern_id: Optional[int] = None

class PatternManager:
    def __init__(self):
        self.patterns: Dict[int, GamePattern] = {}
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize all game patterns with denser tactical layouts"""
        self.patterns = {
            1: GamePattern(
                id=1,
                name="Distributed Defense",
                description="Multiple defensive positions spread across the grid",
                difficulty=1,
                rle="3o2b3o2b3o$b2ob2ob2o5$3o2b3o2b3o$3b2ob2ob2o!",  # Multiple groups spread out
                min_grid_size=(20, 20),
                tactical_notes="Learn to coordinate across multiple positions",
                next_pattern_id=2
            ),
            2: GamePattern(
                id=2,
                name="Network Defense",
                description="Interconnected defensive networks",
                difficulty=2,
                rle="3o2bo2b3o$o4bo4bo$3o2bo2b3o5$2o2b3o2b2o$o2b5o2bo$2o2b3o2b2o!",  # Connected positions
                min_grid_size=(20, 20),
                tactical_notes="Practice managing interconnected defensive zones",
                next_pattern_id=3
            ),
            3: GamePattern(
                id=3,
                name="Grid Control",
                description="Strategic control points across the grid",
                difficulty=2,
                rle="2o2b4o$2ob6o$4o2b2o3$b2o2b2o2b2o$3o2b2o2b3o$b2o2b2o2b2o3$2o2b4o$2ob6o$4o2b2o!",
                min_grid_size=(25, 25),
                tactical_notes="Control multiple strategic points",
                next_pattern_id=4
            ),
            4: GamePattern(
                id=4,
                name="Complex Grid",
                description="Multiple fortified positions with support",
                difficulty=3,
                rle="3o2b3o2b3o$o2b2ob2o2bo$3o2b3o2b3o4$2b4o4b$bo6bo$bo6bo$2b4o4b4$3o2b3o2b3o$o2b2ob2o2bo$3o2b3o2b3o!",
                min_grid_size=(30, 30),
                tactical_notes="Coordinate attacks across multiple strongpoints",
                next_pattern_id=5
            ),
            5: GamePattern(
                id=5,
                name="Grid Sectors",
                description="Multiple defensive sectors",
                difficulty=3,
                rle="2o2b2o2b2o2b2o$2ob2ob2ob2ob2o$2o2b2o2b2o2b2o4$b3o4b3o$bo2b4o2bo$b3o4b3o4$2o2b2o2b2o2b2o$2ob2ob2ob2ob2o$2o2b2o2b2o2b2o!",
                min_grid_size=(30, 30),
                tactical_notes="Manage multiple defensive sectors",
                next_pattern_id=6
            ),
            6: GamePattern(
                id=6,
                name="Advanced Grid",
                description="Complex grid-wide defensive system",
                difficulty=4,
                rle="3o2b4o2b3o$o2b2ob2ob2o2bo$3o2b4o2b3o3$2b6o6b$bo2b4o2bo$bo2b4o2bo$2b6o6b3$3o2b4o2b3o$o2b2ob2ob2o2bo$3o2b4o2b3o!",
                min_grid_size=(35, 35),
                tactical_notes="Advanced grid control tactics",
                next_pattern_id=7
            ),
            7: GamePattern(
                id=7,
                name="Fortress Network",
                description="Network of fortified positions",
                difficulty=4,
                rle="4o2b4o2b4o$o3bob4obo3bo$4o2b4o2b4o3$2b3o6b3o$bo2b8o2bo$bo2b8o2bo$2b3o6b3o3$4o2b4o2b4o$o3bob4obo3bo$4o2b4o2b4o!",
                min_grid_size=(35, 35),
                tactical_notes="Coordinate attacks on multiple fortified positions",
                next_pattern_id=8
            ),
            8: GamePattern(
                id=8,
                name="Elite Grid",
                description="Complex grid-wide elite defensive system",
                difficulty=5,
                rle="3o2b5o2b3o$o2b2ob3ob2o2bo$3o2b5o2b3o3$2b8o8b$bo3b6o3bo$bo3b6o3bo$2b8o8b3$3o2b5o2b3o$o2b2ob3ob2o2bo$3o2b5o2b3o4$b4o6b4o$2o2b8o2b2o$b4o6b4o!",
                min_grid_size=(40, 40),
                tactical_notes="Master complex grid-wide tactics",
                next_pattern_id=9
            ),
            9: GamePattern(
                id=9,
                name="Master Grid",
                description="Ultimate grid-wide challenge",
                difficulty=5,
                rle="4o2b6o2b4o$o3bob6obo3bo$4o2b6o2b4o3$2b4o8b4o$bo2b12o2bo$bo2b12o2bo$2b4o8b4o3$4o2b6o2b4o$o3bob6obo3bo$4o2b6o2b4o4$b5o8b5o$2o3b10o3b2o$b5o8b5o!",
                min_grid_size=(45, 45),
                tactical_notes="Ultimate test of grid control",
                next_pattern_id=1
            )
        }

    def get_pattern_by_id(self, pattern_id: int) -> Optional[GamePattern]:
        """Get a specific pattern by ID"""
        return self.patterns.get(pattern_id)

    def get_random_pattern(self, min_difficulty: int = 1, max_difficulty: int = 5) -> GamePattern:
        """Get a random pattern within the specified difficulty range"""
        valid_patterns = [p for p in self.patterns.values() 
                         if min_difficulty <= p.difficulty <= max_difficulty]
        if not valid_patterns:
            raise ValueError(f"No patterns found with difficulty between {min_difficulty} and {max_difficulty}")
        return random.choice(valid_patterns)

    def get_all_patterns(self) -> List[GamePattern]:
        """Get all available patterns"""
        return list(self.patterns.values())

    def get_patterns_by_difficulty(self, difficulty: int) -> List[GamePattern]:
        """Get all patterns of a specific difficulty level"""
        return [p for p in self.patterns.values() if p.difficulty == difficulty]

    def calculate_pattern_dimensions(self, pattern: GamePattern) -> Tuple[int, int]:
        """Calculate the dimensions of a pattern from its RLE string"""
        max_x, max_y = 0, 0
        temp_x, temp_y = 0, 0
        count = ""
        
        for char in pattern.rle:
            if char.isdigit():
                count += char
                continue
                
            repeat = int(count) if count else 1
            count = ""
            
            if char == '$':  # New line
                temp_y += repeat
                temp_x = 0
            elif char == 'b':  # Dead cell
                temp_x += repeat
            elif char == 'o':  # Live cell
                temp_x += repeat
            elif char == '!':  # End of pattern
                break
                
            max_x = max(max_x, temp_x)
            max_y = max(max_y, temp_y)
        
        return max_x, max_y + 1  # Add 1 to y for zero-based indexing
    
    def get_recommended_blue_count(self, pattern: GamePattern) -> int:
        """Get recommended number of blue units based on pattern difficulty and size"""
        dims = self.calculate_pattern_dimensions(pattern)
        base_count = max(3, pattern.difficulty * 2)  # Scale with difficulty
        size_factor = (dims[0] * dims[1]) / 25  # Scale with pattern size
        return min(10, max(3, int(base_count + size_factor)))  # Between 3 and 10 units