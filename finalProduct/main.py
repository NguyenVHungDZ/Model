import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QMessageBox
from model_loader import ModelLoader
from data_processor import DataProcessor
from gui_components import GUIComponents
from mock_data_loader import MockDataLoader
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class EnergyBillPredictorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home Energy Bill Predictor")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        logging.debug("Central widget set")

        # Log the directory of data_processor.py being imported
        import data_processor
        logging.debug(f"data_processor module loaded from: {data_processor.__file__}")

        # Initialize model loader
        self.model_loader = ModelLoader()
        success, message = self.model_loader.load_model()
        if not success:
            QMessageBox.critical(self, "Error", message)
            sys.exit(1)

        # Initialize data processor
        self.data_processor = DataProcessor(self.model_loader.rf_model, 
                                           self.model_loader.le_device, 
                                           self.model_loader.le_room)

        # Initialize mock data loader
        self.data_loader = MockDataLoader(self)
        self.appliances = []

        # Initialize GUI components
        self.gui = GUIComponents(self.central_widget, self.add_input_row, self.load_dataset)
        self.gui.calculate_button.clicked.connect(self.calculate)
        logging.debug("GUI components initialized")

    def add_input_row(self):
        self.gui.add_input_row()

    def load_dataset(self):
        appliances = self.data_loader.load_dataset()
        if appliances:
            self.appliances = appliances
            self.gui.load_dataset()

    def calculate(self):
        # Get input array from GUI
        self.appliances = self.gui.get_input_array()

        if not self.appliances:
            QMessageBox.warning(self, "Warning", "Please add at least one valid appliance with positive usage and power.")
            return

        self.data_processor.predict_costs(self.appliances)
        self.data_processor.apply_threshold(self.appliances, self.gui.threshold_spin.value())
        self.gui.update_table(self.appliances)
        self.gui.update_visualizations(self.appliances)
        self.gui.update_summary(self.appliances)
        logging.debug("Calculation completed")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnergyBillPredictorGUI()
    window.show()
    logging.debug("Application started")
    sys.exit(app.exec_())