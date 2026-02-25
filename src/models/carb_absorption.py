from entities.meal import Meal

def C_cumulative_carbs_g(t_min: int, meal: Meal) -> float:

    if t_min <= meal.time_min:
        return 0.0

    tau = t_min - meal.time_min
    if tau >= meal.duration_min:
        return meal.carbs_g


    t_peak = max(1, min(meal.t_peak_min, meal.duration_min - 1))
    T = meal.duration_min
    h = 2.0 * meal.carbs_g / T

    if tau <= t_peak:
        return (h / (2.0 * t_peak)) * (tau ** 2)

    area_to_peak = h * t_peak / 2.0
    denom = (T - t_peak)

    integral = (h / denom) * (T * (tau - t_peak) - ((tau ** 2 - t_peak ** 2) / 2.0))
    return min(meal.carbs_g, area_to_peak + integral)

def Rg_mg_per_min(t_min: int, dt_min: int, meal: Meal) -> float:
    c_now = C_cumulative_carbs_g(t_min, meal)
    c_prev = C_cumulative_carbs_g(t_min - dt_min, meal)
    dC = max(0.0, c_now - c_prev)  # grams in this step
    return (1000.0 * dC) / float(dt_min)  # mg/min