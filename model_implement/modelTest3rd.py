import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from sklearn.preprocessing import LabelEncoder, StandardScaler
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QComboBox, QDoubleSpinBox, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QFrame, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import sys
import os

class EnergyBillPredictorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Home Energy Bill Predictor")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize variables
        self.rf_model = None
        self.le_device = LabelEncoder()
        self.le_room = LabelEncoder()
        self.appliances = []
        self.device_types = ['Heater', 'Air Conditioner', 'Microwave', 'Washing Machine', 'Smart Plug', 'Smart Bulb', 
                             'Laptop Charger', 'TV', 'Ceiling Fan', 'Refrigerator']
        self.room_types = ['Living Room', 'Bedroom', 'Kitchen', 'Bathroom', 'Garage', 'Office']
        self.le_device.fit(self.device_types)
        self.le_room.fit(self.room_types)
        self.input_rows = []

        # Setup UI
        self.setup_ui()

        # Load model
        self.load_model()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E2E2E;
            }
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
            }
            QComboBox, QDoubleSpinBox {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #4CAF50;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QTableWidget {
                background-color: #3C3C3C;
                color: #FFFFFF;
                border: 1px solid #555555;
                gridline-color: #555555;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                font-size: 14px;
            }
            QScrollArea {
                background-color: #2E2E2E;
                border: none;
            }
            QFrame.input-row {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3C3C3C, stop:1 #4CAF50);
                border: 2px solid #555555;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        # Input frame (scrollable)
        input_container = QFrame()
        input_scroll = QScrollArea()
        input_scroll.setWidgetResizable(True)
        input_scroll.setWidget(input_container)
        self.input_layout = QVBoxLayout(input_container)
        self.input_layout.setSpacing(15)
        self.input_layout.setContentsMargins(10, 10, 10, 10)

        # Add initial input row
        self.add_input_row()

        main_layout.addWidget(input_scroll)

        # Threshold and Calculate frame
        threshold_frame = QFrame()
        threshold_layout = QHBoxLayout(threshold_frame)
        threshold_layout.setSpacing(15)

        threshold_layout.addWidget(QLabel("Max Monthly Bill ($):"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setSingleStep(10)
        self.threshold_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        threshold_layout.addWidget(self.threshold_spin)

        calculate_button = QPushButton("Calculate")
        calculate_button.clicked.connect(self.calculate)
        calculate_button.setStyleSheet("min-width: 150px;")
        threshold_layout.addWidget(calculate_button)

        self.status_label = QLabel("Status: Waiting for model")
        threshold_layout.addWidget(self.status_label)
        threshold_layout.addStretch()

        main_layout.addWidget(threshold_frame)

        # Table
        self.table = QTableWidget()
        self.table.setRowCount(0)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Device Type", "Daily Usage (h)", "Power (W)", "Monthly Cost ($)",
            "Adj. Usage (h)", "Adj. Power (W)", "Adj. Cost ($)", "Action"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        main_layout.addWidget(self.table)

        # Visualizations
        viz_frame = QFrame()
        viz_layout = QHBoxLayout(viz_frame)
        viz_layout.setContentsMargins(0, 0, 0, 0)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        viz_layout.addWidget(self.canvas)

        main_layout.addWidget(viz_frame)

        # Summary
        self.summary_label = QLabel("Summary: No appliances added")
        self.summary_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.summary_label.setWordWrap(True)
        main_layout.addWidget(self.summary_label)

    def add_input_row(self):
        input_frame = QFrame()
        input_frame.setObjectName("input-row")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setSpacing(20)
        input_layout.setContentsMargins(15, 15, 15, 15)

        device_label = QLabel("Device Type:")
        device_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        input_layout.addWidget(device_label)

        device_combo = QComboBox()
        device_combo.addItems(self.device_types)
        device_combo.setStyleSheet("min-width: 200px; font-size: 16px;")
        input_layout.addWidget(device_combo)

        usage_label = QLabel("Daily Usage (h):")
        usage_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        input_layout.addWidget(usage_label)

        usage_spin = QDoubleSpinBox()
        usage_spin.setRange(0, 24)
        usage_spin.setSingleStep(0.1)
        usage_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        input_layout.addWidget(usage_spin)

        power_label = QLabel("Power (W):")
        power_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        input_layout.addWidget(power_label)

        power_spin = QDoubleSpinBox()
        power_spin.setRange(0, 5000)
        power_spin.setSingleStep(10)
        power_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        input_layout.addWidget(power_spin)

        add_button = QPushButton("+")
        add_button.setFixedSize(50, 50)
        add_button.setStyleSheet("""
            background-color: #4CAF50;
            border-radius: 25px;
            font-size: 20px;
            font-weight: bold;
        """)
        add_button.clicked.connect(self.add_input_row)
        input_layout.addWidget(add_button)

        self.input_rows.append({
            'frame': input_frame,
            'device_combo': device_combo,
            'usage_spin': usage_spin,
            'power_spin': power_spin
        })
        self.input_layout.addWidget(input_frame)

    def load_model(self):
        model_path = './.pkl/rf_model.pkl'
        try:
            self.rf_model = joblib.load(model_path)
            self.status_label.setText("Status: Model loaded successfully")
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", 
                                 f"Model file '{model_path}' not found in {os.path.join(os.getcwd(), '.pkl')}. "
                                 "Ensure 'rf_model.pkl' is in the .pkl folder.")
            self.status_label.setText("Status: Failed to load model")

    def calculate(self):
        self.appliances = []
        for row in self.input_rows:
            device = row['device_combo'].currentText()
            usage = row['usage_spin'].value()
            power = row['power_spin'].value()

            if device and usage > 0 and power > 0:
                self.appliances.append({
                    'Device Type': device,
                    'Daily Usage (h)': usage,
                    'Power Consumption (W)': power,
                    'Adjusted Usage (h)': usage,
                    'Adjusted Power (W)': power,
                    'Predicted Cost ($)': 0.0,
                    'Adjusted Cost ($)': 0.0,
                    'Action': ''
                })

        if not self.appliances:
            QMessageBox.warning(self, "Warning", "Please add at least one valid appliance with positive usage and power.")
            return

        self.predict_costs()
        self.apply_threshold()
        self.update_table()
        self.update_visualizations()
        self.update_summary()

    def predict_costs(self):
        if not self.appliances or self.rf_model is None:
            return

        # Create DataFrame for predictions
        data = []
        for appliance in self.appliances:
            data.append({
                'Device Type': self.le_device.transform([appliance['Device Type']])[0],
                'Power Consumption (W)': appliance['Power Consumption (W)'],
                'Room Location': self.le_room.transform(['Living Room'])[0],
                'Temperature (°C)': 22.0,
                'Humidity (%)': 55.0,
                'Usage Duration (minutes)': appliance['Daily Usage (h)'] * 60,
                'On/Off Status': 1
            })
        df = pd.DataFrame(data)

        # Scale features
        scaler = StandardScaler()
        df_scaled = pd.DataFrame(scaler.fit_transform(df), columns=df.columns)

        # Predict daily cost
        daily_costs = self.rf_model.predict(df_scaled)

        # Update appliances with monthly costs (30 days)
        self.daily_costs = daily_costs
        for i, appliance in enumerate(self.appliances):
            appliance['Predicted Cost ($)'] = daily_costs[i] * 30
            appliance['Adjusted Cost ($)'] = appliance['Predicted Cost ($)']
            appliance['Action'] = ''

    def apply_threshold(self):
        threshold = self.threshold_spin.value()
        if threshold <= 0:
            return

        # Calculate current total adjusted cost
        total_cost = sum(appliance['Adjusted Cost ($)'] for appliance in self.appliances)

        if total_cost <= threshold:
            return

        # Sort appliances by adjusted cost
        sorted_appliances = sorted(self.appliances, key=lambda x: x['Adjusted Cost ($)'], reverse=True)
        high_cost_devices = ['Heater', 'Air Conditioner', 'Microwave', 'Washing Machine']

        # Adjust usage time first, then power
        for appliance in sorted_appliances:
            if total_cost <= threshold:
                break
            if appliance['Device Type'] not in high_cost_devices:
                continue

            # Reduce usage time (up to 50%)
            current_usage = appliance['Adjusted Usage (h)']
            max_reduction = current_usage * 0.5
            reduction_needed = (total_cost - threshold) / 30 / (appliance['Adjusted Cost ($)'] / 30 / current_usage)
            usage_reduction = min(max_reduction, reduction_needed)
            if usage_reduction > 0:
                appliance['Adjusted Usage (h)'] = current_usage - usage_reduction
                appliance['Action'] = f"Reduced usage by {(usage_reduction/current_usage)*100:.1f}%"
                # Recalculate cost
                data = [{
                    'Device Type': self.le_device.transform([appliance['Device Type']])[0],
                    'Power Consumption (W)': appliance['Adjusted Power (W)'],
                    'Room Location': self.le_room.transform(['Living Room'])[0],
                    'Temperature (°C)': 22.0,
                    'Humidity (%)': 55.0,
                    'Usage Duration (minutes)': appliance['Adjusted Usage (h)'] * 60,
                    'On/Off Status': 1
                }]
                df = pd.DataFrame(data)
                df_scaled = pd.DataFrame(scaler.transform(df), columns=df.columns)
                appliance['Adjusted Cost ($)'] = self.rf_model.predict(df_scaled)[0] * 30
                total_cost = sum(a['Adjusted Cost ($)'] for a in self.appliances)

            # Reduce power (up to 20%) if still over threshold
            if total_cost > threshold:
                current_power = appliance['Adjusted Power (W)']
                max_power_reduction = current_power * 0.2
                power_reduction = min(max_power_reduction, (total_cost - threshold) / 30 / (appliance['Adjusted Cost ($)'] / 30 / current_power))
                if power_reduction > 0:
                    appliance['Adjusted Power (W)'] = current_power - power_reduction
                    appliance['Action'] += f"; Reduced power by {(power_reduction/current_power)*100:.1f}%"
                    # Recalculate cost
                    data = [{
                        'Device Type': self.le_device.transform([appliance['Device Type']])[0],
                        'Power Consumption (W)': appliance['Adjusted Power (W)'],
                        'Room Location': self.le_room.transform(['Living Room'])[0],
                        'Temperature (°C)': 22.0,
                        'Humidity (%)': 55.0,
                        'Usage Duration (minutes)': appliance['Adjusted Usage (h)'] * 60,
                        'On/Off Status': 1
                    }]
                    df = pd.DataFrame(data)
                    df_scaled = pd.DataFrame(scaler.transform(df), columns=df.columns)
                    appliance['Adjusted Cost ($)'] = self.rf_model.predict(df_scaled)[0] * 30
                    total_cost = sum(a['Adjusted Cost ($)'] for a in self.appliances)

    def update_table(self):
        self.table.setRowCount(len(self.appliances))
        for row, appliance in enumerate(self.appliances):
            self.table.setItem(row, 0, QTableWidgetItem(appliance['Device Type']))
            self.table.setItem(row, 1, QTableWidgetItem(f"{appliance['Daily Usage (h)']:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{appliance['Power Consumption (W)']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{appliance['Predicted Cost ($)']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{appliance['Adjusted Usage (h)']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{appliance['Adjusted Power (W)']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{appliance['Adjusted Cost ($)']:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(appliance['Action']))

    def update_visualizations(self):
        self.ax1.clear()
        self.ax2.clear()

        df_plot = pd.DataFrame(self.appliances)
        if df_plot.shape[0] > 0:
            # Plot 1: Predicted vs Adjusted Costs
            df_melt = pd.melt(df_plot, id_vars=['Device Type'], value_vars=['Predicted Cost ($)', 'Adjusted Cost ($)'], 
                              var_name='Cost Type', value_name='Cost')
            sns.barplot(x='Device Type', y='Cost', hue='Cost Type', palette='viridis', ax=self.ax1)
            self.ax1.set_title('Predicted vs Adjusted Monthly Cost')
            self.ax1.tick_params(axis='x', rotation=45)

            # Plot 2: Cost Distribution
            sns.histplot(df_plot['Predicted Cost ($)'], color='blue', label='Predicted', alpha=0.5, ax=self.ax2)
            sns.histplot(df_plot['Adjusted Cost ($)'], color='green', label='Adjusted', alpha=0.5, ax=self.ax2)
            self.ax2.set_title('Cost Distribution')
            self.ax2.set_xlabel('Monthly Cost ($)')
            self.ax2.legend()

        self.fig.tight_layout()
        self.canvas.draw()

    def update_summary(self):
        total_predicted = sum(a['Predicted Cost ($)'] for a in self.appliances)
        total_adjusted = sum(a['Adjusted Cost ($)'] for a in self.appliances)
        savings = total_predicted - total_adjusted
        top_devices = sorted(self.appliances, key=lambda x: x['Predicted Cost ($)'], reverse=True)[:3]
        top_devices_str = "; ".join([f"{a['Device Type']}: ${a['Predicted Cost ($)']:.2f} → ${a['Adjusted Cost ($)']:.2f}" for a in top_devices])
        summary = (
            f"Predicted Monthly Bill: ${total_predicted:.2f}\n"
            f"Adjusted Monthly Bill: ${total_adjusted:.2f}\n"
            f"Savings: ${savings:.2f}\n\n"
            f"Top Appliances: {top_devices_str}\n\n"
            f"Adjustments reduce usage (up to 50%) and power (up to 20%) for high-cost appliances to meet the threshold."
        )
        self.summary_label.setText(summary)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnergyBillPredictorGUI()
    window.show()
    sys.exit(app.exec_())