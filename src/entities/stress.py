from dataclasses import dataclass

@dataclass
class Stress:
    start_min: int
    duration_min: int
    multiplier: float