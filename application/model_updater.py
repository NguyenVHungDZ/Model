import os
import joblib
import pandas as pd
from google.cloud import storage
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from datetime import datetime

# Configuration
BUCKET_NAME = "bigdata-model-bucket"
MODEL_BASE_PATH = "models/"
LOCAL_MODEL_DIR = "./models/"
VERSION_FILE = "./model_version.txt"
FILE_NAMES = ["gb_model.pkl", "device_encoder.pkl", "room_encoder.pkl", "scaler.pkl"]

# Ensure local model directory exists
os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

def get_latest_model_version(bucket):
    """Get the latest model version folder from GCS based on timestamp."""
    blobs = bucket.list_blobs(prefix=MODEL_BASE_PATH)
    version_folders = set()
    for blob in blobs:
        folder = "/".join(blob.name.split("/")[:-1])
        if folder.startswith(MODEL_BASE_PATH) and len(folder) > len(MODEL_BASE_PATH):
            version_folders.add(folder)
    if not version_folders:
        return None
    return max(version_folders, key=lambda x: x.split("/")[-1])

def get_local_version():
    """Read the locally stored model version."""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return None

def save_local_version(version):
    """Save the current model version locally."""
    with open(VERSION_FILE, "w") as f:
        f.write(version)

def download_model_files(bucket, version, local_dir):
    """Download model files for the given version to the local directory."""
    for file_name in FILE_NAMES:
        blob_path = f"{version}/{file_name}"
        local_path = os.path.join(local_dir, file_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(local_path)
        print(f"Downloaded {blob_path} to {local_path}")

def delete_old_model_files(local_dir):
    """Delete all model files in the local directory."""
    for file_name in FILE_NAMES:
        file_path = os.path.join(local_dir, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted old file: {file_path}")

def load_model_and_preprocessors(local_dir):
    """Load the model and preprocessors from the local directory."""
    try:
        model = joblib.load(os.path.join(local_dir, "gb_model.pkl"))
        device_encoder = joblib.load(os.path.join(local_dir, "device_encoder.pkl"))
        room_encoder = joblib.load(os.path.join(local_dir, "room_encoder.pkl"))
        scaler = joblib.load(os.path.join(local_dir, "scaler.pkl"))
        return model, device_encoder, room_encoder, scaler
    except Exception as e:
        print(f"Error loading model files: {e}")
        return None, None, None, None

def check_and_update_model():
    """Check for new model versions, update if available, and delete old files."""
    # Initialize GCS client
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(BUCKET_NAME)

    # Get latest version from GCS
    latest_version = get_latest_model_version(bucket)
    if not latest_version:
        print("No model versions found in GCS.")
        return None, None, None, None

    # Get local version
    local_version = get_local_version()

    if local_version != latest_version:
        print(f"New model version detected: {latest_version}")
        # Delete old model files
        delete_old_model_files(LOCAL_MODEL_DIR)
        # Download new model files
        download_model_files(bucket, latest_version, LOCAL_MODEL_DIR)
        # Update local version
        save_local_version(latest_version)
        # Load new model and preprocessors
        model, device_encoder, room_encoder, scaler = load_model_and_preprocessors(LOCAL_MODEL_DIR)
        if model is not None:
            print(f"Updated to model version: {latest_version}")
        return model, device_encoder, room_encoder, scaler
    else:
        print("No new model version available.")
        # Load existing model if available
        if os.path.exists(os.path.join(LOCAL_MODEL_DIR, "gb_model.pkl")):
            return load_model_and_preprocessors(LOCAL_MODEL_DIR)
        return None, None, None, None