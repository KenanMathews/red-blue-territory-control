import random
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class GamePattern:
    name: str
    description: str
    difficulty: int  # 1-5, where 5 is most difficult
    rle: str
    min_grid_size: tuple[int, int]  # minimum (width, height) needed

class PatternManager:
    def __init__(self):
        self.patterns: List[GamePattern] = [
            GamePattern(
                name="Simple Blocks",
                description="A series of small block formations scattered across the grid",
                difficulty=1,
                rle="2o$2o5$7o$7o5$12o$12o5$17o$17o!",
                min_grid_size=(20, 20)
            ),
            GamePattern(
                name="Spiral Challenge",
                description="A spiral pattern that requires strategic elimination",
                difficulty=3,
                rle="2o$2o2$4o$4o2$6o$6o2$8o$8o2$10o$10o2$12o$12o!",
                min_grid_size=(25, 25)
            ),
            GamePattern(
                name="Fortress",
                description="A fortified structure with multiple layers",
                difficulty=4,
                rle="4o$o2bo$o2bo$4o3$6o$o4bo$o4bo$6o!",
                min_grid_size=(30, 30)
            ),
            GamePattern(
                name="Scattered Outposts",
                description="Multiple small fortifications that must be eliminated",
                difficulty=2,
                rle="2o2$2o5$7o2$7o5$12o2$12o!",
                min_grid_size=(20, 20)
            ),
            GamePattern(
                name="Diamond Formation",
                description="A diamond-shaped pattern requiring careful strategy",
                difficulty=3,
                rle="2bo$3bo$o3bo$5o2$5o$o3bo$3bo$2bo!",
                min_grid_size=(25, 25)
            ),
            GamePattern(
                name="Maze Runner",
                description="A maze-like pattern that tests tactical thinking",
                difficulty=5,
                rle="20o$o18bo$o3bo10bo3bo$o3bo10bo3bo$o3bo10bo3bo$o18bo$20o!",
                min_grid_size=(30, 30)
            ),
            GamePattern(
                name="Cross Roads",
                description="Intersecting lines creating a cross pattern",
                difficulty=2,
                rle="2bo$2bo$2bo$5o$2bo$2bo$2bo!",
                min_grid_size=(20, 20)
            ),
            GamePattern(
                name="Corner Fortress",
                description="Strong fortifications in each corner",
                difficulty=4,
                rle="3o2$o2bo2$3o7$14o2$12bo2bo2$14o!",
                min_grid_size=(30, 30)
            ),
        ]

    def get_random_pattern(self, min_difficulty: int = 1, max_difficulty: int = 5) -> GamePattern:
        """Get a random pattern within the specified difficulty range."""
        valid_patterns = [p for p in self.patterns 
                         if min_difficulty <= p.difficulty <= max_difficulty]
        if not valid_patterns:
            raise ValueError(f"No patterns found with difficulty between {min_difficulty} and {max_difficulty}")
        return random.choice(valid_patterns)

    def get_pattern_by_name(self, name: str) -> GamePattern:
        """Get a specific pattern by name."""
        for pattern in self.patterns:
            if pattern.name.lower() == name.lower():
                return pattern
        raise ValueError(f"Pattern '{name}' not found")

    def get_all_patterns(self) -> List[GamePattern]:
        """Get all available patterns."""
        return self.patterns.copy()

    def get_patterns_by_difficulty(self, difficulty: int) -> List[GamePattern]:
        """Get all patterns of a specific difficulty level."""
        return [p for p in self.patterns if p.difficulty == difficulty]

    def add_pattern(self, pattern: GamePattern) -> None:
        """Add a new pattern to the collection."""
        # Validate pattern
        if any(p.name.lower() == pattern.name.lower() for p in self.patterns):
            raise ValueError(f"Pattern with name '{pattern.name}' already exists")
        if not 1 <= pattern.difficulty <= 5:
            raise ValueError("Difficulty must be between 1 and 5")
        if not pattern.rle:
            raise ValueError("RLE pattern cannot be empty")
        
        self.patterns.append(pattern)