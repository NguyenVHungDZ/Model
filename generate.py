import pandas as pd
import pickle

# Load the dataset
df = pd.read_csv('home_data_2023.csv')

# Group by day_type and season, and find the most frequent leaving and returning times
patterns = {}
for (day_type, season), group in df.groupby(['day_type', 'season']):
    leaving_mode = group['leaving_time'].mode()[0]
    returning_mode = group['returning_time'].mode()[0]
    if day_type not in patterns:
        patterns[day_type] = {}
    patterns[day_type][season] = {
        'leaving_time': leaving_mode,
        'returning_time': returning_mode
    }

# Print patterns for verification
print("Leaving and Returning Patterns by Day Type and Season:")
for day_type, seasons in patterns.items():
    for season, times in seasons.items():
        print(f"{day_type} ({season}): Leaving at {times['leaving_time']}, Returning at {times['returning_time']}")

# Save patterns to a .pkl file
with open('patterns_by_daytype_season.pkl', 'wb') as f:
    pickle.dump(patterns, f)
print("Patterns saved to patterns_by_daytype_season.pkl")