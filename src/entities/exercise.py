from dataclasses import dataclass

@dataclass
class Exercise:
    start_min: int
    duration_min: int
    intensity: float