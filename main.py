# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "ics",
# ]
# ///
import datetime
import os # Added for file operations like removing delay_info.txt
from ics import Calendar, Event

DELAY_INFO_FILENAME = "delay_info.txt"

def load_delay_info(filename, max_step_num):
    """
    Loads delay information from the specified file.
    Validates against max_step_num.
    Returns a dictionary {'delay_after_step': int, 'delay_duration_days': int} or None.
    """
    try:
        data = {}
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):  # Skip empty lines or comments
                    continue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    if key in ["delay_after_step", "delay_duration_days"]:
                        try:
                            data[key] = int(value)
                        except ValueError:
                            print(f"Warning: Non-integer value for '{key}' in '{filename}'. File is considered invalid.")
                            return None
                else:
                    print(f"Warning: Malformed line in '{filename}': {line}. File is considered invalid.")
                    return None
        
        if "delay_after_step" not in data or "delay_duration_days" not in data:
            print(f"Warning: Missing 'delay_after_step' or 'delay_duration_days' in '{filename}'. File is considered invalid.")
            return None

        delay_step = data["delay_after_step"]
        delay_duration = data["delay_duration_days"]

        if not (1 <= delay_step <= max_step_num):
            print(f"Warning: Invalid 'delay_after_step' ({delay_step}) in '{filename}'. Must be between 1 and {max_step_num}. File is considered invalid.")
            return None
        if not (delay_duration > 0):
            print(f"Warning: Invalid 'delay_duration_days' ({delay_duration}) in '{filename}'. Must be positive. File is considered invalid.")
            return None
            
        return {"delay_after_step": delay_step, "delay_duration_days": delay_duration}

    except FileNotFoundError:
        return None # File not found is normal, not an error state for loading.
    except Exception as e:
        print(f"Error reading or parsing '{filename}': {e}. File is considered invalid.")
        return None

def save_delay_info(filename, delay_after_step, delay_duration_days):
    """Saves delay information to the specified file. Returns True on success."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"delay_after_step: {delay_after_step}\n")
            f.write(f"delay_duration_days: {delay_duration_days}\n")
        return True
    except IOError as e:
        print(f"Error saving delay information to '{filename}': {e}")
        return False

def create_medication_schedule():
    """
    Generates an iCalendar (.ics) file for a medication schedule.
    Prompts for start date. Reads/writes optional delay from/to delay_info.txt.
    """

    # --- Configuration ---
    medication_steps_details = [
        "1 small scoop",
        "2 small scoops",
        "1 big scoop",
        "2 big scoops",
        "1/64th tsp",
        "1/32th tsp",
        "1/16th tsp"
    ]
    days_per_main_step = 14
    days_per_transition = 18
    applesauce_volume = "3 oz"
    ml_increment_per_day = 5
    # --- End Configuration ---

    num_steps_available = len(medication_steps_details)

    # 1. Get start date from user
    while True:
        start_date_str = input("Enter the start date for the first step (YYYY-MM-DD): ")
        try:
            current_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            initial_start_date = current_date
            break
        except ValueError as e:
            print(f"Invalid date format. Please use YYYY-MM-DD (e.g., 2025-07-15). Error: {e}")

    # 2. Handle Delay Information
    delay_after_step_active = None
    delay_duration_active = 0
    source_of_delay_info = "No delay applied"

    loaded_delay = load_delay_info(DELAY_INFO_FILENAME, num_steps_available)

    if loaded_delay:
        print("-" * 30)
        print(f"Found delay configuration in '{DELAY_INFO_FILENAME}':")
        print(f"  Delay after Step: {loaded_delay['delay_after_step']}")
        print(f"  Delay duration: {loaded_delay['delay_duration_days']} days")
        
        while True:
            choice = input("Action: [U]se this delay, [I]gnore for this run, [O]verwrite with new, [R]emove file & no delay? (u/i/o/r): ").strip().lower()
            if choice == 'u':
                delay_after_step_active = loaded_delay['delay_after_step']
                delay_duration_active = loaded_delay['delay_duration_days']
                source_of_delay_info = f"Loaded from {DELAY_INFO_FILENAME}"
                break
            elif choice == 'i':
                print("Ignoring stored delay for this run.")
                source_of_delay_info = "Stored delay ignored for this run"
                break
            elif choice == 'o':
                print("You'll be prompted to enter new delay information.")
                # delay_after_step_active remains None, will trigger prompts below
                break 
            elif choice == 'r':
                try:
                    os.remove(DELAY_INFO_FILENAME)
                    print(f"Removed '{DELAY_INFO_FILENAME}'. No delay will be applied from file.")
                except OSError as e:
                    print(f"Error removing '{DELAY_INFO_FILENAME}': {e}")
                source_of_delay_info = f"{DELAY_INFO_FILENAME} removed, no delay from file"
                break
            else:
                print("Invalid choice. Please enter 'u', 'i', 'o', or 'r'.")
        print("-" * 30)
    else:
        print(f"No valid delay configuration file ('{DELAY_INFO_FILENAME}') found.")

    # If no delay is active from file (either not loaded, or user chose to ignore/overwrite/remove)
    # then ask if they want to specify one for *this run*.
    # This also covers the 'o' (overwrite) case from above.
    if delay_after_step_active is None: 
        add_new_delay_choice = input("Do you want to specify a delay for this schedule generation? (yes/no): ").strip().lower()
        if add_new_delay_choice == 'yes':
            while True:
                try:
                    delay_step_str = input(f"After which step number was the schedule delayed? (1-{num_steps_available}): ")
                    temp_delay_step = int(delay_step_str)
                    if 1 <= temp_delay_step <= num_steps_available:
                        break
                    else:
                        print(f"Invalid step number. Please enter a number between 1 and {num_steps_available}.")
                except ValueError:
                    print("Invalid input. Please enter a whole number for the step.")
            
            while True:
                try:
                    delay_duration_str = input("For how many days was this step extended (delay duration)? ")
                    temp_delay_duration = int(delay_duration_str)
                    if temp_delay_duration > 0:
                        break
                    else:
                        print("Delay duration must be a positive number of days.")
                except ValueError:
                    print("Invalid input. Please enter a whole number for the duration.")

            delay_after_step_active = temp_delay_step
            delay_duration_active = temp_delay_duration
            source_of_delay_info = "User input for this run"

            save_choice = input(f"Save this new delay configuration to '{DELAY_INFO_FILENAME}'? (yes/no): ").strip().lower()
            if save_choice == 'yes':
                if save_delay_info(DELAY_INFO_FILENAME, delay_after_step_active, delay_duration_active):
                    print(f"Delay configuration saved to '{DELAY_INFO_FILENAME}'.")
                    source_of_delay_info += f" (and saved to {DELAY_INFO_FILENAME})"
                else:
                    print(f"Failed to save delay configuration.")
            print("-" * 30)
        elif source_of_delay_info == "Stored delay ignored for this run" or source_of_delay_info.startswith(f"{DELAY_INFO_FILENAME} removed"):
            pass # Keep the previous status message
        else:
            source_of_delay_info = "No delay specified for this run"


    cal = Calendar() # Output is still ICS

    for i, step_description in enumerate(medication_steps_details):
        current_step_number = i + 1

        # --- Main Dosage Period ---
        print(f"\nProcessing Step {current_step_number}: '{step_description}' for {days_per_main_step} days")
        for day_num in range(1, days_per_main_step + 1):
            event = Event()
            event.name = f"Dose: {step_description}"
            event.description = f"Take {step_description} of cashew. (Day {day_num}/{days_per_main_step} of Step {current_step_number})"
            event.begin = current_date
            event.make_all_day()
            cal.events.add(event)
            current_date += datetime.timedelta(days=1)

        # --- Apply Delay, if configured for *after* this current step ---
        if delay_after_step_active is not None and current_step_number == delay_after_step_active and delay_duration_active > 0:
            print(f"\n--- Applying Delay after Step {current_step_number} ---")
            print(f"Extending '{step_description}' for an additional {delay_duration_active} days.")
            for delay_day_num in range(1, delay_duration_active + 1):
                event = Event()
                event.name = f"Dose (Extended): {step_description}"
                event.description = (
                    f"Extended period for Step {current_step_number} ('{step_description}'). (Delay Day {delay_day_num}/{delay_duration_active})\n"
                    f"Continue taking {step_description} of cashew."
                )
                event.begin = current_date
                event.make_all_day()
                cal.events.add(event)
                print(f"  Added extended event for '{step_description}' on {current_date.strftime('%Y-%m-%d')}")
                current_date += datetime.timedelta(days=1)
            print(f"--- Delay Applied. Schedule continues from {current_date.strftime('%Y-%m-%d')} ---")
            # Make sure delay is only applied once by effectively "consuming" it
            delay_after_step_active = None 

        # --- Transition Period ---
        if current_step_number < num_steps_available:
            next_step_description = medication_steps_details[current_step_number]
            print(f"\nProcessing Transition from Step {current_step_number} to Step {current_step_number + 1} ('{next_step_description}') for {days_per_transition} days")
            for day_num in range(1, days_per_transition + 1):
                ml_amount = day_num * ml_increment_per_day
                event = Event()
                event.name = f"Dose: {ml_amount}ml from {next_step_description} mixture"
                event.description = (
                    f"Transition Day {day_num}/{days_per_transition} (from Step {current_step_number} to {current_step_number + 1})\n"
                    f"Prepare for {next_step_description}: Mix one dose of '{next_step_description}' "
                    f"into {applesauce_volume} of applesauce. "
                    f"Take {ml_amount}ml of this mixture today."
                )
                event.begin = current_date
                event.make_all_day()
                cal.events.add(event)
                current_date += datetime.timedelta(days=1)
        elif current_step_number == num_steps_available:
            print(f"\nStep {current_step_number} ('{step_description}') is the final main step. No transition follows.")

    # --- Write to ICS file ---
    ics_file_name = "medication_schedule.ics"
    try:
        with open(ics_file_name, 'w', encoding='utf-8') as f:
            f.writelines(cal.serialize_iter())
        print("-" * 30)
        last_event_date = current_date - datetime.timedelta(days=1)
        print(f"Successfully created '{ics_file_name}'")
        print(f"The schedule starts on {initial_start_date.strftime('%Y-%m-%d')}.")
        
        # Report on delay status
        if delay_duration_active > 0 and (source_of_delay_info.startswith("Loaded") or source_of_delay_info.startswith("User input")):
            # The delay_after_step_active might be None here if it was consumed.
            # We need to reconstruct the step number for the message.
            # The source_of_delay_info string can help, or we can store the original step number.
            # For now, let's assume delay_duration_active > 0 means a delay was applied.
            # The source_of_delay_info string will give context.
            # To get the step number, we'd need to parse it from source_of_delay_info or store it separately.
            # Let's refine this message slightly.
            # If loaded_delay was used, its values are still intact.
            # If user input was used, temp_delay_step and temp_delay_duration hold those values.
            # This part of the logic needs to be careful about which variables to use for the message.
            
            applied_delay_step_message = ""
            if "Loaded from" in source_of_delay_info and loaded_delay:
                applied_delay_step_message = f"after Step {loaded_delay['delay_after_step']} "
            elif "User input" in source_of_delay_info:
                # This requires temp_delay_step to be available, which it is if user input path was taken.
                # However, if user chose 'u' (use loaded), temp_delay_step wouldn't be set.
                # The current logic sets delay_after_step_active and delay_duration_active correctly.
                # The issue is that delay_after_step_active is set to None after application.
                # We need to store the *original* step number that the delay was applied after.
                # Let's add a variable `applied_delay_step_number_for_message`
                # This is getting a bit complex. The simplest is to rely on source_of_delay_info.
                # The `delay_duration_active` is the key indicator that a delay was applied.
                # The `source_of_delay_info` tells us where it came from.
                # The actual step number it was applied after is `delay_after_step_active` *before* it's set to None.
                # This means the message should ideally be constructed *before* it's set to None, or we store it.

                # Simpler approach for the message:
                # The `delay_duration_active` is the duration that was applied.
                # The `source_of_delay_info` already contains context like "Loaded from..." or "User input...".
                # If it was loaded, `loaded_delay['delay_after_step']` has the step.
                # If it was user input, we need to ensure we captured that.
                # The `delay_after_step_active` is the one used in the loop condition.
                # Let's just use `source_of_delay_info` as it is.
                print(f"Delay status: A delay of {delay_duration_active} days was applied. ({source_of_delay_info})")

        else: # No active delay was applied
            print(f"Delay status: {source_of_delay_info}.")


        print(f"The last scheduled medication day is {last_event_date.strftime('%Y-%m-%d')}.")
        print("You can now import this file into your calendar application.")
    except Exception as e:
        print(f"Error writing ICS file: {e}")

if __name__ == "__main__":
    print("Medication Schedule iCalendar (.ics) Generator")
    print("-" * 30)
    print(f"This script creates an iCalendar file for your medication schedule.")
    print(f"It can use a pre-configured delay from '{DELAY_INFO_FILENAME}', or prompt you for delay details.")
    print("Ensure you have Python installed, and the 'ics' library (pip install ics).")
    print("-" * 30)
    create_medication_schedule()
