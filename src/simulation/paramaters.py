from dataclasses import dataclass

@dataclass
class SimParameters:
    dt_min: int
    horizon_min: int