import joblib
import numpy as np

# Load the trained model and encoders
model = joblib.load("testModel.pkl")
device_encoder = joblib.load("device_encoder.pkl")
room_encoder = joblib.load("room_encosder.pkl")
scaler = joblib.load("scaler.pkl")

# Preprocessing function
def preprocess_input(device_type, power, room, temp, humidity, duration, status):
    device_encoded = device_encoder.transform([device_type])[0]
    room_encoded = room_encoder.transform([room])[0]
    status_binary = 1 if status.lower() == 'on' else 0

    features = np.array([[device_encoded, power, room_encoded, temp, humidity, duration, status_binary]])
    scaled_features = scaler.transform(features)
    return scaled_features

# Example usage
input_data = preprocess_input("Smart Plug", 80, "Living Room", 24.5, 40, 30, "On")
predicted_cost = model.predict(input_data)
print("Predicted Energy Cost: $", round(predicted_cost[0], 2))
