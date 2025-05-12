import sys
import os
import copy
import numpy as np
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from PyQt5.QtCore import QTime
from model_loader import ModelLoader
from preprocessor import preprocess_appliances
from bill_calculator import BillCalculator
from appliance_balancer import ApplianceBalancer
from data_manager import DataManager
from gui_components import EnergyCostPredictorGUI
from adjustment_dialog import AdjustmentDialog
from preprocessor import preprocess_appliances
from usage_analyzer import UsageAnalyzer
from smart_automator import SmartAutomator
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to get the base path of the executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to Model
        return os.path.dirname(script_dir)

# Function to dynamically locate data.csv
def locate_data_csv(base_path):
    """
    Search for data.csv in the base path or subdirectories.
    If not found, prompt the user to select it.

    Args:
        base_path (str): Base directory to start the search.

    Returns:
        str: Path to data.csv or None if not found/selected.
    """
    possible_paths = [
        os.path.join(base_path, "data.csv"),
        os.path.join(base_path, "data", "data.csv"),
        os.path.join(base_path, "mock_dataset", "data.csv")
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logging.debug(f"Found data.csv at {path}")
            return path
    
    # If not found, prompt user to select the file
    app = QApplication.instance() or QApplication(sys.argv)
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select Energy Consumption Data File",
        base_path,
        "CSV Files (*.csv)"
    )
    if file_path:
        logging.debug(f"User selected data.csv at {file_path}")
        return file_path
    else:
        logging.warning("No data.csv selected")
        return None

class EnergyCostPredictorApp:
    def __init__(self):
        """
        Initialize the EnergyCostPredictorApp.
        """
        # Initialize model loader
        self.model_loader = ModelLoader()
        success, message = self.model_loader.load_assets()
        if not success:
            QMessageBox.critical(None, "Error", message)
            sys.exit(1)

        # Initialize data manager
        self.data_manager = DataManager()

        # Initialize bill calculator
        self.bill_calculator = BillCalculator(self.model_loader.model)

        # Initialize appliance balancer
        self.appliance_balancer = ApplianceBalancer(self.bill_calculator)

        # Dynamically locate data.csv
        base_path = get_base_path()
        csv_path = locate_data_csv(base_path)
        if not csv_path:
            QMessageBox.critical(None, "Error", "Could not locate or select data.csv. Exiting.")
            sys.exit(1)

        # Initialize UsageAnalyzer and SmartAutomator with dynamic CSV path
        self.analyzer = UsageAnalyzer(csv_path)
        self.automator = SmartAutomator(self.analyzer)

        # Define energy profiles
        self.energy_profiles = {
            "Eco": {
                "max_monthly_bill": 50.0,
                "usage_factors": {
                    "Heater": 0.5,
                    "Air Conditioner": 0.5,
                    "Microwave": 0.7,
                    "TV": 0.7,
                    "Ceiling Fan": 0.8,
                    "default": 0.9
                }
            },
            "Balanced": {
                "max_monthly_bill": 100.0,
                "usage_factors": {
                    "Heater": 0.8,
                    "Air Conditioner": 0.8,
                    "Microwave": 0.9,
                    "TV": 0.9,
                    "Ceiling Fan": 0.9,
                    "default": 1.0
                }
            },
            "Comfort": {
                "max_monthly_bill": 150.0,
                "usage_factors": {
                    "Heater": 1.0,
                    "Air Conditioner": 1.0,
                    "Microwave": 1.0,
                    "TV": 1.0,
                    "Ceiling Fan": 1.0,
                    "default": 1.0
                }
            },
            "Normal": {
                "max_monthly_bill": 200.0,
                "usage_factors": {
                    "Heater": 1.0,
                    "Air Conditioner": 1.0,
                    "Microwave": 1.0,
                    "TV": 1.0,
                    "Ceiling Fan": 1.0,
                    "default": 1.0
                }
            }
        }

        # Initialize app
        self.app = QApplication(sys.argv)
        self.gui = EnergyCostPredictorGUI(
            self.set_threshold,
            self.load_dataset,
            self.automator
        )
        self.gui.populate_dropdowns(
            list(self.model_loader.device_encoder.classes_),
            list(self.model_loader.room_encoder.classes_)
        )
        self.gui.profile_changed.connect(self.change_profile)
        self.gui.time_settings_changed.connect(self.handle_time_settings)
        self.gui.show()

    def load_dataset(self):
        """
        Handle the "Load Appliances" button click to select a JSON file and load appliances.
        """
        try:
            # Open a file dialog to select a JSON dataset
            file_path, _ = QFileDialog.getOpenFileName(
                self.gui,
                "Select Appliances Dataset",
                os.path.join(get_base_path(), "mock_dataset"),
                "JSON Files (*.json)"
            )
            if not file_path:
                logging.debug("No file selected in file dialog")
                QMessageBox.warning(self.gui, "Warning", "No file selected.")
                return

            # Load the selected dataset
            if not self.data_manager.load_data_from_file(file_path):
                QMessageBox.warning(self.gui, "Error", "Failed to load dataset. Please select a valid JSON file.")
                return

            # Preprocess appliances and calculate initial costs
            self.appliances = self.data_manager.get_appliances()
            self.original_appliances = copy.deepcopy(self.appliances)  # Store original data
            scaled_features, valid_indices = preprocess_appliances(
                self.appliances,
                self.model_loader.device_encoder,
                self.model_loader.room_encoder,
                self.model_loader.scaler
            )
            if scaled_features is None:
                QMessageBox.warning(self.gui, "Error", "Failed to preprocess appliances.")
                return

            # Calculate daily costs
            self.daily_costs = self.bill_calculator.calculate_daily_costs(scaled_features)
            self.valid_indices = valid_indices
            self.adjusted_indices = []  # Initialize empty adjusted indices

            # Update the table with the original data
            self.gui.populate_table(self.appliances, self.daily_costs, self.adjusted_indices)

            # Update original monthly bill display (default to Normal profile)
            adjusted_appliances = copy.deepcopy(self.original_appliances)
            profile = self.energy_profiles["Normal"]
            usage_factors = profile["usage_factors"]
            for idx, appliance in enumerate(adjusted_appliances):
                device_type = appliance["Device Type"]
                factor = usage_factors.get(device_type, usage_factors["default"])
                original_usage = appliance["Usage Duration (minutes)"]
                new_usage = original_usage * factor
                if new_usage != original_usage:
                    self.adjusted_indices.append(idx)
                appliance["Usage Duration (minutes)"] = new_usage
            scaled_features, valid_indices = preprocess_appliances(
                adjusted_appliances,
                self.model_loader.device_encoder,
                self.model_loader.room_encoder,
                self.model_loader.scaler
            )
            if scaled_features is not None:
                daily_costs = self.bill_calculator.calculate_daily_costs(scaled_features)
                total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(daily_costs)
                self.gui.update_monthly_bill(total_monthly_bill)
            self.gui.threshold_var.setValue(profile["max_monthly_bill"])
        except Exception as e:
            logging.error(f"Error in load_dataset: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to load dataset: {str(e)}")

    def change_profile(self, profile_name):
        """
        Handle profile change by updating threshold, displaying usage limits, and calculating predicted bill
        without modifying the appliances table.

        Args:
            profile_name (str): Name of the selected profile.
        """
        try:
            if profile_name not in self.energy_profiles:
                logging.warning(f"Invalid profile: {profile_name}")
                return

            profile = self.energy_profiles[profile_name]
            max_monthly_bill = profile["max_monthly_bill"]
            usage_factors = profile["usage_factors"]

            # Update threshold in GUI
            self.gui.threshold_var.setValue(max_monthly_bill)

            # Display usage limits in QTextEdit (single list without Limited/Unlimited)
            message = f"Profile: {profile_name}\n\n"
            usage_limits = []
            for device, factor in usage_factors.items():
                if factor < 1.0:
                    usage_limits.append(f"{device}: Reduced by {(1.0 - factor) * 100:.0f}%")
                else:
                    usage_limits.append(f"{device}: No reduction")
            message += "\n".join(usage_limits)
            self.gui.profile_info.setText(message)

            # Calculate predicted bill without modifying the table
            if hasattr(self, 'original_appliances') and self.original_appliances:
                # Work with a fresh copy of original appliances
                adjusted_appliances = copy.deepcopy(self.original_appliances)
                adjusted_indices = []
                for idx, appliance in enumerate(adjusted_appliances):
                    device_type = appliance["Device Type"]
                    factor = usage_factors.get(device_type, usage_factors["default"])
                    original_usage = appliance["Usage Duration (minutes)"]
                    new_usage = original_usage * factor
                    if new_usage != original_usage:
                        adjusted_indices.append(idx)
                    appliance["Usage Duration (minutes)"] = new_usage

                # Calculate costs for adjusted appliances
                scaled_features, valid_indices = preprocess_appliances(
                    adjusted_appliances,
                    self.model_loader.device_encoder,
                    self.model_loader.room_encoder,
                    self.model_loader.scaler
                )
                if scaled_features is not None:
                    daily_costs = self.bill_calculator.calculate_daily_costs(scaled_features)
                    # Update original bill display (table remains unchanged)
                    total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(daily_costs)
                    self.gui.update_monthly_bill(total_monthly_bill)

            logging.debug(f"Profile changed to {profile_name} with max bill ${max_monthly_bill}")
        except Exception as e:
            logging.error(f"Error in change_profile: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to change profile: {str(e)}")

    def handle_time_settings(self, time_str, heater_on, water_heater_on):
        """
        Handle changes to arrival time and appliance activation settings.

        Args:
            time_str (str): Arrival time in HH:mm format.
            heater_on (bool): Whether to turn on the heater.
            water_heater_on (bool): Whether to turn on the water heater.
        """
        try:
            logging.debug(f"Received time settings: Arrival {time_str}, Heater {heater_on}, Water Heater {water_heater_on}")
            # Placeholder for scheduling logic (e.g., turning on heater/water heater at specified time)
        except Exception as e:
            logging.error(f"Error in handle_time_settings: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to update time settings: {str(e)}")

    def set_threshold(self):
        """
        Handle setting the maximum monthly bill threshold by balancing appliance usage.
        """
        try:
            max_monthly_bill = self.gui.get_threshold()
            if not hasattr(self, 'appliances') or not self.appliances:
                QMessageBox.warning(self.gui, "Warning", "No appliances loaded. Please load a dataset first.")
                return

            adjusted_appliances, adjustments = self.appliance_balancer.balance_appliances(
                self.appliances,
                self.daily_costs,
                max_monthly_bill,
                self.valid_indices
            )

            # Update appliances with adjusted values
            self.adjusted_indices = [idx for idx in range(len(adjusted_appliances))
                                    if adjusted_appliances[idx]["Usage Duration (minutes)"] !=
                                       self.appliances[idx]["Usage Duration (minutes)"]]
            self.data_manager.update_appliances(adjusted_appliances)
            self.appliances = adjusted_appliances

            # Recalculate daily costs with adjusted usage
            scaled_features, valid_indices = preprocess_appliances(
                self.appliances,
                self.model_loader.device_encoder,
                self.model_loader.room_encoder,
                self.model_loader.scaler
            )
            if scaled_features is not None:
                self.daily_costs = self.bill_calculator.calculate_daily_costs(scaled_features)
                self.valid_indices = valid_indices
                self.gui.populate_table(self.appliances, self.daily_costs, self.adjusted_indices)

                # Update original monthly bill display
                total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(self.daily_costs)
                self.gui.update_monthly_bill(total_monthly_bill)

            # Show adjustments in a dialog
            dialog = AdjustmentDialog(adjustments, self.appliances, self.gui)
            dialog.exec_()
        except Exception as e:
            logging.error(f"Error in set_threshold: {str(e)}")
            QMessageBox.critical(self.gui, "Error", f"Failed to set threshold: {str(e)}")

    def run(self):
        """
        Run the application.
        """
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = EnergyCostPredictorApp()
    app.run()