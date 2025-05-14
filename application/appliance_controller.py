import json
import requests
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import Qt
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ApplianceControlDialog(QDialog):
    def __init__(self, commands, parent=None):
        """
        Initialize the ApplianceControlDialog to display control commands.

        Args:
            commands (list): List of command dictionaries {device, action, time}.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Appliance Control Commands")
        self.setFixedSize(400, 300)
        self.init_ui(commands)

    def init_ui(self, commands):
        """
        Set up the dialog UI.

        Args:
            commands (list): List of command dictionaries {device, action, time}.
        """
        layout = QVBoxLayout()

        # Text area to display commands
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet("""
            QTextEdit {
                background-color: #547792;
                color: #ECEFCA;
                border: 1px solid #213448;
                border-radius: 6px;
                padding: 6px;
                font-family: Roboto, Arial;
                font-size: 10pt;
            }
        """)

        # Build the command message
        if not commands:
            text_area.setText("No appliance control commands generated.")
        else:
            message = "Appliance Control Commands:\n" + "=" * 50 + "\n\n"
            for cmd in commands:
                message += f"Device: {cmd['device']}\nAction: {cmd['action']}\nTime: {cmd['time']}\n" + "-" * 50 + "\n"
            text_area.setText(message)

        layout.addWidget(text_area)

        # OK button to close the dialog
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #213448;
                color: #ECEFCA;
                border: none;
                padding: 8px 16px;
                font-size: 12pt;
                font-weight: bold;
                border-radius: 8px;
                font-family: Roboto, Arial;
            }
            QPushButton:hover { background-color: #94B4C1; }
        """)
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        logging.debug("ApplianceControlDialog UI initialized")

def fetch_weather_data():
    """
    Fetch current location, temperature, and humidity for Hanoi, Vietnam using WeatherAPI.com.

    Returns:
        tuple: (location (str), temperature (°C), humidity (%)), or (None, None, None) if failed.
    """
    try:
        url = "http://api.weatherapi.com/v1/current.json?key=f002f472449b4c6d89f154907251205&q=Hanoi"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        location = data['location']['name']
        temperature = data['current']['temp_c']
        humidity = data['current']['humidity']
        logging.debug(f"Fetched weather for Hanoi: location={location}, temp={temperature}°C, humidity={humidity}%")
        return location, temperature, humidity
    except Exception as e:
        logging.error(f"Failed to fetch weather data: {str(e)}")
        return None, None, None

def load_return_time(file_path):
    """
    Load predicted user return time from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        str: Return time (HH:MM), or None if failed.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'return_time' not in data:
            logging.error("JSON file missing 'return_time' key")
            return None
        logging.debug(f"Loaded return time: {data['return_time']}")
        return data['return_time']
    except Exception as e:
        logging.error(f"Failed to load return time from {file_path}: {str(e)}")
        return None

def generate_control_commands(temperature, humidity, return_time):
    """
    Generate appliance control commands based on weather and return time.

    Args:
        temperature (float): Current temperature (°C).
        humidity (float): Current humidity (%).
        return_time (str): Predicted return time (HH:MM).

    Returns:
        list: List of command dictionaries {device, action, time}.
    """
    commands = []

    # Parse return time
    try:
        return_datetime = datetime.strptime(return_time, '%H:%M')
        current_date = datetime.now().date()
        return_datetime = datetime.combine(current_date, return_datetime.time())
        if return_datetime < datetime.now():
            return_datetime += timedelta(days=1)  # Assume next day if time has passed
    except ValueError as e:
        logging.error(f"Invalid return_time format: {str(e)}")
        return commands

    # Temperature-based commands
    if temperature is not None:
        if temperature > 25.0:  # High temperature
            ac_time = return_datetime - timedelta(minutes=10)
            commands.append({
                'device': 'Air Conditioner',
                'action': 'Turn On',
                'time': ac_time.strftime('%H:%M')
            })
            logging.debug("Generated AC command: Turn On at %s", ac_time.strftime('%H:%M'))
        elif temperature < 18.0:  # Low temperature
            heater_time = return_datetime - timedelta(minutes=20)
            commands.append({
                'device': 'Heater',
                'action': 'Turn On',
                'time': heater_time.strftime('%H:%M')
            })
            logging.debug("Generated Heater command: Turn On at %s", heater_time.strftime('%H:%M'))

    # Water heater command
    water_heater_time = return_datetime - timedelta(minutes=20)
    commands.append({
        'device': 'Water Heater',
        'action': 'Turn On',
        'time': water_heater_time.strftime('%H:%M')
    })
    logging.debug("Generated Water Heater command: Turn On at %s", water_heater_time.strftime('%H:%M'))

    # Humidity-based command
    if humidity is not None and humidity > 60.0:  # High humidity
        dehumidifier_time = return_datetime - timedelta(hours=3)
        commands.append({
            'device': 'Dehumidifier',
            'action': 'Turn On',
            'time': dehumidifier_time.strftime('%H:%M')
        })
        logging.debug("Generated Dehumidifier command: Turn On at %s", dehumidifier_time.strftime('%H:%M'))

    return commands