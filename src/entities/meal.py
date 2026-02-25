from dataclasses import dataclass

@dataclass
class Meal:
    time_min: int
    carbs_g: float
    t_peak_min: int
    duration_min: int