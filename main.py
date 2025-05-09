# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "ics",
# ]
# ///
import datetime
from ics import Calendar, Event # You'll need to install this: pip install ics

def create_medication_schedule():
    """
    Generates an iCalendar (.ics) file for a medication schedule.
    Prompts the user for a start date. Uses only standard datetime.
    """

    # --- Configuration ---
    medication_steps_details = [
        "1 small scoop",
        "2 small scoops",
        "1 big scoop",
        "2 big scoops",
        "1/64th tsp",
        "1/32th tsp"
        "1/16th tsp"
    ]
    days_per_main_step = 14
    days_per_transition = 18
    applesauce_volume = "3 oz"
    ml_increment_per_day = 5
    # --- End Configuration ---

    # 1. Get start date from user
    while True:
        start_date_str = input("Enter the start date for the first step (YYYY-MM-DD): ")
        try:
            # Use datetime.datetime.strptime to parse the date string
            current_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            initial_start_date = current_date # Store for the final message
            break
        except ValueError as e: # strptime raises ValueError for incorrect format
            print(f"Invalid date format. Please use YYYY-MM-DD (e.g., 2025-07-15). Error: {e}")

    cal = Calendar()
    num_steps = len(medication_steps_details)

    for i, step_description in enumerate(medication_steps_details):
        # --- Main Dosage Period (e.g., 14 days) ---
        print(f"\nProcessing Step {i+1}: {step_description} for {days_per_main_step} days")
        for day_num in range(1, days_per_main_step + 1):
            event = Event()
            event.name = f"Dose: {step_description}"
            event.description = f"Take {step_description} of cashew. (Day {day_num}/{days_per_main_step})"
            # ics library handles datetime.date objects for all-day events
            event.begin = current_date
            event.make_all_day()
            cal.events.add(event)
            current_date += datetime.timedelta(days=1)

        # --- Transition Period (e.g., 18 days) ---
        # Only add transition if it's NOT the last step
        if i < num_steps - 1:
            next_step_description = medication_steps_details[i+1]
            print(f"Processing Transition to Step {i+2} ({next_step_description}) for {days_per_transition} days")
            for day_num in range(1, days_per_transition + 1):
                ml_amount = day_num * ml_increment_per_day
                event = Event()
                event.name = f"Dose: {ml_amount}ml from {next_step_description} mixture"
                event.description = (
                    f"Day {day_num}/{days_per_transition} \n"
                    f"Prepare for {next_step_description}: Mix one dose of '{next_step_description}' "
                    f"into {applesauce_volume} of applesauce. "
                    f"Take {ml_amount}ml of this mixture today."
                )
                event.begin = current_date
                event.make_all_day()
                cal.events.add(event)
                current_date += datetime.timedelta(days=1)

    # --- Write to ICS file ---
    ics_file_name = "medication_schedule.ics"
    try:
        with open(ics_file_name, 'w', encoding='utf-8') as f:
            f.writelines(cal.serialize_iter()) # Using serialize_iter for potentially large calendars
        print("-" * 30)
        # The current_date is now the day AFTER the last event. So, the last event was on current_date - 1 day.
        last_event_date = current_date - datetime.timedelta(days=1)
        print(f"Successfully created '{ics_file_name}'")
        print(f"The schedule starts on {initial_start_date.strftime('%Y-%m-%d')}.")
        print(f"The last scheduled medication day is {last_event_date.strftime('%Y-%m-%d')}.")
        print("You can now import this file into your calendar application (Google Calendar, Outlook, Apple Calendar, etc.).")
    except Exception as e:
        print(f"Error writing ICS file: {e}")

if __name__ == "__main__":
    print("Medication Schedule Calendar Generator")
    print("-" * 30)
    print("This script will create an iCalendar (.ics) file based on the specified medication rules.")
    print("Ensure you have Python installed, and the 'ics' library.")
    print("If 'ics' is not installed, run: pip install ics")
    print("-" * 30)
    create_medication_schedule()
