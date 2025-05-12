from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QDoubleSpinBox, QMessageBox, QTextEdit, QTimeEdit, QCheckBox, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtGui import QFont
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class EnergyCostPredictorGUI(QWidget):
    profile_changed = pyqtSignal(str)  # Signal for profile changes
    time_settings_changed = pyqtSignal(str, bool, bool)  # Signal for arrival time and appliance settings

    def __init__(self, set_threshold_callback, load_dataset_callback, automator):
        """
        Initialize the EnergyCostPredictorGUI with a 1400px-wide layout, blue-cream theme, and automation features.

        Args:
            set_threshold_callback (callable): Callback function to set the monthly bill threshold.
            load_dataset_callback (callable): Callback function to load a dataset.
            automator (SmartAutomator): Instance for automation features.
        """
        super().__init__()
        self.set_threshold_callback = set_threshold_callback
        self.load_dataset_callback = load_dataset_callback
        self.automator = automator
        self.init_ui()

    def init_ui(self):
        """
        Set up the GUI components with a 1400px-wide layout for appliance properties, including Usage Adjusted column.
        """
        self.setWindowTitle("Smart Home Energy Cost Predictor")
        self.setFixedSize(640, 480)  # Window width 1400px, height 950px

        # Modern font (Roboto preferred, Arial as fallback)
        font = QFont("Roboto", 11)
        if not font.exactMatch():
            font = QFont("Arial", 11)

        # Blue-cream-themed modern stylesheet with corner button and disabled table styling
        blue_theme = """
            QWidget {
                background-color: #94B4C1; /* Light blue-gray background */
                color: #ECEFCA; /* Light cream text for non-label elements */
            }
            QDoubleSpinBox, QTimeEdit {
                background-color: #547792; /* Medium blue */
                color: #ECEFCA;
                border: 1px solid #547792; /* Medium blue border */
                border-radius: 8px;
                padding: 6px 10px;
                font-family: Roboto, Arial;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QTimeEdit::up-button, QTimeEdit::down-button {
                background-color: #547792; /* Medium blue buttons */
                border-radius: 4px;
            }
            QCheckBox {
                color: #ECEFCA;
                font-family: Roboto, Arial;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #213448; /* Dark blue-gray button */
                color: #ECEFCA;
                border: none;
                padding: 12px 20px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 10px;
                font-family: Roboto, Arial;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2); /* Subtle shadow */
                margin: 10px; /* Add margin around buttons */
            }
            QPushButton:hover {
                background-color: #547792; /* Medium blue on hover */
            }
            #monthly_bill_label {
                color: #ECEFCA;
                font-size: 11pt; /* Larger font size */
                font-weight: bold;
                padding: 6px; /* Larger padding */
                border: 1px solid #213448;
                border-radius: 6px;
                background-color: #213448; /* Dark blue-gray accent */
                font-family: Roboto, Arial;
            }
            QTextEdit {
                background-color: #547792; /* Medium blue */
                border: 1px solid #547792;
                border-radius: 8px;
                padding: 6px;
                font-family: Roboto, Arial;
                font-size: 10pt;
                margin: 10px; /* Add margin around text edit */
            }
            #profile_info {
                color: #ECEFCA; /* Light cream text */
                font-weight: bold; /* Slightly bold text */
            }
            QTableWidget {
                background-color: #547792; /* Medium blue table */
                color: #ECEFCA;
                border: 1px solid #547792;
                gridline-color: #213448; /* Dark blue-gray gridlines */
                font-size: 10pt;
                font-family: Roboto, Arial;
                alternate-background-color: #547792; /* Medium blue for alternating rows */
            }
            QTableWidget:disabled {
                background-color: #547792; /* Maintain blue theme when disabled */
                color: #ECEFCA;
                border: 1px solid #547792;
            }
            QTableWidget::item {
                padding: 4px;
                color: #ECEFCA;
                border: 1px solid #213448; /* Add border to cells */
            }
            QTableWidget::item:disabled {
                color: #ECEFCA; /* Maintain text color when disabled */
                border: 1px solid #213448; /* Keep border when disabled */
            }
            QHeaderView::section {
                background-color: #547792; /* Medium blue header */
                color: #ECEFCA; /* Light cream text */
                padding: 6px;
                border: none;
                font-size: 10pt;
                font-family: Roboto, Arial;
            }
            QHeaderView::section:disabled {
                background-color: #547792; /* Maintain header color when disabled */
                color: #ECEFCA;
            }
            QTableCornerButton::section {
                background-color: #547792; /* Match table background */
                border: 1px solid #547792;
            }
            QFrame {
                color: #547792; /* Medium blue line for separator */
            }
            QScrollArea {
                background-color: #547792; /* Match table background */
                border: 1px solid #547792;
            }
            QLabel {
                color: #000000; /* Black text for contrast on #94B4C1 */
                font-family: Roboto, Arial;
                font-size: 11pt;
                font-weight: demi; /* Semi-bold */
            }
        """
        self.setStyleSheet(blue_theme)

        # Main layout with spacious margins
        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)  # Increased spacing for better separation
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Load Appliances button
        load_button = QPushButton("Load Appliances")
        load_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not load_button.font().exactMatch():
            load_button.setFont(QFont("Arial", 12, QFont.Bold))
        load_button.setCursor(Qt.PointingHandCursor)
        load_button.clicked.connect(self.load_dataset_callback)
        main_layout.addWidget(load_button, alignment=Qt.AlignCenter)

        # Table to display appliances (9 columns, including Usage Adjusted)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Device Type", "Power (W)", "Room", "Temp (°C)", "Humidity (%)",
            "Duration (min)", "Status", "Daily Cost ($)", "Usage Adjusted"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)  # Ensure vertical scrolling as fallback
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrollbar
        self.table.setCornerButtonEnabled(False)  # Hide the corner button
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Disable editing
        self.table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection
        self.table.setFocusPolicy(Qt.NoFocus)  # Prevent focus
        self.table.setEnabled(False)  # Disable all interactions
        self.table.verticalHeader().setDefaultSectionSize(32)  # Set row height to 32px
        self.table.setColumnWidth(0, 250)  # Device Type
        self.table.setColumnWidth(1, 140)  # Power (W)
        self.table.setColumnWidth(2, 180)  # Room
        self.table.setColumnWidth(3, 140)  # Temp (°C)
        self.table.setColumnWidth(4, 140)  # Humidity (%)
        self.table.setColumnWidth(5, 160)  # Duration (min)
        self.table.setColumnWidth(6, 120)  # Status
        self.table.setColumnWidth(7, 140)  # Daily Cost ($)
        self.table.setColumnWidth(8, 120)  # Usage Adjusted
        self.table.setAlternatingRowColors(True)

        # Wrap table in QScrollArea for reliable scrolling
        scroll_area = QScrollArea()
        scroll_area.setFixedHeight(400)  # Height for ~10 rows: 10 rows * 32px + 30px header + 50px buffer
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)
        main_layout.addWidget(scroll_area)

        # Profile buttons
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(10)
        profile_layout.setAlignment(Qt.AlignCenter)

        eco_button = QPushButton("Eco")
        eco_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not eco_button.font().exactMatch():
            eco_button.setFont(QFont("Arial", 12, QFont.Bold))
        eco_button.setCursor(Qt.PointingHandCursor)
        eco_button.clicked.connect(lambda: self.profile_changed.emit("Eco"))
        profile_layout.addWidget(eco_button)

        balanced_button = QPushButton("Balanced")
        balanced_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not balanced_button.font().exactMatch():
            balanced_button.setFont(QFont("Arial", 12, QFont.Bold))
        balanced_button.setCursor(Qt.PointingHandCursor)
        balanced_button.clicked.connect(lambda: self.profile_changed.emit("Balanced"))
        profile_layout.addWidget(balanced_button)

        comfort_button = QPushButton("Comfort")
        comfort_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not comfort_button.font().exactMatch():
            comfort_button.setFont(QFont("Arial", 12, QFont.Bold))
        comfort_button.setCursor(Qt.PointingHandCursor)
        comfort_button.clicked.connect(lambda: self.profile_changed.emit("Comfort"))
        profile_layout.addWidget(comfort_button)

        normal_button = QPushButton("Normal")
        normal_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not normal_button.font().exactMatch():
            normal_button.setFont(QFont("Arial", 12, QFont.Bold))
        normal_button.setCursor(Qt.PointingHandCursor)
        normal_button.clicked.connect(lambda: self.profile_changed.emit("Normal"))
        profile_layout.addWidget(normal_button)

        main_layout.addLayout(profile_layout)

        # Profile information display
        self.profile_info = QTextEdit()
        self.profile_info.setObjectName("profile_info")  # Set object name for specific styling
        self.profile_info.setReadOnly(True)
        self.profile_info.setFixedHeight(120)  # Reduced height to make room for larger table
        self.profile_info.setText("Select a profile to view usage time limits.")
        main_layout.addWidget(self.profile_info)

        # Monthly bill display (compact)
        self.monthly_bill_label = QLabel("Predicted Monthly Bill: $0.00")
        self.monthly_bill_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.monthly_bill_label.font().exactMatch():
            self.monthly_bill_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.monthly_bill_label.setAlignment(Qt.AlignCenter)
        self.monthly_bill_label.setObjectName("monthly_bill_label")
        main_layout.addWidget(self.monthly_bill_label, alignment=Qt.AlignCenter)

        # Combined settings layout for threshold and time settings
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(40)  # Increased spacing for better separation
        settings_layout.setAlignment(Qt.AlignCenter)

        # Threshold input and button
        threshold_layout = QHBoxLayout()
        threshold_layout.setSpacing(15)
        threshold_layout.setAlignment(Qt.AlignCenter)

        threshold_label = QLabel("Max Monthly Bill ($):")
        threshold_label.setFont(font)
        threshold_layout.addWidget(threshold_label)

        self.threshold_var = QDoubleSpinBox()
        self.threshold_var.setRange(0, 10000)
        self.threshold_var.setSingleStep(10)
        self.threshold_var.setFont(font)
        self.threshold_var.setStyleSheet("min-width: 120px;")  # Reduced width to fit alongside time settings
        threshold_layout.addWidget(self.threshold_var)

        set_threshold_button = QPushButton("Set Threshold")
        set_threshold_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not set_threshold_button.font().exactMatch():
            set_threshold_button.setFont(QFont("Arial", 12, QFont.Bold))
        set_threshold_button.setCursor(Qt.PointingHandCursor)
        set_threshold_button.clicked.connect(self.set_threshold_callback)
        threshold_layout.addWidget(set_threshold_button)

        settings_layout.addLayout(threshold_layout)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        settings_layout.addWidget(separator)

        # Time input and appliance activation settings
        time_layout = QHBoxLayout()
        time_layout.setSpacing(15)
        time_layout.setAlignment(Qt.AlignCenter)

        time_label = QLabel("Arrival Time:")
        time_label.setFont(font)
        time_layout.addWidget(time_label)

        self.arrival_time = QTimeEdit()
        self.arrival_time.setFont(font)
        self.arrival_time.setTime(QTime(18, 0))  # Default to 6:00 PM
        self.arrival_time.setDisplayFormat("HH:mm")
        self.arrival_time.timeChanged.connect(self.update_time_settings)
        time_layout.addWidget(self.arrival_time)

        self.heater_check = QCheckBox("Turn on Heater")
        self.heater_check.setFont(font)
        self.heater_check.stateChanged.connect(self.update_time_settings)
        time_layout.addWidget(self.heater_check)

        self.water_heater_check = QCheckBox("Turn on Water Heater")
        self.water_heater_check.setFont(font)
        self.water_heater_check.stateChanged.connect(self.update_time_settings)
        time_layout.addWidget(self.water_heater_check)

        settings_layout.addLayout(time_layout)

        main_layout.addLayout(settings_layout)

        # Automation controls
        automation_layout = QVBoxLayout()
        automation_label = QLabel("Automation Controls")
        automation_layout.addWidget(automation_label)

        # Button to suggest automation rules
        suggest_rules_btn = QPushButton("Suggest Automation Rules")
        suggest_rules_btn.clicked.connect(self.suggest_rules)
        automation_layout.addWidget(suggest_rules_btn)

        # Button to simulate automation impact
        simulate_impact_btn = QPushButton("Simulate Automation Impact")
        simulate_impact_btn.clicked.connect(self.simulate_impact)
        automation_layout.addWidget(simulate_impact_btn)

        # Text area to display suggestions
        self.suggestions_text = QTextEdit()
        self.suggestions_text.setReadOnly(True)
        automation_layout.addWidget(self.suggestions_text)

        main_layout.addLayout(automation_layout)

        # Add stretch for clean spacing
        main_layout.addStretch(1)

        # Apply layout
        self.setLayout(main_layout)
        logging.debug("GUI components initialized with 1400px-wide layout and blue-cream theme, with Usage Adjusted column")

    def suggest_rules(self):
        """Display suggested automation rules."""
        rules = self.automator.suggest_automation_rules()
        suggestions = "\n".join([f"{rule['action']} when {rule['condition']} ({rule['time_range']})" for rule in rules])
        self.suggestions_text.setText(suggestions)
        logging.debug("Automation rules suggested")

    def simulate_impact(self):
        """Simulate the impact of automation rules and display the result."""
        rules = self.automator.suggest_automation_rules()
        savings = self.automator.simulate_automation_impact(rules, self.automator.analyzer.csv_path)
        QMessageBox.information(self, "Simulation Result", f"Estimated energy savings: {savings} kWh")
        logging.debug(f"Simulated automation impact: {savings} kWh saved")

    def update_time_settings(self):
        """
        Emit the time_settings_changed signal with the current arrival time and appliance settings.
        """
        time_str = self.arrival_time.time().toString("HH:mm")
        heater_on = self.heater_check.isChecked()
        water_heater_on = self.water_heater_check.isChecked()
        self.time_settings_changed.emit(time_str, heater_on, water_heater_on)
        logging.debug(f"Time settings updated: Arrival {time_str}, Heater {heater_on}, Water Heater {water_heater_on}")

    def populate_dropdowns(self, device_options, room_options):
        """
        Placeholder for dropdown population (kept for compatibility).

        Args:
            device_options (list): List of device types.
            room_options (list): List of room locations.
        """
        logging.debug("Dropdowns populated with device and room options (no-op)")

    def populate_table(self, appliances, daily_costs=None, adjusted_indices=None):
        """
        Populate the table with appliance data, predicted daily costs, and usage adjustment status.

        Args:
            appliances (list): List of appliance dictionaries.
            daily_costs (list, optional): Predicted daily costs for each appliance.
            adjusted_indices (list, optional): Indices of appliances with adjusted usage times.
        """
        adjusted_indices = adjusted_indices or []
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
            adjusted_cost = cost / 100
            self.table.setItem(row, 7, QTableWidgetItem(f"{adjusted_cost:.2f}"))
            usage_adjusted = "Yes" if row in adjusted_indices else "No"
            self.table.setItem(row, 8, QTableWidgetItem(usage_adjusted))

        logging.debug(f"Table populated with {len(appliances)} appliances")

    def update_monthly_bill(self, monthly_bill):
        """
        Update the monthly bill display.

        Args:
            monthly_bill (float): Total predicted monthly bill.
        """
        adjusted_monthly_bill = monthly_bill / 100
        self.monthly_bill_label.setText(f"Predicted Monthly Bill: ${adjusted_monthly_bill:.2f}")
        logging.debug(f"Updated monthly bill display: ${adjusted_monthly_bill:.2f}")

    def get_threshold(self):
        """
        Retrieve the threshold value from the GUI.

        Returns:
            float: Maximum monthly bill threshold.
        """
        return self.threshold_var.value()