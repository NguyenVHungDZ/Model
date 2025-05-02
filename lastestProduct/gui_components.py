from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QMessageBox, QAbstractButton
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class EnergyCostPredictorGUI(QWidget):
    # Signal to emit when a delete button is clicked, passing the row index
    delete_row_signal = pyqtSignal(int)

    def __init__(self, add_appliance_callback, set_threshold_callback, load_dataset_callback, delete_row_callback):
        """
        Initialize the EnergyCostPredictorGUI.

        Args:
            add_appliance_callback (callable): Callback function to add an appliance to the list.
            set_threshold_callback (callable): Callback function to set the monthly bill threshold.
            load_dataset_callback (callable): Callback function to load a dataset.
            delete_row_callback (callable): Callback function to delete a specific row.
        """
        super().__init__()
        self.add_appliance_callback = add_appliance_callback
        self.set_threshold_callback = set_threshold_callback
        self.load_dataset_callback = load_dataset_callback
        self.delete_row_callback = delete_row_callback
        self.init_ui()

    def init_ui(self):
        """
        Set up the GUI components and layout.
        """
        # Increase window width to 1200px to accommodate all columns comfortably
        self.setWindowTitle("Smart Home Energy Cost Predictor")
        self.setFixedSize(1200, 800)

        # Font
        font = QFont("Segoe UI", 11)

        # Dark theme stylesheet with updated table colors
        dark_theme = """
            QWidget { background-color: #2e2e2e; color: #ffffff; }
            QComboBox, QLineEdit, QDoubleSpinBox {
                background-color: #3c3c3c; color: #ffffff;
                border: 1px solid #666; border-radius: 6px; padding: 6px 10px;
            }
            QComboBox {
                min-width: 200px;  /* Increased width to prevent text truncation */
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #00e676; color: #111;
                border: none; padding: 10px 18px;
                font-size: 12pt; font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #00c853; }
            #monthly_bill_label {
                color: #ffffff; font-size: 12pt; font-weight: bold;
                padding: 8px; border: 1px solid #888;
                border-radius: 8px; background-color: #444;
            }
            QTableWidget {
                background-color: #333333; /* Dark gray background */
                color: #BBDEFB; /* Light blue text for contrast */
                border: 1px solid #666; 
                gridline-color: #444; /* Slightly lighter gridlines */
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 4px;
                color: #BBDEFB; /* Light blue text for all items */
            }
            QTableWidget::item:selected {
                background-color: #4CAF50; /* Selection matches button color */
                color: #BBDEFB; /* Keep text color consistent */
            }
            QHeaderView::section {
                background-color: #4CAF50; /* Header matches button color */
                color: #ffffff;
                padding: 6px; 
                border: none; 
                font-size: 10pt;
            }
            QPushButton#deleteButton {
                background-color: #FF5252; /* Red for delete */
                color: #ffffff;
                border: none;
                padding: 5px;
                font-size: 10pt;
                border-radius: 4px;
            }
            QPushButton#deleteButton:hover {
                background-color: #D32F2F; /* Darker red on hover */
            }
        """
        self.setStyleSheet(dark_theme)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Form layout for manual input
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # Dropdown and field options (to be populated later)
        self.device_type_var = QComboBox()
        self.device_type_var.setFont(font)
        self.power_var = QLineEdit()
        self.power_var.setFont(font)
        self.power_var.setStyleSheet("min-width: 200px;")  # Match width for consistency
        self.room_var = QComboBox()
        self.room_var.setFont(font)
        self.temp_var = QLineEdit()
        self.temp_var.setFont(font)
        self.temp_var.setStyleSheet("min-width: 200px;")
        self.humidity_var = QLineEdit()
        self.humidity_var.setFont(font)
        self.humidity_var.setStyleSheet("min-width: 200px;")
        self.duration_var = QLineEdit()
        self.duration_var.setFont(font)
        self.duration_var.setStyleSheet("min-width: 200px;")
        self.status_var = QComboBox()
        self.status_var.addItems(["On", "Off"])
        self.status_var.setFont(font)
        self.status_var.setStyleSheet("min-width: 200px;")

        form_layout.addRow("Device Type", self.device_type_var)
        form_layout.addRow("Power Consumption (W)", self.power_var)
        form_layout.addRow("Room Location", self.room_var)
        form_layout.addRow("Temperature (°C)", self.temp_var)
        form_layout.addRow("Humidity (%)", self.humidity_var)
        form_layout.addRow("Usage Duration (minutes)", self.duration_var)
        form_layout.addRow("On/Off Status", self.status_var)

        # Increase label font size for all form labels
        label_font = QFont("Segoe UI", 11)
        for i in range(form_layout.rowCount()):
            label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item:
                label = label_item.widget()
                if label:
                    label.setFont(label_font)

        main_layout.addLayout(form_layout)

        # Add Appliance button
        add_button = QPushButton("Add Appliance")
        add_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        add_button.setCursor(Qt.PointingHandCursor)
        add_button.clicked.connect(self.add_appliance_callback)
        main_layout.addWidget(add_button)

        # Load Dataset button
        load_button = QPushButton("Load Dataset")
        load_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        load_button.setCursor(Qt.PointingHandCursor)
        load_button.clicked.connect(self.load_dataset_callback)
        main_layout.addWidget(load_button)

        # Table to display appliances
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # Includes the Delete button column
        self.table.setHorizontalHeaderLabels([
            "Device Type", "Power (W)", "Room", "Temp (°C)", "Humidity (%)",
            "Duration (min)", "Status", "Daily Cost ($)", "Action"
        ])
        # Calculate height for 5 rows plus header
        # Approximate row height: 30px per row, header height: ~30px
        # Total height = (5 rows * 30px) + header (30px) + small buffer = 180px
        self.table.setFixedHeight(180)
        self.table.horizontalHeader().setStretchLastSection(True)
        # Enable vertical scrolling
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Adjust column widths to ensure all properties are fully visible
        self.table.setColumnWidth(0, 200)  # Device Type (e.g., "Air Conditioner")
        self.table.setColumnWidth(1, 120)  # Power (W) (e.g., "1500.30")
        self.table.setColumnWidth(2, 150)  # Room (e.g., "Living Room")
        self.table.setColumnWidth(3, 120)  # Temp (°C) (e.g., "26.70")
        self.table.setColumnWidth(4, 120)  # Humidity (%) (e.g., "70.20")
        self.table.setColumnWidth(5, 150)  # Duration (min) (e.g., "1440.00")
        self.table.setColumnWidth(6, 100)  # Status (e.g., "On")
        self.table.setColumnWidth(7, 120)  # Daily Cost ($) (e.g., "$200.10")
        self.table.setColumnWidth(8, 100)  # Action (Delete button)
        self.table.setAlternatingRowColors(False)  # Disable alternating colors since we're setting a uniform color
        main_layout.addWidget(self.table)

        # Monthly bill display
        self.monthly_bill_label = QLabel("Predicted Monthly Bill: $0.00")
        self.monthly_bill_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.monthly_bill_label.setAlignment(Qt.AlignCenter)
        self.monthly_bill_label.setObjectName("monthly_bill_label")
        main_layout.addWidget(self.monthly_bill_label)

        # Threshold input and button
        threshold_layout = QHBoxLayout()
        threshold_layout.setSpacing(10)

        threshold_label = QLabel("Max Monthly Bill ($):")
        threshold_label.setFont(font)
        threshold_layout.addWidget(threshold_label)

        self.threshold_var = QDoubleSpinBox()
        self.threshold_var.setRange(0, 10000)
        self.threshold_var.setSingleStep(10)
        self.threshold_var.setFont(font)
        self.threshold_var.setStyleSheet("min-width: 150px;")
        threshold_layout.addWidget(self.threshold_var)

        set_threshold_button = QPushButton("Set Threshold")
        set_threshold_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        set_threshold_button.setCursor(Qt.PointingHandCursor)
        set_threshold_button.clicked.connect(self.set_threshold_callback)
        threshold_layout.addWidget(set_threshold_button)

        main_layout.addLayout(threshold_layout)

        # Apply layout
        self.setLayout(main_layout)
        logging.debug("GUI components initialized")

    def populate_dropdowns(self, device_options, room_options):
        """
        Populate dropdowns with device and room options.

        Args:
            device_options (list): List of device types.
            room_options (list): List of room locations.
        """
        self.device_type_var.addItems(device_options)
        self.room_var.addItems(room_options)
        logging.debug("Dropdowns populated with device and room options")

    def populate_table(self, appliances, daily_costs=None):
        """
        Populate the table with appliance data, predicted daily costs, and delete buttons.

        Args:
            appliances (list): List of appliance dictionaries.
            daily_costs (list, optional): Predicted daily costs for each appliance.
        """
        self.table.setRowCount(len(appliances))
        for row, appliance in enumerate(appliances):
            self.table.setItem(row, 0, QTableWidgetItem(appliance["Device Type"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"{appliance['Power Consumption (W)']:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(appliance["Room Location"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"{appliance['Temperature (°C)']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{appliance['Humidity (%)']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{appliance['Usage Duration (minutes)']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(appliance["On/Off Status"]))
            cost = daily_costs[row] if daily_costs is not None else 0.0
            # Divide the daily cost by 100 to correct for display
            adjusted_cost = cost / 100
            self.table.setItem(row, 7, QTableWidgetItem(f"{adjusted_cost:.2f}"))

            # Add Delete button for each row
            delete_button = QPushButton("Delete")
            delete_button.setObjectName("deleteButton")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_row_signal.emit(r))
            self.table.setCellWidget(row, 8, delete_button)

        logging.debug(f"Table populated with {len(appliances)} appliances")

    def update_monthly_bill(self, monthly_bill):
        """
        Update the monthly bill display.

        Args:
            monthly_bill (float): Total predicted monthly bill.
        """
        # Divide the monthly bill by 100 to match the adjusted daily costs
        adjusted_monthly_bill = monthly_bill / 100
        self.monthly_bill_label.setText(f"Predicted Monthly Bill: ${adjusted_monthly_bill:.2f}")
        logging.debug(f"Updated monthly bill display: ${adjusted_monthly_bill:.2f}")

    def get_input_values(self):
        """
        Retrieve input values from the GUI for adding an appliance.

        Returns:
            dict: Dictionary containing input values.
        """
        return {
            "Device Type": self.device_type_var.currentText(),
            "Power Consumption (W)": self.power_var.text(),
            "Room Location": self.room_var.currentText(),
            "Temperature (°C)": self.temp_var.text(),
            "Humidity (%)": self.humidity_var.text(),
            "Usage Duration (minutes)": self.duration_var.text(),
            "On/Off Status": self.status_var.currentText()
        }

    def get_threshold(self):
        """
        Retrieve the threshold value from the GUI.

        Returns:
            float: Maximum monthly bill threshold.
        """
        return self.threshold_var.value()

    def clear_form(self):
        """
        Clear the input form fields after adding an appliance.
        """
        self.power_var.clear()
        self.temp_var.clear()
        self.humidity_var.clear()
        self.duration_var.clear()
        logging.debug("Cleared input form fields")