from dataclasses import dataclass
from entities.person import Person

@dataclass
class MinimalModelState:
    G_mgdl: float
    X_per_min: float

def step_euler(person: Person, state: MinimalModelState, Rg_mg_per_min: float, I_signal: float, dt_min: int) -> MinimalModelState:
    G = state.G_mgdl
    X = state.X_per_min

    Xdot = -person.p2_per_min * X + person.p3_per_min_per_signal * I_signal
    X_new = X + dt_min * Xdot

    V = person.V_dL()
    Gdot = (-(person.SG_per_min + X) * G) + (person.SG_per_min * person.Gb_mgdl) + (Rg_mg_per_min / V)
    G_new = G + dt_min * Gdot

    return MinimalModelState(G_mgdl=G_new, X_per_min=X_new)