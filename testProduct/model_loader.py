import joblib
import os
from sklearn.preprocessing import LabelEncoder

class ModelLoader:
    def __init__(self, model_path='d:/Desktop/Big Data/Model/.pkl/rf_model.pkl'):
        self.model_path = model_path
        self.rf_model = None
        self.le_device = LabelEncoder()
        self.le_room = LabelEncoder()
        self.device_types = ['Heater', 'Air Conditioner', 'Microwave', 'Washing Machine', 'Smart Plug', 'Smart Bulb', 
                             'Laptop Charger', 'TV', 'Ceiling Fan', 'Refrigerator']
        self.room_types = ['Living Room', 'Bedroom', 'Kitchen', 'Bathroom', 'Garage', 'Office']
        self.le_device.fit(self.device_types)
        self.le_room.fit(self.room_types)

    def load_model(self):
        try:
            self.rf_model = joblib.load(self.model_path)
            return True, "Model loaded successfully"
        except FileNotFoundError:
            return False, f"Model file '{self.model_path}' not found in {os.path.join(os.getcwd(), '.pkl')}."