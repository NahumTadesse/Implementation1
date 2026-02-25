from dataclasses import dataclass

@dataclass
class InsulinDose:
    time_min: int
    units: float