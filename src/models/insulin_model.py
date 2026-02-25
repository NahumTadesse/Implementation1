import math
from typing import List
from entities.person import Person
from entities.insulin import InsulinDose

def compute_bolus_units_from_carbs(person: Person, carbs_g: float) -> float:
    return carbs_g / person.carb_ratio_g_per_unit

def insulin_I_t(person: Person, t_min: int, doses: List[InsulinDose]) -> float:
    total_signal = 0.0
    for d in doses:
        if t_min >= d.time_min:
            dt = t_min - d.time_min
            I0 = d.units * person.insulin_signal_per_unit
            total_signal += I0 * math.exp(-person.ke_per_min * dt)
    return total_signal