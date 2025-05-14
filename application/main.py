import sys
import os
import copy
import numpy as np
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer, QTime
from model_loader import ModelLoader
from preprocessor import preprocess_appliances
from bill_calculator import BillCalculator
from data_manager import DataManager
from gui_components import EnergyCostPredictorGUI, SettingsDialog
import urllib.request
import logging
import pickle
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.dirname(script_dir)

class EnergyCostPredictorApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.model_loader = ModelLoader()
        success, message = self.model_loader.load_assets()
        if not success:
            QMessageBox.critical(None, "Error", message)
            sys.exit(1)

        self.data_manager = DataManager()
        self.bill_calculator = BillCalculator(self.model_loader.model)

        self.energy_profiles = {
            "Eco": {
                "usage_factors": {
                    "Heater": 0.5,
                    "Air Conditioner": 0.5,
                    "Microwave": 0.7,
                    "TV": 0.7,
                    "Ceiling Fan": 0.8,
                    "Smart Plug": 0.9,
                    "Laptop Charger": 0.9,
                    "Refrigerator": 1.0,
                    "default": 0.9
                }
            },
            "Balanced": {
                "usage_factors": {
                    "Heater": 0.8,
                    "Air Conditioner": 0.8,
                    "Microwave": 0.9,
                    "TV": 0.9,
                    "Ceiling Fan": 0.9,
                    "Smart Plug": 0.95,
                    "Laptop Charger": 0.95,
                    "Refrigerator": 1.0,
                    "default": 1.0
                }
            },
            "Comfort": {
                "usage_factors": {
                    "Heater": 1.0,
                    "Air Conditioner": 1.0,
                    "Microwave": 1.0,
                    "TV": 1.0,
                    "Ceiling Fan": 1.0,
                    "Smart Plug": 1.0,
                    "Laptop Charger": 1.0,
                    "Refrigerator": 1.0,
                    "default": 1.0
                }
            },
            "Normal": {
                "usage_factors": {
                    "Heater": 1.0,
                    "Air Conditioner": 1.0,
                    "Microwave": 1.0,
                    "TV": 1.0,
                    "Ceiling Fan": 1.0,
                    "Smart Plug": 1.0,
                    "Laptop Charger": 1.0,
                    "Refrigerator": 1.0,
                    "default": 1.0
                }
            }
        }

        self.gui = EnergyCostPredictorGUI(self.load_dataset)
        self.gui.populate_dropdowns(
            list(self.model_loader.device_encoder.classes_),
            list(self.model_loader.room_encoder.classes_)
        )
        self.gui.profile_changed.connect(self.change_profile)
        self.gui.bill_update_requested.connect(self.update_bill_for_day)
        self.gui.check_model_update.connect(self.check_for_model_update)
        self.gui.open_settings.connect(self.open_settings_dialog)
        self.gui.toggle_owner_home.connect(self.toggle_owner_home)
        self.gui.save_return_time.connect(self.save_return_time_handler)

        # Initialize settings with defaults
        self.settings = {
            "ac_temp_threshold": 25,
            "heater_temp_threshold": 18,
            "turn_on_before": {
                "Air Conditioner": 30,
                "Heater": 30,
                "Water Heater": 30,
                "Dehumidifier": 30
            },
            "turn_off_period": 60,
            "grace_period": 15
        }

        # Owner state management
        self.owner_home = False
        self.appliance_states = {
            "Air Conditioner": False,
            "Heater": False,
            "Water Heater": False,
            "Dehumidifier": False,
            "Refrigerator": True
        }
        self.time_away = 0
        self.grace_countdown = 0
        self.return_time_passed = False
        self.saved_return_time = None  # Initially no saved return time

        # Timer for owner status updates
        self.owner_status_timer = QTimer()
        self.owner_status_timer.timeout.connect(self.update_owner_status)
        self.owner_status_timer.start(60000)

        self.update_weather_display()
        self.weather_timer = QTimer()
        self.weather_timer.timeout.connect(self.update_weather_display)
        self.weather_timer.start(30 * 60 * 1000)
        self.current_model_folder = None
        self.current_profile = "Normal"
        self.gui.show()

        self.model_folders_file = os.path.join(get_base_path(), "model_folders.txt")
        if not os.path.exists(self.model_folders_file):
            with open(self.model_folders_file, 'w') as f:
                f.write("")

    def save_return_time_handler(self):
        """Handle the saving of the return time and trigger an immediate status update."""
        self.saved_return_time = self.gui.expected_return_time_edit.time()
        logging.debug(f"Saved return time: {self.saved_return_time.toString('HH:mm')}")
        self.update_owner_status()

    def load_seen_folders(self):
        seen_folders = set()
        try:
            with open(self.model_folders_file, 'r') as f:
                for line in f:
                    folder = line.strip()
                    if folder:
                        seen_folders.add(folder)
        except Exception as e:
            logging.error(f"Failed to read model_folders.txt: {str(e)}")
        return seen_folders

    def save_seen_folders(self, seen_folders):
        try:
            with open(self.model_folders_file, 'w') as f:
                for folder in sorted(seen_folders):
                    f.write(f"{folder}\n")
        except Exception as e:
            logging.error(f"Failed to write to model_folders.txt: {str(e)}")

    def toggle_owner_home(self):
        self.owner_home = not self.owner_home
        if self.owner_home:
            self.grace_countdown = 0
            self.return_time_passed = False
            self.time_away = 0
        else:
            self.time_away = 0
        self.update_owner_status()

    def reduce_appliance_power(self):
        if not hasattr(self, 'original_appliances') or not self.original_appliances:
            return
        for appliance in self.original_appliances:
            device_type = appliance["Device Type"]
            if device_type != "Refrigerator":
                original_usage = appliance["Usage Duration (minutes)"]
                reduced_usage = original_usage * 0.5
                appliance["Usage Duration (minutes)"] = reduced_usage
                logging.debug(f"Reduced power for {device_type}: {original_usage} -> {reduced_usage} minutes")
        self.calculate_monthly_bill_for_7_days()

    def update_owner_status(self):
        current_time = QTime.currentTime()
        if self.owner_home:
            self.gui.owner_status_label.setText("Owner is home")
            self.time_away = 0
            self.grace_countdown = 0
            self.return_time_passed = False
            for appliance in ["Air Conditioner", "Heater", "Water Heater", "Dehumidifier"]:
                self.appliance_states[appliance] = True
        else:
            if self.gui.enable_return_time_checkbox.isChecked() and self.saved_return_time:
                if current_time < self.saved_return_time:
                    time_left = current_time.secsTo(self.saved_return_time) // 60
                    hours = time_left // 60
                    minutes = time_left % 60
                    self.gui.owner_status_label.setText(f"Time left: {hours:02d}:{minutes:02d}")
                    self.return_time_passed = False
                    for appliance in ["Air Conditioner", "Heater", "Water Heater", "Dehumidifier"]:
                        turn_on_before = self.settings["turn_on_before"][appliance]
                        if time_left <= turn_on_before:
                            self.appliance_states[appliance] = True
                        else:
                            self.appliance_states[appliance] = False
                else:
                    if not self.return_time_passed:
                        self.return_time_passed = True
                        self.grace_countdown = self.settings["grace_period"]
                        logging.debug(f"Return time passed. Starting grace period countdown: {self.grace_countdown} minutes")
                    if self.grace_countdown > 0:
                        hours = self.grace_countdown // 60
                        minutes = self.grace_countdown % 60
                        self.gui.owner_status_label.setText(f"Missed Return - Grace Period: {hours:02d}:{minutes:02d}")
                        self.grace_countdown -= 1
                    else:
                        self.gui.owner_status_label.setText("Grace Period Ended - Power Reduced")
                        self.reduce_appliance_power()
                        for appliance in ["Air Conditioner", "Heater", "Water Heater", "Dehumidifier"]:
                            self.appliance_states[appliance] = False
            else:
                self.gui.owner_status_label.setText("Away")
                self.return_time_passed = False
                self.grace_countdown = 0
                turn_off_period = self.settings["turn_off_period"]
                if self.time_away >= turn_off_period:
                    turn_off_order = ["Dehumidifier", "Water Heater", "Heater", "Air Conditioner"]
                    for i, appliance in enumerate(turn_off_order):
                        if self.time_away >= turn_off_period + i * 5:
                            self.appliance_states[appliance] = False
            self.time_away += 1
        logging.debug(f"Owner status updated: Home={self.owner_home}, States={self.appliance_states}")

    def open_settings_dialog(self):
        if not hasattr(self, 'original_appliances') or not self.original_appliances:
            QMessageBox.warning(self.gui, "Warning", "Please load a dataset first.")
            return
        dialog = SettingsDialog(self.gui)
        if dialog.exec_():
            self.settings = dialog.get_settings()
            logging.debug(f"Settings updated: {self.settings}")
            self.update_weather_display()

    def check_for_model_update(self):
        try:
            seen_folders = self.load_seen_folders()
            storage_client = storage.Client(credentials=AnonymousCredentials())
            bucket = storage_client.bucket("big_data32")
            blobs = bucket.list_blobs(delimiter="/")
            current_folders = set(blob.name.split('/')[0] for blob in blobs if '/' in blob.name)
            new_seen_folders = seen_folders.union(current_folders)
            self.save_seen_folders(new_seen_folders)
            new_folders = current_folders - seen_folders
            if not new_folders:
                QMessageBox.information(self.gui, "No Update Found", "No new model folders found.")
                return
            for folder in sorted(new_folders):
                model_url = f"https://storage.googleapis.com/big_data32/{folder}/gb_model.pkl"
                try:
                    urllib.request.urlopen(model_url).close()
                except urllib.error.HTTPError as e:
                    continue
                model_path = os.path.join(get_base_path(), "models", "gb_model.pkl")
                old_model_path = model_path + ".old"
                os.makedirs(os.path.dirname(model_path), exist_ok=True)
                if os.path.exists(model_path):
                    os.rename(model_path, old_model_path)
                    os.remove(old_model_path)
                urllib.request.urlretrieve(model_url, model_path)
                self.model_loader.model = pickle.load(open(model_path, "rb"))
                self.bill_calculator = BillCalculator(self.model_loader.model)
                self.current_model_folder = folder
                QMessageBox.information(
                    self.gui,
                    "Model Updated",
                    f"The new model from {folder} has been downloaded and replaced."
                )
            if new_folders and hasattr(self, 'original_appliances') and self.original_appliances:
                self.calculate_monthly_bill_for_7_days()
        except Exception as e:
            logging.error(f"Error checking for model update: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to check for model update: {str(e)}")

    def calculate_monthly_bill_for_7_days(self):
        try:
            if not hasattr(self, 'original_appliances') or not self.original_appliances:
                self.gui.update_monthly_bill(0.0)
                return
            dates = sorted(list(set(item["Date"] for item in self.original_appliances)))
            if len(dates) != 7:
                self.gui.update_monthly_bill(0.0)
                return
            profile = self.energy_profiles[self.current_profile]
            usage_factors = profile["usage_factors"]
            total_daily_costs = 0.0
            num_days = len(dates)
            for date in dates:
                daily_data = [item for item in self.original_appliances if item["Date"] == date]
                adjusted_appliances = copy.deepcopy(daily_data)
                for idx, appliance in enumerate(adjusted_appliances):
                    device_type = appliance["Device Type"]
                    factor = usage_factors.get(device_type, usage_factors["default"])
                    original_usage = appliance["Usage Duration (minutes)"]
                    appliance["Usage Duration (minutes)"] = original_usage * factor
                scaled_features, valid_indices = preprocess_appliances(
                    adjusted_appliances,
                    self.model_loader.device_encoder,
                    self.model_loader.room_encoder,
                    self.model_loader.scaler
                )
                if scaled_features is not None:
                    daily_costs = self.bill_calculator.calculate_daily_costs(scaled_features)
                    total_daily_costs += sum(daily_costs)
                else:
                    self.gui.update_monthly_bill(0.0)
                    return
            average_daily_cost = total_daily_costs / num_days
            total_monthly_bill = average_daily_cost 
            self.gui.update_monthly_bill(total_monthly_bill)
        except Exception as e:
            logging.error(f"Error calculating monthly bill for 7 days: {str(e)}")
            self.gui.update_monthly_bill(0.0)

    def load_dataset(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self.gui,
                "Select Appliances Dataset",
                os.path.join(get_base_path(), "mock_dataset"),
                "JSON Files (*.json)"
            )
            if not file_path:
                QMessageBox.warning(self.gui, "Warning", "No file selected.")
                return
            if not self.data_manager.load_data_from_file(file_path):
                QMessageBox.warning(self.gui, "Error", "Failed to load dataset. Please select a valid JSON file.")
                return
            self.appliances = self.data_manager.get_appliances()
            self.original_appliances = copy.deepcopy(self.appliances)
            self.gui.set_weekly_data(self.appliances)
            if self.appliances:
                self.calculate_monthly_bill_for_7_days()
            else:
                QMessageBox.warning(self.gui, "Error", "Empty dataset loaded.")
        except Exception as e:
            logging.error(f"Error in load_dataset: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to load dataset: {str(e)}")

    def change_profile(self, profile_name):
        try:
            if profile_name not in self.energy_profiles:
                return
            self.current_profile = profile_name
            profile = self.energy_profiles[profile_name]
            usage_factors = profile["usage_factors"]
            message = f"Profile: {profile_name}\n\n"
            usage_limits = []
            for device, factor in usage_factors.items():
                if factor < 1.0:
                    usage_limits.append(f"{device}: Reduced by {(1.0 - factor) * 100:.0f}%")
                else:
                    usage_limits.append(f"{device}: No reduction")
            message += "\n".join(usage_limits)
            self.gui.profile_info.setText(message)
            if hasattr(self, 'original_appliances') and self.original_appliances:
                self.calculate_monthly_bill_for_7_days()
        except Exception as e:
            logging.error(f"Error in change_profile: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to change profile: {str(e)}")

    def update_bill_for_day(self, daily_data):
        self.calculate_monthly_bill_for_7_days()

    def update_weather_display(self):
        try:
            location, temperature, humidity = ("Hanoi", 25.0, 60.0)
            if location is not None and temperature is not None and humidity is not None:
                self.gui.update_weather(location, temperature, humidity, self.settings)
            else:
                self.gui.update_weather(None, None, None, self.settings)
        except Exception as e:
            logging.error(f"Error updating weather display: {str(e)}")
            self.gui.update_weather(None, None, None, self.settings)

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = EnergyCostPredictorApp()
    app.run()