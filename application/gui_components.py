from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QMessageBox, QTextEdit, QScrollArea, QGroupBox, QDialog, QApplication, QSpinBox, QTimeEdit, QFormLayout, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTime
from PyQt5.QtGui import QFont
import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class UsageGraphDialog(QDialog):
    def __init__(self, weekly_data, dates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weekly Usage Patterns")
        self.setFixedSize(800, 600)
        self.weekly_data = weekly_data
        self.dates = dates

        self.appliances = sorted(set(item["Device Type"] for item in weekly_data))
        self.current_appliance_index = 0

        self.layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.toggle_button = QPushButton("Next Appliance")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #547792, stop:1 #426b82);
                color: #ECEFCA;
                border: none;
                padding: 8px 16px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
                font-family: Roboto, Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #94B4C1, stop:1 #547792);
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_appliance)

        self.ok_button = QPushButton("OK")
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #547792, stop:1 #426b82);
                color: #ECEFCA;
                border: none;
                padding: 8px 16px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
                font-family: Roboto, Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #94B4C1, stop:1 #547792);
            }
        """)
        self.ok_button.clicked.connect(self.accept)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.toggle_button)
        button_layout.addWidget(self.ok_button)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.update_graph()

    def toggle_appliance(self):
        self.current_appliance_index = (self.current_appliance_index + 1) % len(self.appliances)
        self.update_graph()

    def update_graph(self):
        self.ax.clear()
        current_appliance = self.appliances[self.current_appliance_index]
        usage_data = [0.0] * len(self.dates)
        hours = [0] * len(self.dates)

        for i, date in enumerate(self.dates):
            daily_data = [item for item in self.weekly_data if item["Date"] == date]
            for item in daily_data:
                if item["Device Type"] == current_appliance and item["On/Off Status"] == "On":
                    turn_on = item["Turn On Time"]
                    if turn_on != "N/A":
                        hour = int(turn_on.split(":")[0])
                        hours[i] = hour
                        usage_data[i] = item["Usage Duration (minutes)"]
                    break

        x = np.arange(len(self.dates))
        self.ax.plot(x, usage_data, label=current_appliance, marker='o', color='b')
        self.ax.set_xlabel("Day of the Week")
        self.ax.set_ylabel("Usage Duration (minutes)")
        self.ax.set_title(f"Weekly Usage Pattern - {current_appliance} ({self.dates[0]} to {self.dates[-1]})")
        self.ax.set_xticks(x)
        self.ax.set_xticklabels([date.split('-')[2] for date in self.dates])
        self.ax.legend()
        self.ax.grid(True)
        self.canvas.draw()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #94B4C1;
                color: #ECEFCA;
                font-family: Roboto, Arial;
                border: 1px solid #213448;
                border-radius: 10px;
            }
            QLabel {
                font-size: 14pt;
                color: #ECEFCA;
            }
            QGroupBox {
                font-size: 16pt;
                font-weight: bold;
                color: #ECEFCA;
                border: 1px solid #547792;
                border-radius: 8px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
            QSpinBox, QTimeEdit {
                background-color: #547792;
                color: #ECEFCA;
                border: 1px solid #213448;
                border-radius: 5px;
                padding: 5px;
                font-size: 12pt;
                min-width: 100px;
            }
            QTimeEdit {
                min-width: 120px;
            }
            QSpinBox::up-button, QSpinBox::down-button,
            QTimeEdit::up-button, QTimeEdit::down-button {
                background-color: #426b82;
                border: none;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {
                background-color: #94B4C1;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow,
            QTimeEdit::up-arrow, QTimeEdit::down-arrow {
                width: 10px;
                height: 10px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #547792, stop:1 #426b82);
                color: #ECEFCA;
                border: none;
                padding: 10px 20px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
                font-family: Roboto, Arial;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #94B4C1, stop:1 #547792);
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        temp_group = QGroupBox("Temperature Thresholds")
        temp_group.setStyleSheet("""
            QGroupBox {
                font-size: 16pt;
                font-weight: bold;
                color: #ECEFCA;
                border: 1px solid #547792;
                border-radius: 8px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        temp_form = QFormLayout()
        temp_form.setLabelAlignment(Qt.AlignRight)
        temp_form.setSpacing(15)

        self.ac_temp_spinbox = QSpinBox()
        self.ac_temp_spinbox.setRange(0, 50)
        self.ac_temp_spinbox.setValue(25)
        self.ac_temp_spinbox.setSuffix(" °C")
        temp_form.addRow("AC Turn-On (Above):", self.ac_temp_spinbox)

        self.heater_temp_spinbox = QSpinBox()
        self.heater_temp_spinbox.setRange(-10, 30)
        self.heater_temp_spinbox.setValue(18)
        self.heater_temp_spinbox.setSuffix(" °C")
        temp_form.addRow("Heater Turn-On (Below):", self.heater_temp_spinbox)

        temp_group.setLayout(temp_form)
        layout.addWidget(temp_group)

        time_group = QGroupBox("Turn-On Before Home (Minutes)")
        time_group.setStyleSheet("""
            QGroupBox {
                font-size: 16pt;
                font-weight: bold;
                color: #ECEFCA;
                border: 1px solid #547792;
                border-radius: 8px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        time_form = QFormLayout()
        time_form.setLabelAlignment(Qt.AlignRight)
        time_form.setSpacing(15)

        self.turn_on_before = {}
        selected_appliances = ["Air Conditioner", "Heater", "Water Heater", "Dehumidifier"]
        for appliance in selected_appliances:
            spinbox = QSpinBox()
            spinbox.setRange(0, 120)
            spinbox.setValue(30)
            self.turn_on_before[appliance] = spinbox
            time_form.addRow(f"{appliance}:", spinbox)

        time_group.setLayout(time_form)
        layout.addWidget(time_group)

        turn_off_group = QGroupBox("Turn-Off Settings")
        turn_off_group.setStyleSheet("""
            QGroupBox {
                font-size: 16pt;
                font-weight: bold;
                color: #ECEFCA;
                border: 1px solid #547792;
                border-radius: 8px;
                margin-top: 20px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
            }
        """)
        turn_off_form = QFormLayout()
        turn_off_form.setLabelAlignment(Qt.AlignRight)
        turn_off_form.setSpacing(15)

        self.turn_off_period = QSpinBox()
        self.turn_off_period.setRange(10, 240)
        self.turn_off_period.setValue(60)
        turn_off_form.addRow("Turn-Off Period When Away (Minutes):", self.turn_off_period)

        self.grace_period = QSpinBox()
        self.grace_period.setRange(5, 60)
        self.grace_period.setValue(15)
        turn_off_form.addRow("Grace Period After Return Time (Minutes):", self.grace_period)

        turn_off_group.setLayout(turn_off_form)
        layout.addWidget(turn_off_group)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch(1)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        button_layout.addStretch(1)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_settings(self):
        settings = {
            "ac_temp_threshold": self.ac_temp_spinbox.value(),
            "heater_temp_threshold": self.heater_temp_spinbox.value(),
            "turn_on_before": {appliance: spinbox.value() for appliance, spinbox in self.turn_on_before.items()},
            "turn_off_period": self.turn_off_period.value(),
            "grace_period": self.grace_period.value()
        }
        return settings

class EnergyCostPredictorGUI(QWidget):
    profile_changed = pyqtSignal(str)
    bill_update_requested = pyqtSignal(list)
    check_model_update = pyqtSignal()
    open_settings = pyqtSignal()
    toggle_owner_home = pyqtSignal()
    save_return_time = pyqtSignal()

    def __init__(self, load_dataset_callback):
        super().__init__()
        self.load_dataset_callback = load_dataset_callback
        self.weekly_data = []
        self.dates = []
        self.current_day_index = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Smart Home Energy Cost Predictor")
        
        screen = QApplication.primaryScreen().availableGeometry()
        self.setFixedHeight(1200)
        self.setFixedWidth(screen.width())
        
        self.move(0, (screen.height() - 1200) // 2)

        font = QFont("Roboto", 11)
        if not font.exactMatch():
            font = QFont("Arial", 11)

        blue_theme = """
            QWidget {
                background-color: #94B4C1;
                color: #ECEFCA;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #547792, stop:1 #426b82);
                color: #ECEFCA;
                border: none;
                padding: 12px 20px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 10px;
                font-family: Roboto, Arial;
                box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2);
                margin: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #94B4C1, stop:1 #547792);
            }
            QPushButton#prev_button, QPushButton#next_button {
                padding: 8px;
                font-size: 12pt;
            }
            QPushButton#save_return_time_button, QPushButton#simulate_button {
                padding: 4px 8px;
                font-size: 10pt;
                margin: 2px;
            }
            #monthly_bill_label, #location_label, #temp_label, #humidity_label, #date_label {
                background-color: #213448;
                color: #ECEFCA;
                font-size: 11pt;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #213448;
                border-radius: 6px;
                font-family: Roboto, Arial;
            }
            QTextEdit {
                background-color: #547792;
                border: 1px solid #547792;
                border-radius: 8px;
                padding: 6px;
                font-family: Roboto, Arial;
                font-size: 10pt;
                margin: 10px;
            }
            #profile_info {
                color: #ECEFCA;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #547792;
                color: #ECEFCA;
                border: 1px solid #547792;
                gridline-color: #213448;
                font-size: 10pt;
                font-family: Roboto, Arial;
                alternate-background-color: #547792;
            }
            QTableWidget:disabled {
                background-color: #547792;
                color: #ECEFCA;
                border: 1px solid #547792;
            }
            QTableWidget::item {
                padding: 4px;
                color: #ECEFCA;
                border: 1px solid #213448;
            }
            QTableWidget::item:disabled {
                color: #ECEFCA;
                border: 1px solid #213448;
            }
            QHeaderView::section {
                background-color: #547792;
                color: #ECEFCA;
                padding: 6px;
                border: none;
                font-size: 10pt;
                font-family: Roboto, Arial;
            }
            QHeaderView::section:disabled {
                background-color: #547792;
                color: #ECEFCA;
            }
            QTableCornerButton::section {
                background-color: #547792;
                border: 1px solid #547792;
            }
            QScrollArea {
                background-color: #547792;
                border: 1px solid #547792;
            }
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #ECEFCA;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }
            QGroupBox#owner_status_group {
                font-size: 10pt;
            }
            QGroupBox#owner_status_group QLabel {
                font-size: 10pt;
            }
            QCheckBox {
                font-size: 10pt;
                color: #ECEFCA;
            }
            QTimeEdit#return_time_edit {
                min-width: 80px;
                font-size: 10pt;
            }
            #ac_label, #heater_label, #dehumidifier_label, #water_heater_label {
                color: #000000;
                font-size: 11pt;
                font-family: Roboto, Arial;
                padding: 4px;
            }
        """
        self.setStyleSheet(blue_theme)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(30)
        main_layout.setContentsMargins(40, 40, 40, 40)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch(1)

        load_button = QPushButton("Load Appliances")
        load_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not load_button.font().exactMatch():
            load_button.setFont(QFont("Arial", 12, QFont.Bold))
        load_button.setCursor(Qt.PointingHandCursor)
        load_button.clicked.connect(self.load_dataset_callback)
        button_layout.addWidget(load_button)

        self.prev_button = QPushButton("◄")
        self.prev_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not self.prev_button.font().exactMatch():
            self.prev_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.prev_button.setFixedWidth(40)
        self.prev_button.clicked.connect(self.prev_day)
        button_layout.addWidget(self.prev_button)

        self.date_label = QLabel("Date: N/A")
        self.date_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.date_label.font().exactMatch():
            self.date_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.date_label.setObjectName("date_label")
        button_layout.addWidget(self.date_label)

        self.next_button = QPushButton("►")
        self.next_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not self.next_button.font().exactMatch():
            self.next_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.next_button.setFixedWidth(40)
        self.next_button.clicked.connect(self.next_day)
        button_layout.addWidget(self.next_button)

        self.graph_button = QPushButton("Show Usage Graph")
        self.graph_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not self.graph_button.font().exactMatch():
            self.graph_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.graph_button.clicked.connect(self.show_usage_graph)
        button_layout.addWidget(self.graph_button)

        self.update_model_button = QPushButton("Check for Model Update")
        self.update_model_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not self.update_model_button.font().exactMatch():
            self.update_model_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.update_model_button.setCursor(Qt.PointingHandCursor)
        self.update_model_button.clicked.connect(self.check_model_update)
        button_layout.addWidget(self.update_model_button)

        self.settings_button = QPushButton("Settings ⚙️")
        self.settings_button.setFont(QFont("Roboto", 12, QFont.Bold))
        if not self.settings_button.font().exactMatch():
            self.settings_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_button)

        button_layout.addStretch(1)
        main_layout.addLayout(button_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Device Type", "Power (W)", "Room", "Temp (°C)", "Humidity (%)",
            "Duration (min)", "Status", "Turn On Time", "Usage Adjusted"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setCornerButtonEnabled(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setEnabled(False)
        self.table.verticalHeader().setDefaultSectionSize(32)
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 160)
        self.table.setColumnWidth(6, 120)
        self.table.setColumnWidth(7, 140)
        self.table.setColumnWidth(8, 120)
        self.table.setAlternatingRowColors(True)

        scroll_area = QScrollArea()
        scroll_area.setFixedHeight(400)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.table)
        main_layout.addWidget(scroll_area)

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

        # Combined layout for weather, appliance recommendations, and owner status
        weather_appliance_owner_layout = QHBoxLayout()
        weather_appliance_owner_layout.setSpacing(20)
        weather_appliance_owner_layout.addStretch(1)

        # Weather vertical layout
        weather_vertical_layout = QVBoxLayout()
        weather_vertical_layout.setSpacing(5)

        self.location_label = QLabel("🌍 Location: N/A")
        self.location_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.location_label.font().exactMatch():
            self.location_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.location_label.setObjectName("location_label")
        weather_vertical_layout.addWidget(self.location_label)

        self.temp_label = QLabel("🌡️ Temperature: N/A")
        self.temp_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.temp_label.font().exactMatch():
            self.temp_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.temp_label.setObjectName("temp_label")
        weather_vertical_layout.addWidget(self.temp_label)

        self.humidity_label = QLabel("💧 Humidity: N/A")
        self.humidity_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.humidity_label.font().exactMatch():
            self.humidity_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.humidity_label.setObjectName("humidity_label")
        weather_vertical_layout.addWidget(self.humidity_label)

        weather_appliance_owner_layout.addLayout(weather_vertical_layout, 1)

        # Appliance recommendations
        self.appliance_group = QGroupBox("Appliance Recommendations")
        appliance_layout = QVBoxLayout()
        appliance_layout.setSpacing(5)

        self.ac_label = QLabel("<b>AC:</b> N/A")
        self.ac_label.setFont(QFont("Roboto", 11))
        if not self.ac_label.font().exactMatch():
            self.ac_label.setFont(QFont("Arial", 11))
        self.ac_label.setObjectName("ac_label")
        appliance_layout.addWidget(self.ac_label)

        self.heater_label = QLabel("<b>Heater:</b> N/A")
        self.heater_label.setFont(QFont("Roboto", 11))
        if not self.heater_label.font().exactMatch():
            self.heater_label.setFont(QFont("Arial", 11))
        self.heater_label.setObjectName("heater_label")
        appliance_layout.addWidget(self.heater_label)

        self.dehumidifier_label = QLabel("<b>Dehumidifier:</b> N/A")
        self.dehumidifier_label.setFont(QFont("Roboto", 11))
        if not self.dehumidifier_label.font().exactMatch():
            self.dehumidifier_label.setFont(QFont("Arial", 11))
        self.dehumidifier_label.setObjectName("dehumidifier_label")
        appliance_layout.addWidget(self.dehumidifier_label)

        self.water_heater_label = QLabel("<b>Water Heater:</b> Scheduled")
        self.water_heater_label.setFont(QFont("Roboto", 11))
        if not self.water_heater_label.font().exactMatch():
            self.water_heater_label.setFont(QFont("Arial", 11))
        self.water_heater_label.setObjectName("water_heater_label")
        appliance_layout.addWidget(self.water_heater_label)

        self.appliance_group.setLayout(appliance_layout)
        weather_appliance_owner_layout.addWidget(self.appliance_group, 1)

        # Compact Owner Status Section
        owner_status_group = QGroupBox("Owner Status")
        owner_status_group.setObjectName("owner_status_group")
        owner_status_layout = QFormLayout()
        owner_status_layout.setLabelAlignment(Qt.AlignRight)
        owner_status_layout.setSpacing(5)  # Reduced spacing

        self.enable_return_time_checkbox = QCheckBox("Enable")
        self.enable_return_time_checkbox.setChecked(True)

        self.expected_return_time_edit = QTimeEdit()
        self.expected_return_time_edit.setDisplayFormat("HH:mm")
        self.expected_return_time_edit.setTime(QTime.currentTime().addSecs(3600))
        self.expected_return_time_edit.setEnabled(True)
        self.expected_return_time_edit.setObjectName("return_time_edit")

        self.save_return_time_button = QPushButton("Save")
        self.save_return_time_button.setObjectName("save_return_time_button")
        self.save_return_time_button.clicked.connect(self.save_return_time.emit)

        return_time_layout = QHBoxLayout()
        return_time_layout.addWidget(self.expected_return_time_edit)
        return_time_layout.addWidget(self.save_return_time_button)

        self.owner_status_label = QLabel("Time left: N/A")
        self.owner_status_label.setFont(QFont("Arial", 10))

        self.simulate_button = QPushButton("Simulate")
        self.simulate_button.setObjectName("simulate_button")
        self.simulate_button.clicked.connect(self.toggle_owner_home.emit)

        owner_status_layout.addRow("", self.enable_return_time_checkbox)
        owner_status_layout.addRow("Return:", return_time_layout)
        owner_status_layout.addRow("Status:", self.owner_status_label)
        owner_status_layout.addRow("", self.simulate_button)

        owner_status_group.setLayout(owner_status_layout)
        weather_appliance_owner_layout.addWidget(owner_status_group, 1)

        weather_appliance_owner_layout.addStretch(1)
        main_layout.addLayout(weather_appliance_owner_layout)

        self.profile_info = QTextEdit()
        self.profile_info.setObjectName("profile_info")
        self.profile_info.setReadOnly(True)
        self.profile_info.setFixedHeight(120)
        self.profile_info.setText("Select a profile to view usage time limits.")
        main_layout.addWidget(self.profile_info)

        self.monthly_bill_label = QLabel("Predicted Monthly Bill: $0.00")
        self.monthly_bill_label.setFont(QFont("Roboto", 11, QFont.Bold))
        if not self.monthly_bill_label.font().exactMatch():
            self.monthly_bill_label.setFont(QFont("Arial", 11, QFont.Bold))
        self.monthly_bill_label.setAlignment(Qt.AlignCenter)
        self.monthly_bill_label.setObjectName("monthly_bill_label")
        main_layout.addWidget(self.monthly_bill_label, alignment=Qt.AlignCenter)

        main_layout.addStretch(1)
        self.setLayout(main_layout)
        logging.debug("GUI components initialized with full-width and 1200px height layout, with settings button")

    def update_weather(self, location, temperature, humidity, settings=None):
        if location is not None:
            self.location_label.setText(f"🌍 Location: {location}")
        else:
            self.location_label.setText("🌍 Location: N/A")

        if temperature is not None:
            self.temp_label.setText(f"🌡️ Temperature: {temperature:.1f}°C")
            if settings:
                ac_temp_threshold = settings.get("ac_temp_threshold", 25.0)
                heater_temp_threshold = settings.get("heater_temp_threshold", 18.0)
                ac_state = "On" if temperature > ac_temp_threshold else "Off"
                heater_state = "On" if temperature < heater_temp_threshold else "Off"
                self.ac_label.setText(f"<b>AC:</b> {ac_state} (Above {ac_temp_threshold}°C)")
                self.heater_label.setText(f"<b>Heater:</b> {heater_state} (Below {heater_temp_threshold}°C)")
            else:
                ac_state = "On" if temperature > 25.0 else "Off"
                heater_state = "On" if temperature < 18.0 else "Off"
                self.ac_label.setText(f"<b>AC:</b> {ac_state}")
                self.heater_label.setText(f"<b>Heater:</b> {heater_state}")
        else:
            self.temp_label.setText("🌡️ Temperature: N/A")
            self.ac_label.setText("<b>AC:</b> N/A")
            self.heater_label.setText(f"<b>Heater:</b> N/A")

        if humidity is not None:
            self.humidity_label.setText(f"💧 Humidity: {humidity:.0f}%")
            dehumidifier_state = "On" if humidity > 60.0 else "Off"
            self.dehumidifier_label.setText(f"<b>Dehumidifier:</b> {dehumidifier_state}")
        else:
            self.humidity_label.setText("💧 Humidity: N/A")
            self.dehumidifier_label.setText("<b>Dehumidifier:</b> N/A")

        self.water_heater_label.setText("<b>Water Heater:</b> Scheduled")

        logging.debug(f"Updated weather display: location={location}, temp={temperature}, humidity={humidity}")

    def populate_dropdowns(self, device_options, room_options):
        logging.debug("Dropdowns populated with device and room options (no-op)")

    def set_weekly_data(self, appliances):
        self.weekly_data = appliances
        self.dates = sorted(list(set(item["Date"] for item in appliances)))
        self.current_day_index = 0
        if self.dates:
            self.update_day_display()

    def update_day_display(self):
        if not self.dates:
            return
        current_date = self.dates[self.current_day_index]
        self.date_label.setText(f"Date: {current_date}")
        daily_data = [item for item in self.weekly_data if item["Date"] == current_date]
        self.populate_table(daily_data)

        self.bill_update_requested.emit(daily_data)

        self.prev_button.setEnabled(self.current_day_index > 0)
        self.next_button.setEnabled(self.current_day_index < len(self.dates) - 1)

    def prev_day(self):
        if self.current_day_index > 0:
            self.current_day_index -= 1
            self.update_day_display()

    def next_day(self):
        if self.current_day_index < len(self.dates) - 1:
            self.current_day_index += 1
            self.update_day_display()

    def show_usage_graph(self):
        if not self.dates:
            QMessageBox.warning(self, "Warning", "No data loaded.")
            return
        dialog = UsageGraphDialog(self.weekly_data, self.dates, self)
        dialog.exec_()

    def populate_table(self, appliances, daily_costs=None, adjusted_indices=None):
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
            self.table.setItem(row, 7, QTableWidgetItem(appliance["Turn On Time"]))
            usage_adjusted = "Yes" if row in adjusted_indices else "No"
            self.table.setItem(row, 8, QTableWidgetItem(usage_adjusted))

        logging.debug(f"Table populated with {len(appliances)} appliances")

    def update_monthly_bill(self, monthly_bill):
        self.monthly_bill_label.setText(f"Predicted Monthly Bill: ${monthly_bill:.2f}")
        logging.debug(f"Updated monthly bill display: ${monthly_bill:.2f}")