# **EnergyCostPredictorApp README**

**Last Updated:** May 24, 2025

## **Overview**

`EnergyCostPredictorApp` is a **PyQt5-based desktop application** designed to predict and manage energy costs for household appliances. It leverages a machine learning model to forecast monthly bills, provides energy usage profiles, visualizes appliance usage patterns, and manages appliance states based on the owner's presence and environmental conditions. The app also supports automatic model updates from a Google Cloud Storage bucket and integrates weather-based appliance recommendations.

This README provides detailed instructions on setting up and running the application on your local machine.

## **Features**

- **Energy Cost Prediction**: Predicts monthly energy bills based on a 7-day dataset using a machine learning model.
- **Energy Profiles**: Adjusts appliance usage with profiles (Eco, Balanced, Comfort, Normal).
- **Model Updates**: Automatically checks for and downloads new models from a Google Cloud Storage bucket.
- **Usage Graph**: Visualizes weekly usage patterns for individual appliances.
- **Weather Integration**: Displays simulated weather data and provides appliance recommendations.
- **Owner Presence Management**: Manages appliance states based on the owner's expected return time, with a grace period countdown and power reduction.

## **Prerequisites**

Before setting up the application, ensure you have the following:

### **System Requirements**
- **Operating System**: Windows, macOS, or Linux.
- **Python Version**: Python 3.8 or higher (tested with Python 3.9).
- **Disk Space**: Approximately 500 MB for dependencies and model files.
- **Internet Connection**: **Required** for initial setup (downloading dependencies) and model updates.

### **Software Requirements**
- **Python**: Install Python from [python.org](https://www.python.org/downloads/).
- **pip**: Ensure `pip` is installed (usually bundled with Python).
- **Git**: Optional, for cloning the repository (download from [git-scm.com](https://git-scm.com/downloads)).

### **Hardware Requirements**
- **RAM**: Minimum 4 GB (8 GB recommended).
- **CPU**: Any modern processor (e.g., Intel i3 or equivalent).

## **Setup Instructions**

Follow these steps to set up the `EnergyCostPredictorApp` on your machine.

### **Step 1: Clone or Download the Repository**
1. **Option 1: Clone with Git**
   - Open a terminal or command prompt.
   - Run the following command to clone the repository:
     ```
     git clone https://github.com/NguyenVHungDZ/Model
     ```

2. **Option 2: Download Manually**
   - Download the project as a ZIP file from the repository's GitHub page.
   - Extract the ZIP file to a directory 
   - Navigate to the extracted directory:
     ```
     cd /path/to/Model
     ```

### **Step 2: Set Up a Virtual Environment **
1. Create a virtual environment to isolate dependencies:
   ```
   python -m venv venv
   ```
2. **Activate the virtual environment**:
   - **Windows**:
     ```
     venv\Scripts\activate
     ```
   - **macOS/Linux**:
     ```
     source venv/bin/activate
     ```
   You should see `(venv)` in your terminal prompt.

### **Step 3: Install Dependencies**
1. Install the required Python packages using `pip`:
   ```
   pip install -r requirements.txt
   ```
2. **If `requirements.txt` is not provided**, install the following packages manually:
   ```
   pip install PyQt5 numpy pandas matplotlib google-cloud-storage joblib requests urllib3
   ```
   - **PyQt5**: For the GUI framework.
   - **numpy**, **pandas**: For data processing.
   - **matplotlib**: For usage graph visualization.
   - **google-cloud-storage**: For model updates from Google Cloud Storage.
   - **joblib**: For loading the machine learning model.
   - **requests**, **urllib3**: For network operations.

### **Step 4: Prepare Dataset**
The app requires a dataset file (`mock_appliances_week.json`) for energy cost predictions. This file should contain 7 days of appliance data (e.g., May 12 to May 18, 2025).

1. **Place Dataset**:
   - Ensure `mock_appliances_week.json` is in the `mock_dataset` directory.
   - Example structure of the JSON file:
     ```json
     [
         {
             "Date": "2025-05-12",
             "Device Type": "Air Conditioner",
             "Power Consumption (W)": 1200.0,
             "Room Location": "Living Room",
             "Temperature (°C)": 25.0,
             "Humidity (%)": 60.0,
             "Usage Duration (minutes)": 60.0,
             "On/Off Status": "On",
             "Turn On Time": "08:00"
         },
         ...
     ]
     ```

2. **Create Dataset (if wanted)**:
   - If the dataset is not provided, create a JSON file with at least 7 days of data (56 records for 8 appliances per day).
   - Save it as `mock_dataset/mock_appliances_week.json`.

## **Running the Application**

### **Step 1: Run the Application**
1. Ensure you're in the project directory with the virtual environment activated:
   ```
   cd /path/to/Model
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
2. **Run the main script**:
   ```
   python main.py
   ```
3. The application window should open, displaying the main interface with buttons like "Load Appliances", "Show Usage Graph", and "Settings ⚙️".

### **Step 2: Initial Setup**
1. **Load Dataset**:
   - Click **"Load Appliances"**.
   - Select `mock_appliances_week.json` from the `mock_dataset` directory.
   - The table will populate with appliance data for the first day (e.g., May 12, 2025), and the predicted monthly bill will update (e.g., "Predicted Monthly Bill: $179.14").
2. **Check for Model Update**:
   - Click **"Check for Model Update"** to download the latest `gb_model.pkl` from the `big_data32` bucket if new folders are available.
   - **Ensure an internet connection is available for this step.**
3. **Set Up Owner Return Time**:
   - In the "Owner Status" section, set the "Expected Return Time" (e.g., 20:30 PM).
   - Click **"Save"** to confirm the return time.
   - The app will compare with the current time (08:20 PM) and start a countdown if the time has passed.

### **Step 3: Using the Application**
- **Navigate Days**: Use the "◄" and "►" buttons to view appliance data for different days (May 12 to May 18, 2025).
- **Change Profile**: Click "Eco", "Balanced", "Comfort", or "Normal" to adjust appliance usage and recalculate the bill.
- **View Usage Graph**: Click **"Show Usage Graph"** to see weekly usage patterns for each appliance, toggling between appliances with the "Next Appliance" button.
- **Manage Owner Presence**:
  - Set a return time and save it.
  - If the return time passes (e.g., 20:30 PM passes at 08:20 PM), a grace period countdown starts (e.g., "Missed Return - Grace Period: 00:15").
  - Click "Simulate" to simulate the owner returning home, stopping the countdown.
- **Settings**: Click **"Settings ⚙️"** to adjust temperature thresholds, turn-on times, turn-off period, and grace period.

## **Troubleshooting**

### **Common Issues**
1. **"File not found" Error on Startup**:
   - **Cause**: Missing model files (`gb_model.pkl`, etc.) in the `models` directory.
   - **Solution**: Ensure all `.pkl` files are in the `models` directory. Run "Check for Model Update" to download them, or manually place them.
2. **"No file selected" Warning**:
   - **Cause**: Cancelled the dataset selection dialog.
   - **Solution**: Click "Load Appliances" and select `mock_appliances_week.json`.
3. **Model Update Fails**:
   - **Cause**: No internet connection or bucket access issues.
   - **Solution**: Ensure you're online. Verify the `big_data32` bucket is public and contains model files.
4. **GUI Not Displaying**:
   - **Cause**: Missing PyQt5 or dependency issues.
   - **Solution**: Reinstall dependencies:
     ```
     pip install PyQt5 numpy pandas matplotlib google-cloud-storage joblib requests urllib3
     ```

### **Logs**
- The app logs debug information to the console.
- **Check the logs** for detailed error messages (e.g., "Failed to load dataset: ...").

## **Additional Notes**

- **Dataset**: The app expects `mock_appliances_week.json` to contain 7 days of data (e.g., May 12 to May 18, 2025). Ensure the file matches this format.
- **Model Updates**: The app checks the `big_data32` bucket for new folders. Ensure the bucket is accessible and contains folders like `test_folder_2025-05-15/` with `gb_model.pkl`.
- **Time-Based Features**: The owner return feature uses the laptop's system time (e.g., 08:20 PM on May 24, 2025). **Ensure your system time is correct.**
- **Dependencies**: If dependency installation fails, try updating `pip`:
  ```
  pip install --upgrade pip
  ```

## **Contributing**

To contribute to the project:
## **Nguyen Viet Hung - 22028331**
## **Nguyen Nho Hieu - 22028328**
## **Hoang Duy Hung - 22028392**
## **License**


**Happy Energy Monitoring!**
