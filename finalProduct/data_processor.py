import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataProcessor:
    def __init__(self, model, le_device, le_room):
        self.model = model
        self.le_device = le_device
        self.le_room = le_room
        self.daily_costs = None
        self.scaler = StandardScaler()

    def predict_costs(self, appliances):
        if not appliances or self.model is None:
            logging.warning("No appliances or model not loaded")
            return

        # Create DataFrame from array of objects
        data = []
        for appliance in appliances:
            try:
                device_type = self.le_device.transform([appliance['device_type']])[0]
            except ValueError:
                logging.error(f"Invalid device type: {appliance['device_type']}")
                continue
            data.append({
                'Device Type': device_type,
                'Power Consumption (W)': appliance['power_watts'],
                'Room Location': self.le_room.transform(['Living Room'])[0],
                'Temperature (°C)': 22.0,
                'Humidity (%)': 55.0,
                'Usage Duration (minutes)': appliance['daily_usage_hours'] * 60,
                'On/Off Status': 1
            })
        if not data:
            logging.warning("No valid appliances to process")
            return

        df = pd.DataFrame(data)
        logging.debug(f"DataFrame created with {len(df)} appliances")

        # Scale features
        df_scaled = pd.DataFrame(self.scaler.fit_transform(df), columns=df.columns)

        # Predict daily cost
        self.daily_costs = self.model.predict(df_scaled)
        logging.debug(f"Predicted daily costs: {self.daily_costs}")

        # Update appliances with monthly costs (30 days)
        for i, appliance in enumerate(appliances):
            if i < len(self.daily_costs):
                appliance['predicted_cost'] = self.daily_costs[i] * 30
                appliance['adjusted_usage_hours'] = appliance['daily_usage_hours']
                appliance['adjusted_power_watts'] = appliance['power_watts']
                appliance['adjusted_cost'] = appliance['predicted_cost']
                appliance['action'] = ''
            else:
                appliance['predicted_cost'] = 0.0
                appliance['adjusted_usage_hours'] = appliance['daily_usage_hours']
                appliance['adjusted_power_watts'] = appliance['power_watts']
                appliance['adjusted_cost'] = 0.0
                appliance['action'] = 'Invalid device type'

    def apply_threshold(self, appliances, threshold):
        if threshold <= 0:
            logging.debug("Threshold not set, skipping adjustments")
            return

        # Calculate total predicted cost
        total_cost = sum(appliance['adjusted_cost'] for appliance in appliances)
        logging.debug(f"Total adjusted cost: ${total_cost:.2f}, Threshold: ${threshold:.2f}")

        if total_cost <= threshold:
            logging.debug("Total cost below threshold, no adjustments needed")
            self.output_adjustments(appliances, threshold, sum(appliance['predicted_cost'] for appliance in appliances), total_cost)
            return

        # Sort appliances by adjusted cost
        sorted_appliances = sorted(appliances, key=lambda x: x['adjusted_cost'], reverse=True)
        high_cost_devices = ['Heater', 'Air Conditioner', 'Microwave', 'Washing Machine']

        # Calculate cost per hour for each appliance
        for appliance in sorted_appliances:
            if appliance['daily_usage_hours'] > 0:
                appliance['cost_per_hour'] = appliance['adjusted_cost'] / (appliance['daily_usage_hours'] * 30)
            else:
                appliance['cost_per_hour'] = 0.0

        # Adjust usage time to meet threshold
        while total_cost > threshold:
            excess_cost = total_cost - threshold
            total_cost_per_hour = sum(appliance['cost_per_hour'] for appliance in sorted_appliances 
                                      if appliance['device_type'] in high_cost_devices and appliance['adjusted_usage_hours'] > appliance['daily_usage_hours'] * 0.5)
            
            if total_cost_per_hour == 0:
                break  # No more adjustments possible without exceeding 50% reduction

            # Distribute reduction proportionally
            for appliance in sorted_appliances:
                if appliance['device_type'] not in high_cost_devices:
                    continue
                if appliance['adjusted_usage_hours'] <= appliance['daily_usage_hours'] * 0.5:
                    continue

                cost_per_hour = appliance['cost_per_hour']
                if cost_per_hour == 0:
                    continue

                # Calculate hours to reduce for this appliance
                cost_to_reduce = (excess_cost * (cost_per_hour / total_cost_per_hour))
                hours_to_reduce = (cost_to_reduce / cost_per_hour) / 30  # Convert cost to daily hours
                current_usage = appliance['adjusted_usage_hours']
                new_usage = max(current_usage - hours_to_reduce, appliance['daily_usage_hours'] * 0.5)

                if new_usage < current_usage:
                    appliance['adjusted_usage_hours'] = new_usage
                    reduction_percent = ((current_usage - new_usage) / appliance['daily_usage_hours']) * 100
                    appliance['action'] = f"Reduced usage by {reduction_percent:.1f}% to {new_usage:.2f} hours"

                    # Recalculate cost
                    data = [{
                        'Device Type': self.le_device.transform([appliance['device_type']])[0],
                        'Power Consumption (W)': appliance['adjusted_power_watts'],
                        'Room Location': self.le_room.transform(['Living Room'])[0],
                        'Temperature (°C)': 22.0,
                        'Humidity (%)': 55.0,
                        'Usage Duration (minutes)': appliance['adjusted_usage_hours'] * 60,
                        'On/Off Status': 1
                    }]
                    df = pd.DataFrame(data)
                    df_scaled = pd.DataFrame(self.scaler.transform(df), columns=df.columns)
                    appliance['adjusted_cost'] = self.model.predict(df_scaled)[0] * 30
                    logging.debug(f"Adjusted usage for {appliance['device_type']}, new cost: ${appliance['adjusted_cost']:.2f}")

            total_cost = sum(appliance['adjusted_cost'] for appliance in appliances)

        # If still over threshold, reduce power
        if total_cost > threshold:
            excess_cost = total_cost - threshold
            total_cost_per_watt = sum(appliance['adjusted_cost'] / appliance['adjusted_power_watts'] 
                                      for appliance in sorted_appliances 
                                      if appliance['device_type'] in high_cost_devices and appliance['adjusted_power_watts'] > appliance['power_watts'] * 0.8)
            
            if total_cost_per_watt > 0:
                for appliance in sorted_appliances:
                    if appliance['device_type'] not in high_cost_devices:
                        continue
                    if appliance['adjusted_power_watts'] <= appliance['power_watts'] * 0.8:
                        continue

                    cost_per_watt = appliance['adjusted_cost'] / appliance['adjusted_power_watts']
                    if cost_per_watt == 0:
                        continue

                    # Calculate watts to reduce
                    cost_to_reduce = (excess_cost * (cost_per_watt / total_cost_per_watt))
                    watts_to_reduce = (cost_to_reduce / cost_per_watt) * 30  # Convert cost to watts
                    current_power = appliance['adjusted_power_watts']
                    new_power = max(current_power - watts_to_reduce, appliance['power_watts'] * 0.8)

                    if new_power < current_power:
                        appliance['adjusted_power_watts'] = new_power
                        reduction_percent = ((current_power - new_power) / appliance['power_watts']) * 100
                        appliance['action'] += f"; Reduced power by {reduction_percent:.1f}% to {new_power:.2f} W"

                        # Recalculate cost
                        data = [{
                            'Device Type': self.le_device.transform([appliance['device_type']])[0],
                            'Power Consumption (W)': appliance['adjusted_power_watts'],
                            'Room Location': self.le_room.transform(['Living Room'])[0],
                            'Temperature (°C)': 22.0,
                            'Humidity (%)': 55.0,
                            'Usage Duration (minutes)': appliance['adjusted_usage_hours'] * 60,
                            'On/Off Status': 1
                        }]
                        df = pd.DataFrame(data)
                        df_scaled = pd.DataFrame(self.scaler.transform(df), columns=df.columns)
                        appliance['adjusted_cost'] = self.model.predict(df_scaled)[0] * 30
                        logging.debug(f"Adjusted power for {appliance['device_type']}, new cost: ${appliance['adjusted_cost']:.2f}")

            total_cost = sum(appliance['adjusted_cost'] for appliance in appliances)

        self.output_adjustments(appliances, threshold, sum(appliance['predicted_cost'] for appliance in appliances), total_cost)

    def output_adjustments(self, appliances, threshold, original_total, adjusted_total):
        """
        Output adjustments to a formatted text file.
        """
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = f"d:/Desktop/Big Data/Model/finalProduct/adjustments_{timestamp}.txt"
        
        with open(output_file, 'w') as f:
            f.write("Smart Home Energy Adjustments Report\n")
            f.write("=" * 35 + "\n\n")
            f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Maximum Electricity Bill: ${threshold:.2f}\n")
            f.write(f"Original Total Bill: ${original_total:.2f}\n")
            f.write(f"Adjusted Total Bill: ${adjusted_total:.2f}\n")
            f.write(f"Savings: ${original_total - adjusted_total:.2f}\n\n")
            f.write("Appliance Adjustments:\n")
            f.write("-" * 35 + "\n")

            for appliance in appliances:
                f.write(f"Device: {appliance['device_type']}\n")
                f.write(f"  Original Usage: {appliance['daily_usage_hours']:.2f} hours\n")
                f.write(f"  Adjusted Usage: {appliance['adjusted_usage_hours']:.2f} hours\n")
                f.write(f"  Original Power: {appliance['power_watts']:.2f} W\n")
                f.write(f"  Adjusted Power: {appliance['adjusted_power_watts']:.2f} W\n")
                f.write(f"  Original Cost: ${appliance['predicted_cost']:.2f}\n")
                f.write(f"  Adjusted Cost: ${appliance['adjusted_cost']:.2f}\n")
                f.write(f"  Action: {appliance['action'] if appliance['action'] else 'No adjustment'}\n")
                f.write("-" * 35 + "\n")
        
        logging.debug(f"Adjustments written to {output_file}")