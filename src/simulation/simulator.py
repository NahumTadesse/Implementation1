from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from entities import Person, Meal, InsulinDose, Exercise, Stress
from models.minimal_model import MinimalModelState, step_euler
from models.carb_absorption import Rg_mg_per_min
from models.insulin_model import insulin_I_t

@dataclass
class SimulationResult:
    times_dt: List[datetime]
    glucose_mgdl: List[float]

def active_window(t_min: int, start_min: int, duration_min: int) -> bool:
    return start_min <= t_min < (start_min + duration_min)

def run_forecast(
    person: Person,
    start_datetime: datetime,
    start_state: MinimalModelState,
    horizon_min: int,
    dt_min: int,
    meals: List[Meal],
    doses: List[InsulinDose],
    exercise: Optional[Exercise] = None,
    stress: Optional[Stress] = None,
) -> SimulationResult:

    steps = horizon_min // dt_min
    t_min = 0
    now = start_datetime
    state = start_state

    times: List[datetime] = []
    glucose: List[float] = []

    for _ in range(steps):
        t_min += dt_min
        now += timedelta(minutes=dt_min)

        Rg_total = sum(Rg_mg_per_min(t_min, dt_min, m) for m in meals)
        I_signal = insulin_I_t(person, t_min, doses)

        state = step_euler(person, state, Rg_total, I_signal, dt_min)

        if exercise and active_window(t_min, exercise.start_min, exercise.duration_min):
            state.G_mgdl -= person.rex_mgdl_per_min * exercise.intensity * dt_min

        if stress and active_window(t_min, stress.start_min, stress.duration_min):
            state.G_mgdl *= stress.multiplier
        state.G_mgdl = max(20.0, min(400.0, state.G_mgdl))

        times.append(now)
        glucose.append(state.G_mgdl)

    return SimulationResult(times_dt=times, glucose_mgdl=glucose)