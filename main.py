# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "ics",
# ]
# ///
import datetime
import os # Added for file operations like removing delay_info.txt
from ics import Calendar, Event
from step import Step, Transition
from dataclasses import dataclass

def find_steps_for_transition(steps, transition): 
    from_ = None
    to = None
    for s in steps:
        if type(s) == Step and s.id == transition.from_:
            from_ = s
        elif type(s) == Step and s.id == transition.to:
            to = s
    return (from_, to)

@dataclass
class ToCalendar:
    end: datetime.datetime
    events: list

def step_to_events(step: Step, start: datetime.datetime):
    events = []
    for day_num in range(step.intended_length):
        event = Event()
        event.name = f"Dose: {step.name}"
        event.description = f"Take {step.name} of cashew. (Day {day_num}/{step.intended_length} of Step {step.id})"
        event.begin = start + datetime.timedelta(days=day_num)
        print(f"    {event.begin}: {event.name}")
        event.make_all_day()
        events.append(event)
    for delay_day_num in range(step.delay_length):
        event = Event()
        event.name = f"Dose (Extended): {step.name}"
        event.description = (
            f"Extended period for Step {step.id} ('{step.name}'). (Delay Day {delay_day_num}/{step.delay_length})\n"
            f"Continue taking {step.name} of cashew."
        )
        event.begin = start + datetime.timedelta(days = step.intended_length + delay_day_num)
        print(f"    {event.begin}: {event.name}")
        event.make_all_day()
        events.append(event)
    return ToCalendar(events=events, end=start + datetime.timedelta(days=step.intended_length + step.delay_length -1))

def transition_to_events(transition, start: datetime.datetime, from_, to ):
    events = []
    current_ml = transition.ml_start_number
    current_day = 0
    total_days = (transition.ml_end_number - transition.ml_start_number) / transition.ml_increment_per_day
    while current_ml <= transition.ml_end_number:
        event = Event()
        event.name = f"Dose: {current_ml}ml from {to.name}"
        event.description = (
            f"Transition Day {current_day +1}/{total_days} (from Step {from_.name} to {to.name})\n"
            f"Prepare for {to.name}: Mix one dose of '{to.name}' "
            f"into 3oz (90ml) of applesauce. "
            f"Take {current_ml}ml of this mixture today."
        )
        event.begin = start + datetime.timedelta(days=current_day)
        print(f"    {event.begin}: {event.name}")
        event.make_all_day()
        events.append(event)
        current_ml += transition.ml_increment_per_day
        current_day += 1

    return ToCalendar(events=events, end=start + datetime.timedelta(days=current_day-1))

def create_medication_schedule():
    """
    Generates an iCalendar (.ics) file for a medication schedule.
    Prompts for start date. Reads/writes optional delay from/to delay_info.txt.
    """
    # --- Configuration ---
    medication_steps = [
        Step(id=1,name="1 small scoop", intended_length=14, delay_length=7),
        Transition(from_=1, to=2, ml_start_number=5, ml_end_number=90),
        Step(id=2,name="2 small scoops", intended_length=20),
        Transition(from_=2, to=3, ml_start_number=45),
        Step(id=3,name="1 big scoop", intended_length=21),
        Transition(from_=3, to=4),
        Step(id=4,name="2 big scoops", intended_length=21),
        Transition(from_=4, to=5),
        Step(id=5,name="1/64th tsp", intended_length=21),
        Transition(from_=5, to=6),
        Step(id=6,name="1/32th tsp", intended_length=21),
        Transition(from_=6, to=7),
        Step(id=7,name="1/16th tsp", intended_length=21),
    ]
    # --- End Configuration ---


    # 1. Get start date from user
    start_date_str = "2025-05-08"
    current_time = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

    cal = Calendar() # Output is still ICS

    for step in medication_steps:
        print(f"Starting: {step}")
        print(f"    {current_time}")
        if type(step) == Step:
            to_cal = step_to_events(step, current_time)
            for event in to_cal.events:
                cal.events.add(event)
        if type(step) == Transition:
            from_, to  = find_steps_for_transition(medication_steps, step)
            to_cal = transition_to_events(step, current_time, from_, to)
            for event in to_cal.events:
                cal.events.add(event)
        print(f"Ending {to_cal.end}")
        print("----------")
        current_time =  to_cal.end + datetime.timedelta(days=1)

    # --- Write to ICS file ---
    ics_file_name = "medication_schedule.ics"
    try:
        with open(ics_file_name, 'w', encoding='utf-8') as f:
            f.writelines(cal.serialize_iter())
        print("-" * 30)
        last_event_date = current_time - datetime.timedelta(days=1)
        print(f"Successfully created '{ics_file_name}'")
        print(f"The schedule starts on {start_date_str}.")
        
        print(f"The last scheduled medication day is {last_event_date.strftime('%Y-%m-%d')}.")
        print("You can now import this file into your calendar application.")
    except Exception as e:
        print(f"Error writing ICS file: {e}")

if __name__ == "__main__":
    print("Medication Schedule iCalendar (.ics) Generator")
    print("-" * 30)
    print(f"This script creates an iCalendar file for your medication schedule.")
    print("Ensure you have Python installed, and the 'ics' library (pip install ics).")
    print("-" * 30)
    create_medication_schedule()