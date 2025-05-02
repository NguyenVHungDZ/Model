import joblib
import os
import sys
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

class ModelLoader:
    def __init__(self, base_path=None):
        if base_path is None:
            base_path = os.path.join(get_base_path(), '.pkl')
        self.base_path = base_path
        self.model = None
        self.device_encoder = None
        self.room_encoder = None
        self.scaler = None

    def load_assets(self):
        try:
            # Load model
            model_path = os.path.join(self.base_path, "gb_model.pkl")
            logging.debug(f"Loading model from: {model_path}")
            self.model = joblib.load(model_path)

            # Load device encoder
            device_encoder_path = os.path.join(self.base_path, "device_encoder.pkl")
            logging.debug(f"Loading device encoder from: {device_encoder_path}")
            self.device_encoder = joblib.load(device_encoder_path)

            # Load room encoder
            room_encoder_path = os.path.join(self.base_path, "room_encoder.pkl")
            logging.debug(f"Loading room encoder from: {room_encoder_path}")
            self.room_encoder = joblib.load(room_encoder_path)

            # Load scaler
            scaler_path = os.path.join(self.base_path, "scaler.pkl")
            logging.debug(f"Loading scaler from: {scaler_path}")
            self.scaler = joblib.load(scaler_path)

            logging.debug("All assets loaded successfully")
            return True, "Assets loaded successfully"
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}. Please ensure all .pkl files are in '{self.base_path}'."
            logging.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to load assets: {str(e)}"
            logging.error(error_msg)
            return False, error_msg