import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_appliances(appliances, device_encoder, room_encoder, scaler):
    """
    Preprocess a list of appliances for prediction.

    Args:
        appliances (list): List of dictionaries containing appliance data.
        device_encoder (LabelEncoder): Encoder for device types.
        room_encoder (LabelEncoder): Encoder for room locations.
        scaler (StandardScaler): Scaler for feature scaling.

    Returns:
        tuple: (scaled_features, valid_indices)
            - scaled_features: Preprocessed and scaled features for valid appliances.
            - valid_indices: Indices of appliances that were successfully preprocessed.
    """
    logging.debug(f"Preprocessing {len(appliances)} appliances")

    data = []
    valid_indices = []

    # Define the feature columns expected by the model
    feature_columns = [
        "Device Type",
        "Power Consumption (W)",
        "Room Location",
        "Temperature (°C)",
        "Humidity (%)",
        "Usage Duration (minutes)",
        "On/Off Status"
    ]

    # Process each appliance
    for idx, appliance in enumerate(appliances):
        try:
            # Encode device type
            device_encoded = device_encoder.transform([appliance["Device Type"]])[0]
            # Encode room location
            room_encoded = room_encoder.transform([appliance["Room Location"]])[0]
            # Convert on/off status to binary (1 for On, 0 for Off)
            status_binary = 1 if appliance["On/Off Status"].lower() == 'on' else 0

            # Use the recorded usage duration regardless of On/Off Status
            usage_duration = float(appliance["Usage Duration (minutes)"])

            # Create a row of features
            row = [
                device_encoded,
                float(appliance["Power Consumption (W)"]),
                room_encoded,
                float(appliance["Temperature (°C)"]),
                float(appliance["Humidity (%)"]),
                usage_duration,
                status_binary
            ]

            data.append(row)
            valid_indices.append(idx)
        except Exception as e:
            logging.error(f"Failed to preprocess appliance {idx}: {str(e)}")
            continue

    if not data:
        logging.warning("No valid appliances to preprocess")
        return None, []

    # Convert to DataFrame
    features_df = pd.DataFrame(data, columns=feature_columns)
    # Scale the features
    scaled_features = scaler.transform(features_df)
    logging.debug(f"Preprocessed {len(data)} appliances successfully")
    return scaled_features, valid_indices