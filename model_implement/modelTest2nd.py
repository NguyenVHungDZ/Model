import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import joblib
import numpy as np
import pandas as pd

# Load model and encoders
model = joblib.load("gb_model.pkl")
device_encoder = joblib.load("device_encoder.pkl")
room_encoder = joblib.load("room_encoder.pkl")
scaler = joblib.load("scaler.pkl")

# Preprocessing function
def preprocess_input(device_type, power, room, temp, humidity, duration, status):
    try:
        print("DEBUG VALUES:")
        print(f"device_type={device_type}, power={power}, room={room}, temp={temp}, humidity={humidity}, duration={duration}, status={status}")
        
        device_encoded = device_encoder.transform([device_type])[0]
        room_encoded = room_encoder.transform([room])[0]
        status_binary = 1 if status.lower() == 'on' else 0

        # These must match the column names used during training exactly
        feature_columns = [
            "Device Type", 
            "Power Consumption (W)", 
            "Room Location", 
            "Temperature (°C)", 
            "Humidity (%)", 
            "Usage Duration (minutes)", 
            "On/Off Status"
        ]
        # change font size of feature columns

        features_df = pd.DataFrame([[
            device_encoded,
            float(power),
            room_encoded,
            float(temp),
            float(humidity),
            float(duration),
            status_binary
        ]], columns=feature_columns)

        scaled_features = scaler.transform(features_df)
        return scaled_features
    except Exception as e:
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", f"Invalid input: {e}")
        return None


# Prediction function
def predict():
    data = preprocess_input(
        device_type_var.currentText(),
        power_var.text(),
        room_var.currentText(),
        temp_var.text(),
        humidity_var.text(),
        duration_var.text(),
        status_var.currentText()
    )

    if data is not None:
        prediction = model.predict(data)
        result_label.setText(f"Predicted Energy Cost: ${round(prediction[0], 2)}")
    else:
        result_label.setText("Invalid input. Please check your entries.")

# Initialize app
app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Smart Home Energy Cost Predictor")
window.setFixedSize(600, 640)

# Font
font = QFont("Segoe UI", 11)

# Dark theme stylesheet
dark_theme = """
    QWidget { background-color: #2e2e2e; color: #eee; }
    QComboBox, QLineEdit {
        background-color: #3c3c3c; color: #eee;
        border: 1px solid #666; border-radius: 6px; padding: 6px 10px;
    }
    QPushButton {
        background-color: #00e676; color: #111;
        border: none; padding: 10px 18px;
        font-size: 12pt; font-weight: bold;
        border-radius: 8px;
    }
    QPushButton:hover { background-color: #00c853; }
    #result_label {
        color: #ddd; font-size: 14pt; font-weight: bold;
        padding: 12px; border: 1px dashed #888;
        border-radius: 8px; background-color: #444;
    }
"""

# Apply dark theme
app.setStyleSheet(dark_theme)

# Layouts
main_layout = QVBoxLayout()
main_layout.setSpacing(15)
main_layout.setContentsMargins(20, 20, 20, 20)

# Form layout
form_layout = QFormLayout()
form_layout.setSpacing(12)

   
# Dropdown and field options
device_options = list(device_encoder.classes_)
room_options = list(room_encoder.classes_)
status_options = ["On", "Off"]

device_type_var = QComboBox(); device_type_var.addItems(device_options); device_type_var.setFont(font)
power_var = QLineEdit(); power_var.setFont(font)
room_var = QComboBox(); room_var.addItems(room_options); room_var.setFont(font)
temp_var = QLineEdit(); temp_var.setFont(font)
humidity_var = QLineEdit(); humidity_var.setFont(font)
duration_var = QLineEdit(); duration_var.setFont(font)
status_var = QComboBox(); status_var.addItems(status_options); status_var.setFont(font)

form_layout.addRow("Device Type", device_type_var)
form_layout.addRow("Power Consumption (W)", power_var)
form_layout.addRow("Room Location", room_var)
form_layout.addRow("Temperature (°C)", temp_var)
form_layout.addRow("Humidity (%)", humidity_var)
form_layout.addRow("Usage Duration (minutes)", duration_var)
form_layout.addRow("On/Off Status", status_var)

# Increase label font size for all form labels
label_font = QFont("Segoe UI", 11)  # You can make it larger if needed
for i in range(form_layout.rowCount()):
    label_item = form_layout.itemAt(i, QFormLayout.LabelRole)
    if label_item:
        label = label_item.widget()
        if label:
            label.setFont(label_font)

main_layout.addLayout(form_layout)

# Predict button
predict_button = QPushButton("Predict Energy Cost")
predict_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
predict_button.setCursor(Qt.PointingHandCursor)
predict_button.clicked.connect(predict)
main_layout.addWidget(predict_button)

# Result label
result_label = QLabel("Predicted Energy Cost: $0.00")
result_label.setFont(QFont("Arial", 14, QFont.Bold))
result_label.setAlignment(Qt.AlignCenter)
result_label.setObjectName("result_label")
main_layout.addWidget(result_label)

# Apply layout and show window
window.setLayout(main_layout)
window.show()
sys.exit(app.exec_())
