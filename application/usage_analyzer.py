import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class UsageAnalyzer:
    def __init__(self, csv_path):
        """
        Initialize with CSV data path.
        
        Args:
            csv_path (str): Path to the CSV file.
        """
        self.csv_path = csv_path
        self.data = pd.read_csv(csv_path, parse_dates=['Timestamp'])
        self.data['Hour'] = self.data['Timestamp'].dt.hour
        self.data['Day'] = self.data['Timestamp'].dt.day
        self.data['Month'] = self.data['Timestamp'].dt.month
        logging.debug(f"UsageAnalyzer initialized with CSV: {csv_path}")

    def daily_profile(self, user_type=None, household_size=None, season=None):
        """Calculate average hourly consumption for daily pattern with filters."""
        filtered = self._filter_data(user_type, household_size, season)
        return filtered.groupby('Hour')['Power Consumption (W)'].mean()

    def appliance_contribution(self, user_type=None, household_size=None, season=None):
        """Compute total consumption per appliance type with filters."""
        filtered = self._filter_data(user_type, household_size, season)
        return filtered.groupby('Device Type')['Power Consumption (W)'].sum()

    def peak_times(self, threshold=5000, user_type=None, household_size=None, season=None):
        """Identify hours with consumption above threshold with filters."""
        filtered = self._filter_data(user_type, household_size, season)
        hourly_consumption = filtered.groupby('Hour')['Power Consumption (W)'].sum()
        return hourly_consumption[hourly_consumption > threshold].index.tolist()

    def seasonal_analysis(self, user_type=None, household_size=None):
        """Analyze average monthly consumption for seasonal trends with filters."""
        filtered = self._filter_data(user_type, household_size)
        return filtered.groupby('Month')['Power Consumption (W)'].mean()

    def optimization_suggestions(self, user_type, household_size, season):
        """Generate personalized optimization recommendations."""
        suggestions = {}
        if user_type == "reckless":
            suggestions['General'] = "Consider reducing usage duration for non-essential devices."
        elif user_type == "conscious":
            suggestions['General'] = "Maintain your efficient habits; consider smart plugs for further savings."
        if household_size == "family":
            suggestions['Family'] = "Stagger appliance use to avoid simultaneous high consumption."
        elif household_size == "single":
            suggestions['Single'] = "Focus on energy-efficient appliances for your smaller household."
        if season == "summer" and "Air Conditioner" in self.appliance_contribution(user_type, household_size, season):
            suggestions['Summer'] = "Set air conditioner to a higher temperature (e.g., 24°C) or use fans."
        elif season == "winter" and "Heater" in self.appliance_contribution(user_type, household_size, season):
            suggestions['Winter'] = "Lower heater settings and use insulation to retain heat."
        return suggestions

    def _filter_data(self, user_type=None, household_size=None, season=None):
        """Helper to filter data based on parameters."""
        filtered = self.data
        if user_type and 'user_type' in filtered.columns:
            filtered = filtered[filtered['user_type'] == user_type]
        if household_size and 'household_size' in filtered.columns:
            filtered = filtered[filtered['household_size'] == household_size]
        if season:
            season_months = {'winter': [12, 1, 2], 'spring': [3, 4, 5], 'summer': [6, 7, 8], 'fall': [9, 10, 11]}
            filtered = filtered[filtered['Month'].isin(season_months.get(season, []))]
        return filtered

    def export_for_grafana(self, output_path, user_type=None, household_size=None, season=None):
        """Export filtered data as CSV for visualization tools."""
        filtered = self._filter_data(user_type, household_size, season)
        filtered.to_csv(output_path, index=False)
        logging.debug(f"Data exported to {output_path}")