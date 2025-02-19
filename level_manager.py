from typing import Optional, Dict, Tuple
from pattern_manager import PatternManager, GamePattern

class LevelManager:
    def __init__(self):
        self.pattern_manager = PatternManager()
        self.current_pattern_id = 1
        
    def get_current_pattern(self) -> GamePattern:
        """Get the current pattern"""
        return self.pattern_manager.get_pattern_by_id(self.current_pattern_id)

    def reset_to_first_pattern(self):
        """Reset to the first pattern"""
        self.current_pattern_id = 1

    def get_pattern_info(self, level_id: Optional[int] = None) -> Dict:
        """Get information about current or specified pattern"""
        pattern = (self.pattern_manager.get_pattern_by_id(level_id) 
                  if level_id is not None 
                  else self.get_current_pattern())
        
        if not pattern:
            raise ValueError(f"Pattern {level_id} not found")
            
        return {
            "pattern_id": pattern.id,
            "name": pattern.name,
            "description": pattern.description,
            "difficulty": pattern.difficulty,
            "next_pattern_id": pattern.next_pattern_id,
            "min_grid_size": pattern.min_grid_size,
            "rle": pattern.rle
        }

    def get_total_patterns(self) -> int:
        """Get the total number of patterns"""
        return len(self.pattern_manager.patterns)

    def get_progress(self) -> float:
        """Get current progress as a percentage"""
        return (self.current_pattern_id / len(self.pattern_manager.patterns)) * 100

    def get_pattern_dimensions(self, pattern_id: Optional[int] = None) -> Tuple[int, int]:
        """Get the dimensions of current or specified pattern"""
        pattern = (self.pattern_manager.get_pattern_by_id(pattern_id) 
                  if pattern_id is not None 
                  else self.get_current_pattern())
        
        return self.pattern_manager.calculate_pattern_dimensions(pattern)