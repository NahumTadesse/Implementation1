from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from entities import Person, Meal, InsulinDose, Exercise, Stress
from models.minimal_model import MinimalModelState
from models.insulin_model import compute_bolus_units_from_carbs
from simulation.simulator import run_forecast

DT_MIN = 15
HORIZON_MIN = 180  # 3 hours
MEAL_T_PEAK_MIN = 75
MEAL_DURATION_MIN = 240


def ask_int_range(prompt: str, default: int, lo: int, hi: int) -> int:
    """Enter -> uses default, but default is not shown in the prompt."""
    while True:
        s = input(f"{prompt}: ").strip()
        if s == "":
            v = default
        else:
            try:
                v = int(s)
            except ValueError:
                print("Enter a whole number.")
                continue
        if lo <= v <= hi:
            return v
        print(f"Value must be between {lo} and {hi}.")


def ask_float_range(prompt: str, default: float, lo: float, hi: float) -> float:
    """Enter -> uses default, but default is not shown in the prompt."""
    while True:
        s = input(f"{prompt}: ").strip()
        if s == "":
            v = default
        else:
            try:
                v = float(s)
            except ValueError:
                print("Enter a number.")
                continue
        if lo <= v <= hi:
            return v
        print(f"Value must be between {lo} and {hi}.")


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """Enter -> uses default, but default is not shown in the prompt."""
    s = input(f"{prompt} (y/n): ").strip().lower()
    if s == "":
        return default_yes
    return s == "y"


def ask_ampm(default: str) -> str:
    """Enter -> uses default, but default is not shown in the prompt."""
    s = input("  AM or PM: ").strip().upper()
    if s == "":
        s = default
    while s not in ("AM", "PM"):
        s = input("  Please enter AM or PM: ").strip().upper()
    return s


def ask_time_of_day(label: str, default_h: int, default_m: int, default_ampm: str):
    """
    hour (1-12), minute (0-59), AM/PM -> (hour24, minute)
    Defaults are applied on Enter but not displayed.
    """
    print(f"\n{label} time:")
    h = ask_int_range("  Hour (1-12)", default_h, 1, 12)
    m = ask_int_range("  Minute (0-59)", default_m, 0, 59)
    ampm = ask_ampm(default_ampm)

    if ampm == "AM":
        hour24 = 0 if h == 12 else h
    else:
        hour24 = 12 if h == 12 else h + 12
    return hour24, m


def minutes_since_start(start_dt: datetime, event_hour24: int, event_min: int) -> int:
    event_dt = start_dt.replace(hour=event_hour24, minute=event_min, second=0, microsecond=0)
    if event_dt < start_dt:
        event_dt += timedelta(days=1)
    return int((event_dt - start_dt).total_seconds() // 60)


def fmt_time(dt: datetime) -> str:
    return dt.strftime("%I:%M %p").lstrip("0")


def time_range_str(start_dt: datetime, start_offset_min: int, duration_min: int) -> str:
    a = start_dt + timedelta(minutes=start_offset_min)
    b = a + timedelta(minutes=duration_min)
    return f"{fmt_time(a)}–{fmt_time(b)}"


def in_window(offset_min: int) -> bool:
    return 0 <= offset_min < HORIZON_MIN


def plot_cgm(times_dt, glucose):
    plt.figure()
    plt.plot(times_dt, glucose)

    ax = plt.gca()
    ax.set_title("CGM Glucose Forecast (Next 3 Hours)")
    ax.set_xlabel("Time")
    ax.set_ylabel("Glucose (mg/dL)")

    ax.axhline(70, linestyle="--", linewidth=1)
    ax.axhline(180, linestyle="--", linewidth=1)

    ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%I:%M %p"))

    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    plt.show()


def main():
    sh24, sm = ask_time_of_day("Simulation START", 8, 24, "PM")
    today = datetime.now().date()
    start_dt = datetime(today.year, today.month, today.day, sh24, sm)

    start_glucose = ask_float_range("\nStart glucose (mg/dL)", 120.0, 20.0, 400.0)
    carb_ratio = ask_float_range("Carb-to-insulin ratio (grams per 1 unit)", 12.0, 1.0, 50.0)

    person = Person(weight_kg=80.0, carb_ratio_g_per_unit=carb_ratio)

    if start_glucose < 70:
        print("Warning: Starting glucose is below 70 mg/dL (hypoglycemia range).")
        if not ask_yes_no("Continue anyway?", True):
            print("Exiting.")
            return

    meals = []
    meal_summary = "Meal: (none)"
    if ask_yes_no("\nAdd a meal?", True):
        mh24, mm = ask_time_of_day("Meal", 8, 24, "PM")
        carbs = ask_float_range("Meal carbs (g)", 60.0, 0.0, 300.0)

        meal_offset = minutes_since_start(start_dt, mh24, mm)
        if not in_window(meal_offset):
            meal_dt = start_dt + timedelta(minutes=meal_offset)
            print(f"Meal at {fmt_time(meal_dt)} is outside the 3-hour window; ignoring it.")
        else:
            meals.append(
                Meal(
                    time_min=meal_offset,
                    carbs_g=carbs,
                    t_peak_min=MEAL_T_PEAK_MIN,
                    duration_min=MEAL_DURATION_MIN
                )
            )
            meal_dt = start_dt + timedelta(minutes=meal_offset)
            meal_summary = f"Meal: {carbs:.0f} g at {fmt_time(meal_dt)}"

    doses = []
    insulin_summary = "Insulin: (none)"
    if ask_yes_no("\nAdd insulin?", True):
        auto = ask_yes_no("Auto-calc insulin from meal carbs?", True)
        if auto and len(meals) > 0:
            units = compute_bolus_units_from_carbs(person, meals[0].carbs_g)
            doses.append(InsulinDose(time_min=meals[0].time_min, units=units))
            insulin_dt = start_dt + timedelta(minutes=meals[0].time_min)
            insulin_summary = f"Insulin: {units:.1f} units at {fmt_time(insulin_dt)} (auto)"
        else:
            ih24, im = ask_time_of_day("Insulin dose", 8, 24, "PM")
            units = ask_float_range("Insulin units", 5.0, 0.0, 50.0)
            dose_offset = minutes_since_start(start_dt, ih24, im)

            if not in_window(dose_offset):
                dose_dt = start_dt + timedelta(minutes=dose_offset)
                print(f"Insulin at {fmt_time(dose_dt)} is outside the 3-hour window; ignoring it.")
            else:
                doses.append(InsulinDose(time_min=dose_offset, units=units))
                dose_dt = start_dt + timedelta(minutes=dose_offset)
                insulin_summary = f"Insulin: {units:.1f} units at {fmt_time(dose_dt)}"

    exercise = None
    exercise_summary = "Exercise: (none)"
    if ask_yes_no("\nAdd exercise?", False):
        eh24, em = ask_time_of_day("Exercise START", 9, 24, "PM")
        ex_dur = ask_int_range("Exercise duration (min)", 30, 5, 240)
        ex_int = ask_float_range("Exercise intensity (0.0–1.0)", 0.7, 0.0, 1.0)

        ex_offset = minutes_since_start(start_dt, eh24, em)
        if not in_window(ex_offset):
            ex_dt = start_dt + timedelta(minutes=ex_offset)
            print(f"Exercise at {fmt_time(ex_dt)} is outside the 3-hour window; ignoring it.")
        else:
            exercise = Exercise(start_min=ex_offset, duration_min=ex_dur, intensity=ex_int)
            exercise_summary = f"Exercise: {time_range_str(start_dt, ex_offset, ex_dur)}, intensity {ex_int:.1f}"

    stress = None
    stress_summary = "Stress: (none)"
    if ask_yes_no("\nAdd stress?", False):
        sth24, stm = ask_time_of_day("Stress START", 10, 24, "PM")
        st_dur = ask_int_range("Stress duration (min)", 30, 5, 240)
        st_mult = ask_float_range("Stress multiplier (e.g., 1.2)", 1.2, 1.0, 2.0)

        st_offset = minutes_since_start(start_dt, sth24, stm)
        if not in_window(st_offset):
            st_dt = start_dt + timedelta(minutes=st_offset)
            print(f"Stress at {fmt_time(st_dt)} is outside the 3-hour window; ignoring it.")
        else:
            stress = Stress(start_min=st_offset, duration_min=st_dur, multiplier=st_mult)
            stress_summary = f"Stress: {time_range_str(start_dt, st_offset, st_dur)}, multiplier {st_mult:.1f}"

    if start_glucose < 70 and len(meals) == 0 and (len(doses) > 0 or exercise is not None):
        print("WARNING: Low start glucose + insulin/exercise without carbs may cause dangerous hypoglycemia.")

    print("\nScenario:")
    print(f"  Start glucose: {start_glucose:.0f} mg/dL")
    print(f"  {meal_summary}")
    print(f"  {insulin_summary}")
    print(f"  {exercise_summary}")
    print(f"  {stress_summary}")

    state0 = MinimalModelState(G_mgdl=start_glucose, X_per_min=0.0)
    result = run_forecast(
        person=person,
        start_datetime=start_dt,
        start_state=state0,
        horizon_min=HORIZON_MIN,
        dt_min=DT_MIN,
        meals=meals,
        doses=doses,
        exercise=exercise,
        stress=stress
    )

    print("\n=== Forecast Results ===")
    for t_dt, g in zip(result.times_dt, result.glucose_mgdl):
        print(f"{fmt_time(t_dt)}  G={g:7.2f} mg/dL")

    plot_cgm(result.times_dt, result.glucose_mgdl)


if __name__ == "__main__":
    main()