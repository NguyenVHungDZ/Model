import json
import os
from PyQt5.QtWidgets import QFileDialog
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MockDataLoader:
    def __init__(self, parent):
        self.parent = parent

    def load_dataset(self):
        """
        Open a file dialog to select a mock dataset JSON and return its appliances as an array of objects.
        """
        file_path, _ = QFileDialog.getOpenFileName(self.parent, "Select Mock Dataset", 
                                                  "d:/Desktop/Big Data/Model/finalProduct/mock_datasets", 
                                                  "JSON Files (*.json)")
        if not file_path:
            logging.debug("No file selected in file dialog")
            return None

        logging.debug(f"Selected file path: {file_path}")

        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            appliances = []
            required_fields = ['Device Type', 'Power Consumption (W)', 'Usage Duration (minutes)']
            if not isinstance(data, list):
                logging.error("JSON data is not a list of appliances")
                return None

            for item in data:
                if not isinstance(item, dict):
                    logging.error(f"Invalid item format, expected dict: {item}")
                    continue

                if not all(field in item for field in required_fields):
                    logging.error(f"Missing required fields in item: {item}, expected: {required_fields}")
                    continue

                # Convert usage duration from minutes to hours
                daily_usage_hours = item['Usage Duration (minutes)'] / 60.0
                appliances.append({
                    'device_type': item['Device Type'],
                    'daily_usage_hours': daily_usage_hours,
                    'power_watts': item['Power Consumption (W)'],
                    'predicted_cost': 0.0,
                    'adjusted_usage_hours': daily_usage_hours,
                    'adjusted_power_watts': item['Power Consumption (W)'],
                    'adjusted_cost': 0.0,
                    'action': ''
                })
            if not appliances:
                logging.warning("No valid appliances found in dataset")
                return None

            logging.debug(f"Loaded dataset from {file_path} with {len(appliances)} appliances")
            return appliances
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON format in file {file_path}: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Failed to load dataset from {file_path}: {str(e)}")
            return None