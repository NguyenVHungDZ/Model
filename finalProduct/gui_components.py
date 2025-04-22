import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QDoubleSpinBox, QPushButton, QTableWidget, QTableWidgetItem, 
                             QFrame, QScrollArea, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GUIComponents:
    def __init__(self, central_widget, add_row_callback, load_dataset_callback):
        self.central_widget = central_widget
        self.add_row_callback = add_row_callback
        self.load_dataset_callback = load_dataset_callback
        self.input_rows = []
        self.device_types = ['Heater', 'Air Conditioner', 'Microwave', 'Washing Machine', 'Smart Plug', 'Smart Bulb', 
                             'Laptop Charger', 'TV', 'Ceiling Fan', 'Refrigerator']
        self.setup_ui()
        logging.debug("GUIComponents initialized")

    def setup_ui(self):
        # Main layout on central widget
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        logging.debug("Main layout created")

        # Styling
        self.central_widget.setStyleSheet("""
            QWidget {
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
        self.input_scroll = QScrollArea()
        self.input_scroll.setWidgetResizable(True)
        self.input_scroll.setWidget(input_container)
        self.input_layout = QVBoxLayout(input_container)
        self.input_layout.setSpacing(15)
        self.input_layout.setContentsMargins(10, 10, 10, 10)
        logging.debug("Input scroll area created")

        # Add initial input row
        self.add_input_row()

        self.main_layout.addWidget(self.input_scroll)

        # Load Dataset, Threshold, and Calculate frame
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setSpacing(15)

        load_button = QPushButton("Load Dataset")
        load_button.clicked.connect(self.load_dataset)
        load_button.setStyleSheet("min-width: 150px;")
        control_layout.addWidget(load_button)

        control_layout.addWidget(QLabel("Max Monthly Bill ($):"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0, 10000)
        self.threshold_spin.setSingleStep(10)
        self.threshold_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        control_layout.addWidget(self.threshold_spin)

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setStyleSheet("min-width: 150px;")
        control_layout.addWidget(self.calculate_button)

        self.status_label = QLabel("Status: Waiting for model")
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        self.main_layout.addWidget(control_frame)
        logging.debug("Control frame added")

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
        self.main_layout.addWidget(self.table)
        logging.debug("Table created")

        # Visualizations
        viz_frame = QFrame()
        viz_layout = QHBoxLayout(viz_frame)
        viz_layout.setContentsMargins(0, 0, 0, 0)

        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.canvas = FigureCanvas(self.fig)
        viz_layout.addWidget(self.canvas)

        self.main_layout.addWidget(viz_frame)
        logging.debug("Visualization frame added")

        # Summary
        self.summary_label = QLabel("Summary: No appliances added")
        self.summary_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.summary_label.setWordWrap(True)
        self.main_layout.addWidget(self.summary_label)
        logging.debug("Summary label added")

    def add_input_row(self, device_type="", usage=0.0, power=0.0):
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
        if device_type:
            device_combo.setCurrentText(device_type)
        input_layout.addWidget(device_combo)

        usage_label = QLabel("Daily Usage (h):")
        usage_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        input_layout.addWidget(usage_label)

        usage_spin = QDoubleSpinBox()
        usage_spin.setRange(0, 24)
        usage_spin.setSingleStep(0.1)
        usage_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        usage_spin.setValue(usage)
        input_layout.addWidget(usage_spin)

        power_label = QLabel("Power (W):")
        power_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        input_layout.addWidget(power_label)

        power_spin = QDoubleSpinBox()
        power_spin.setRange(0, 5000)
        power_spin.setSingleStep(10)
        power_spin.setStyleSheet("min-width: 150px; font-size: 16px;")
        power_spin.setValue(power)
        input_layout.addWidget(power_spin)

        add_button = QPushButton("+")
        add_button.setFixedSize(50, 50)
        add_button.setStyleSheet("""
            background-color: #4CAF50;
            border-radius: 25px;
            font-size: 20px;
            font-weight: bold;
        """)
        add_button.clicked.connect(self.add_row_callback)
        input_layout.addWidget(add_button)

        self.input_rows.append({
            'frame': input_frame,
            'device_combo': device_combo,
            'usage_spin': usage_spin,
            'power_spin': power_spin
        })
        self.input_layout.addWidget(input_frame)
        logging.debug(f"Input row added: {device_type}, {usage} h, {power} W")

    def load_dataset(self):
        appliances = self.load_dataset_callback()
        if not appliances:
            QMessageBox.warning(self.central_widget, "Warning", "Failed to load dataset. Please select a valid JSON file.")
            return

        # Clear existing rows
        for row in self.input_rows:
            self.input_layout.removeWidget(row['frame'])
            row['frame'].deleteLater()
        self.input_rows = []
        logging.debug("Cleared existing input rows")

        # Add rows from loaded dataset
        for appliance in appliances:
            self.add_input_row(appliance['device_type'], appliance['daily_usage_hours'], appliance['power_watts'])

    def get_input_array(self):
        input_array = []
        for row in self.input_rows:
            device = row['device_combo'].currentText()
            usage = row['usage_spin'].value()
            power = row['power_spin'].value()
            if device and usage > 0 and power > 0:
                input_array.append({
                    'device_type': device,
                    'daily_usage_hours': usage,
                    'power_watts': power,
                    'predicted_cost': 0.0,
                    'adjusted_usage_hours': usage,
                    'adjusted_power_watts': power,
                    'adjusted_cost': 0.0,
                    'action': ''
                })
        logging.debug(f"Input array created with {len(input_array)} appliances")
        return input_array

    def update_table(self, appliances):
        self.table.setRowCount(len(appliances))
        for row, appliance in enumerate(appliances):
            self.table.setItem(row, 0, QTableWidgetItem(appliance['device_type']))
            self.table.setItem(row, 1, QTableWidgetItem(f"{appliance['daily_usage_hours']:.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(f"{appliance['power_watts']:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"{appliance['predicted_cost']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"{appliance['adjusted_usage_hours']:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"{appliance['adjusted_power_watts']:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{appliance['adjusted_cost']:.2f}"))
            self.table.setItem(row, 7, QTableWidgetItem(appliance['action']))
        logging.debug("Table updated with %d appliances", len(appliances))

    def update_visualizations(self, appliances):
        self.ax1.clear()
        self.ax2.clear()

        df_plot = pd.DataFrame(appliances)
        if df_plot.shape[0] > 0:
            # Plot 1: Predicted vs Adjusted Costs
            df_melt = pd.melt(df_plot, id_vars=['device_type'], value_vars=['predicted_cost', 'adjusted_cost'], 
                              var_name='Cost Type', value_name='Cost')
            sns.barplot(x='device_type', y='Cost', hue='Cost Type', palette='viridis', ax=self.ax1)
            self.ax1.set_title('Predicted vs Adjusted Monthly Cost')
            self.ax1.tick_params(axis='x', rotation=45)

            # Plot 2: Cost Distribution
            sns.histplot(df_plot['predicted_cost'], color='blue', label='Predicted', alpha=0.5, ax=self.ax2)
            sns.histplot(df_plot['adjusted_cost'], color='green', label='Adjusted', alpha=0.5, ax=self.ax2)
            self.ax2.set_title('Cost Distribution')
            self.ax2.set_xlabel('Monthly Cost ($)')
            self.ax2.legend()

        self.fig.tight_layout()
        self.canvas.draw()
        logging.debug("Visualizations updated")

    def update_summary(self, appliances):
        total_predicted = sum(a['predicted_cost'] for a in appliances)
        total_adjusted = sum(a['adjusted_cost'] for a in appliances)
        savings = total_predicted - total_adjusted
        top_devices = sorted(appliances, key=lambda x: x['predicted_cost'], reverse=True)[:3]
        top_devices_str = "; ".join([f"{a['device_type']}: ${a['predicted_cost']:.2f} → ${a['adjusted_cost']:.2f}" for a in top_devices])
        summary = (
            f"Predicted Monthly Bill: ${total_predicted:.2f}\n"
            f"Adjusted Monthly Bill: ${total_adjusted:.2f}\n"
            f"Savings: ${savings:.2f}\n\n"
            f"Top Appliances: {top_devices_str}\n\n"
            f"Adjustments reduce usage (up to 50%) and power (up to 20%) for high-cost appliances to meet the threshold."
        )
        self.summary_label.setText(summary)
        logging.debug("Summary updated")