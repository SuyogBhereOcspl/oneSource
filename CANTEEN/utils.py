from datetime import time
from .models import *
from .models import Shift

# Create your views here.

def determine_shift(punch_datetime):
    allowed_shifts = [
        {"name": "Lunch F", "start": time(11, 30), "end": time(13, 00)},
        {"name": "Lunch G", "start": time(13, 0), "end": time(14, 30)},
        {"name": "Dinner", "start": time(19, 30), "end": time(20, 30)},
        {"name": "Evening Dinner", "start": time(20, 30), "end": time(21, 30)},
        {"name": "Morning Tea Break", "start": time(8, 30), "end": time(9, 15)},
        {"name": "Evening Tea Break", "start": time(16, 00), "end": time(16, 30)},
        {"name": "Night Tea Break", "start": time(3, 0), "end": time(3, 30)},
    ]
    
    punch_time = punch_datetime.time()

    for period in allowed_shifts:
        if period["start"] <= punch_time <= period["end"]:
            shift, _ = Shift.objects.get_or_create(name=period["name"])
            if shift.start_time != period["start"] or shift.end_time != period["end"]:
                shift.start_time = period["start"]
                shift.end_time = period["end"]
                shift.save()
            return shift

    return None
