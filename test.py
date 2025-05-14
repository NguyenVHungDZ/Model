import pickle
from datetime import date

# Hardcoded holidays for 2025 (adjust as needed for the current year)
holidays = [
    date(2025, 1, 1),  # New Year's Day
    date(2025, 7, 4),  # Independence Day
    date(2025, 12, 25) # Christmas Day
]

# Function to determine season based on month
def get_season(month):
    if month in [12, 1, 2]:
        return 'winter'
    elif month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    else:
        return 'autumn'

# Load patterns from the .pkl file
with open('patterns_by_daytype_season.pkl', 'rb') as f:
    patterns = pickle.load(f)

# Get today's date
today = date.today()

# Determine day type
if today in holidays:
    day_type = 'holiday'
elif today.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
    day_type = 'weekend'
else:
    day_type = 'weekday'

# Determine season
season = get_season(today.month)

# Get predicted times
try:
    predicted_times = patterns[day_type][season]
    leaving_time = predicted_times['leaving_time']
    returning_time = predicted_times['returning_time']

    # Display the prediction
    print(f"Today is a {day_type} in {season}. Predicted leaving time: {leaving_time}, returning time: {returning_time}")
except KeyError:
    print(f"No pattern found for {day_type} in {season}. Please check the patterns.pkl file.")