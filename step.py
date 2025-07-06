from dataclasses import dataclass
from ics import Calendar, Event


@dataclass
class Step:
    id: int
    name: str
    intended_length:int
    delay_length: int = 0

@dataclass
class Transition:
    from_: int
    to: int
    ml_increment_per_day: int = 5
    ml_start_number: int = 40
    ml_end_number: int = 85
