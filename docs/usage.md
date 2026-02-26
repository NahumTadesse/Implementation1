# Usage

## How to Run the Simulation
- Install Python
- Install the required dependency:
  pip install matplotlib
- From the project root directory, run:
  python main.py
- Follow the prompts to enter scenario details.

## Command-Line Arguments or Configuration
- No command-line arguments are required.
- All inputs (start time, glucose, meal, insulin, exercise, stress) are provided interactively when the program runs.

## Expected Output / Behavior
- Printed glucose values (mg/dL) at 15-minute intervals.
- A 3-hour glucose forecast plot.
- Reference lines at 70 mg/dL (low glucose) and 180 mg/dL (high glucose).
- Warning messages for unsafe glucose levels (starting glucose below 70 mg/dL).
