import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SmartAutomator:
    def __init__(self, analyzer):
        """
        Initialize the SmartAutomator with a UsageAnalyzer instance.

        Args:
            analyzer (UsageAnalyzer): Instance to analyze usage patterns.
        """
        self.analyzer = analyzer
        self.quiet_hours_threshold = 1000  # Example threshold in watts
        self.quiet_hours = self._identify_quiet_hours()
        logging.debug("SmartAutomator initialized")

    def _identify_quiet_hours(self):
        """
        Identify hours with consistently low activity based on historical data.

        Returns:
            list: Hours (0-23) with low activity.
        """
        hourly_activity = self.analyzer.data.groupby('Hour')['Power Consumption (W)'].mean()
        quiet_hours = hourly_activity[hourly_activity < self.quiet_hours_threshold].index.tolist()
        logging.debug(f"Identified quiet hours: {quiet_hours}")
        return quiet_hours

    def suggest_automation_rules(self):
        """
        Suggest automation rules to turn off lights during quiet hours.

        Returns:
            list: List of automation rules.
        """
        rules = []
        if self.quiet_hours:
            rules.append({
                "action": "Turn off lights",
                "condition": f"During quiet hours: {', '.join(map(str, self.quiet_hours))}",
                "time_range": "All days"
            })
        logging.debug(f"Suggested automation rules: {rules}")
        return rules

    def apply_automation(self, current_time):
        """
        Apply automation rules based on current time.

        Args:
            current_time (datetime): Current time.

        Returns:
            str: Action to take (e.g., "Turn off lights").
        """
        current_hour = current_time.hour
        if current_hour in self.quiet_hours:
            return "Turn off lights"
        return None

    def set_custom_rule(self, action, condition, time_range):
        """
        Allow users to define a custom automation rule.

        Args:
            action (str): Action to take (e.g., "Turn off TV").
            condition (str): Condition for action (e.g., "No activity for 1 hour").
            time_range (str): Time range (e.g., "09:00 - 17:00").

        Returns:
            dict: Custom rule dictionary.
        """
        rule = {"action": action, "condition": condition, "time_range": time_range}
        logging.debug(f"Custom rule set: {rule}")
        return rule