import sys
import os
import numpy as np
from PyQt5.QtWidgets import QApplication, QMessageBox, QFileDialog
from model_loader import ModelLoader
from preprocessor import preprocess_appliances
from bill_calculator import BillCalculator
from appliance_balancer import ApplianceBalancer
from data_manager import DataManager
from gui_components import EnergyCostPredictorGUI
from adjustment_dialog import AdjustmentDialog
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to get the base path of the executable or script
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Running as .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Running as script (inside lastestProduct)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to Model
        return os.path.dirname(script_dir)

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

        # Initialize app
        self.app = QApplication(sys.argv)
        self.gui = EnergyCostPredictorGUI(
            self.add_appliance,
            self.set_threshold,
            self.load_dataset,
            self.delete_row
        )
        self.gui.populate_dropdowns(
            list(self.model_loader.device_encoder.classes_),
            list(self.model_loader.room_encoder.classes_)
        )
        # Connect signal for delete action
        self.gui.delete_row_signal.connect(self.delete_row)
        self.gui.show()

    def load_dataset(self):
        """
        Handle the "Load Dataset" button click to select a JSON file and load appliances.
        """
        # Open a file dialog to select a JSON dataset
        file_path, _ = QFileDialog.getOpenFileName(
            self.gui,
            "Select Mock Dataset",
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

        # Update the table with the new data
        self.gui.populate_table(self.appliances, self.daily_costs)

        # Update monthly bill display
        total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(self.daily_costs)
        self.gui.update_monthly_bill(total_monthly_bill)

    def add_appliance(self):
        """
        Handle the "Add Appliance" button click to add a manually entered appliance to the list
        and append it to the JSON file.
        """
        inputs = self.gui.get_input_values()

        # Validate and convert numeric inputs to floats
        try:
            inputs["Power Consumption (W)"] = float(inputs["Power Consumption (W)"])
            inputs["Temperature (°C)"] = float(inputs["Temperature (°C)"])
            inputs["Humidity (%)"] = float(inputs["Humidity (%)"])
            inputs["Usage Duration (minutes)"] = float(inputs["Usage Duration (minutes)"])
        except ValueError as e:
            logging.error(f"Invalid numeric input: {str(e)}")
            QMessageBox.warning(self.gui, "Error", "Please enter valid numeric values for Power, Temperature, Humidity, and Duration.")
            return

        data = preprocess_appliances(
            [inputs],
            self.model_loader.device_encoder,
            self.model_loader.room_encoder,
            self.model_loader.scaler
        )
        scaled_features, valid_indices = data

        if scaled_features is None or not valid_indices:
            QMessageBox.warning(self.gui, "Error", "Invalid input. Please check your entries.")
            return

        # Calculate the daily cost for the new appliance
        prediction = self.bill_calculator.calculate_daily_costs(scaled_features)

        # Append the appliance to the JSON file
        if not self.data_manager.append_appliance_to_file(inputs):
            QMessageBox.warning(self.gui, "Error", "Failed to append appliance to JSON file.")
            return

        # Update the in-memory list
        self.appliances = self.data_manager.get_appliances()
        self.daily_costs = np.append(self.daily_costs, prediction[0])
        self.valid_indices.append(len(self.appliances) - 1)

        # Update the table
        self.gui.populate_table(self.appliances, self.daily_costs)

        # Update monthly bill display
        total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(self.daily_costs)
        self.gui.update_monthly_bill(total_monthly_bill)

        # Clear the input form
        self.gui.clear_form()

    def delete_row(self, row):
        """
        Handle the "Delete" button click for a specific row to remove the appliance.

        Args:
            row (int): The row index to delete.
        """
        if not self.data_manager.delete_appliance_at_index(row):
            QMessageBox.warning(self.gui, "Error", "Failed to delete appliance.")
            return

        # Update the in-memory lists
        self.appliances = self.data_manager.get_appliances()
        self.daily_costs = np.delete(self.daily_costs, row)
        self.valid_indices = [i if i < row else i - 1 for i in self.valid_indices if i != row]

        # Update the table
        self.gui.populate_table(self.appliances, self.daily_costs)

        # Update monthly bill display
        if len(self.daily_costs) > 0:
            total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(self.daily_costs)
        else:
            total_monthly_bill = 0.0
        self.gui.update_monthly_bill(total_monthly_bill)

    def set_threshold(self):
        """
        Handle setting the maximum monthly bill threshold by balancing appliance usage.
        """
        max_monthly_bill = self.gui.get_threshold()
        adjusted_appliances, adjustments = self.appliance_balancer.balance_appliances(
            self.appliances,
            self.daily_costs,
            max_monthly_bill,
            self.valid_indices
        )

        # Update appliances with adjusted values
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
            self.gui.populate_table(self.appliances, self.daily_costs)

            # Update monthly bill display
            total_monthly_bill, _ = self.bill_calculator.calculate_monthly_bill(self.daily_costs)
            self.gui.update_monthly_bill(total_monthly_bill)

        # Show adjustments in a dialog
        dialog = AdjustmentDialog(adjustments, self.appliances, self.gui)
        dialog.exec_()

    def run(self):
        """
        Run the application.
        """
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = EnergyCostPredictorApp()
    app.run()