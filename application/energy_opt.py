import numpy as np
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class EnergyOptimizer:
    def __init__(self, data_manager, bill_calculator):
        """
        Initialize the EnergyOptimizer with DataManager and BillCalculator instances.

        Args:
            data_manager (DataManager): Instance to access appliance data.
            bill_calculator (BillCalculator): Instance to calculate costs.
        """
        self.data_manager = data_manager
        self.bill_calculator = bill_calculator
        self.appliances = self.data_manager.get_appliances()
        logging.debug("EnergyOptimizer initialized")

    def analyze_usage(self, csv_data_path=None):
        """
        Analyze usage and consumption rates from appliance data or CSV.

        Args:
            csv_data_path (str, optional): Path to CSV file with detailed usage data.

        Returns:
            dict: Analysis results including total consumption, peak times, and averages.
        """
        analysis_results = {
            "total_consumption_kwh": {},
            "peak_usage_times": {},
            "avg_daily_consumption_kwh": {},
            "high_consumption_appliances": []
        }

        if csv_data_path:
            # Load CSV data
            df = pd.read_csv(csv_data_path, parse_dates=["Timestamp"])
            grouped = df.groupby("Device Type")

            for device_type, group in grouped:
                # Calculate total consumption (Power in watts * Duration in minutes / 60 / 1000 = kWh)
                total_kwh = (group["Power Consumption (W)"] * group["Usage Duration (minutes)"] / 60 / 1000).sum()
                analysis_results["total_consumption_kwh"][device_type] = total_kwh

                # Identify peak usage times
                group["Hour"] = group["Timestamp"].dt.hour
                peak_hour = group.groupby("Hour").size().idxmax()
                analysis_results["peak_usage_times"][device_type] = peak_hour

                # Average daily consumption
                days = (group["Timestamp"].max() - group["Timestamp"].min()).days + 1
                avg_daily_kwh = total_kwh / days if days > 0 else total_kwh
                analysis_results["avg_daily_consumption_kwh"][device_type] = avg_daily_kwh

                # Flag high consumption appliances
                if total_kwh > 100:  # Arbitrary threshold, adjust as needed
                    analysis_results["high_consumption_appliances"].append(device_type)

        else:
            # Use appliance data from DataManager
            for appliance in self.appliances:
                device_type = appliance["Device Type"]
                power_w = float(appliance.get("Power Consumption (W)", 0))
                duration_min = float(appliance["Usage Duration (minutes)"])
                kwh = (power_w * duration_min / 60 / 1000)
                analysis_results["total_consumption_kwh"][device_type] = kwh
                # Simplified peak time and avg daily for static data
                analysis_results["peak_usage_times"][device_type] = "N/A (static data)"
                analysis_results["avg_daily_consumption_kwh"][device_type] = kwh

        logging.debug("Usage analysis completed")
        return analysis_results

    def generate_recommendations(self, analysis_results, profile=None, season="general"):
        """
        Generate energy optimization recommendations based on analysis.

        Args:
            analysis_results (dict): Results from analyze_usage.
            profile (dict, optional): User profile (e.g., {"type": "family", "behavior": "reckless"}).
            season (str): Current season (e.g., "summer", "winter").

        Returns:
            list: List of recommendation strings.
        """
        recommendations = []
        high_consumers = analysis_results["high_consumption_appliances"]
        peak_times = analysis_results["peak_usage_times"]

        # General recommendations
        if high_consumers:
            recommendations.append(
                "Consider upgrading these high-consumption appliances to energy-efficient models: "
                f"{', '.join(high_consumers)}."
            )

        # Peak usage recommendations
        for device, peak_hour in peak_times.items():
            if peak_hour != "N/A (static data)" and 12 <= int(peak_hour) <= 18:  # Assuming 12-6 PM as peak
                recommendations.append(
                    f"Shift usage of {device} from peak hour ({peak_hour}:00) to off-peak times (e.g., after 18:00)."
                )

        # Profile-specific recommendations
        if profile:
            if profile.get("behavior") == "reckless":
                recommendations.append("Reduce unnecessary usage duration to save energy.")
            if profile.get("type") == "family":
                recommendations.append("Coordinate appliance use to avoid simultaneous high consumption.")

        # Seasonal recommendations
        if season == "summer" and "Air Conditioner" in analysis_results["total_consumption_kwh"]:
            recommendations.append(
                "Optimize air conditioner settings: set thermostat higher (e.g., 24°C) or use fans."
            )
        elif season == "winter" and "Heater" in analysis_results["total_consumption_kwh"]:
            recommendations.append(
                "Set heater thermostat lower (e.g., 20°C) and use blankets for comfort."
            )

        logging.debug("Recommendations generated")
        return recommendations

    def simulate_savings(self, original_data, modifications):
        """
        Simulate potential savings by modifying usage patterns.

        Args:
            original_data (list): Original appliance data.
            modifications (dict): {device_type: reduction_factor} e.g., {"Heater": 0.2} for 20% reduction.

        Returns:
            float: Estimated savings in cents.
        """
        modified_data = original_data.copy()
        for device_type, reduction in modifications.items():
            for appliance in modified_data:
                if appliance["Device Type"] == device_type:
                    original_duration = appliance["Usage Duration (minutes)"]
                    appliance["Usage Duration (minutes)"] *= (1 - reduction)

        # Recalculate costs
        from preprocessor import Preprocessor  # Assuming this exists in your codebase
        preprocessor = Preprocessor()
        features, _ = preprocessor.preprocess_data(modified_data)
        daily_costs = self.bill_calculator.calculate_daily_costs(features)
        new_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(daily_costs)

        # Original bill
        orig_features, _ = preprocessor.preprocess_data(original_data)
        orig_daily_costs = self.bill_calculator.calculate_daily_costs(orig_features)
        orig_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(orig_daily_costs)

        savings = orig_monthly_bill - new_monthly_bill
        logging.debug(f"Simulated savings: ${savings/100:.2f}")
        return savings