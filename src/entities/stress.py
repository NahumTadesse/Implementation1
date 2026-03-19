from dataclasses import dataclass
import math

@dataclass
class Stress:
    start_min: int
    duration_min: int
    level: float   # 0.0 to 1.0


def stress_glucose_delta(
    t_min: int,
    stress: "Stress",
    max_effect_mgdl: float = 25.0,
    tau_rise_min: float = 30.0,
    tau_decay_min: float = 45.0,
) -> float:


    if stress is None or stress.level <= 0:
        return 0.0

    start = stress.start_min
    end = stress.start_min + stress.duration_min

    if t_min < start:
        return 0.0


    if t_min <= end:
        u = t_min - start
        rise = 1.0 - math.exp(-u / tau_rise_min)
        return max_effect_mgdl * stress.level * rise


    peak = max_effect_mgdl * stress.level * (
        1.0 - math.exp(-stress.duration_min / tau_rise_min)
    )
    v = t_min - end
    return peak * math.exp(-v / tau_decay_min)