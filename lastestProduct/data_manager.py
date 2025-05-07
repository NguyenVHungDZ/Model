import json
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    def __init__(self):
        """
        Initialize the DataManager without a hardcoded path.
        Appliances will be loaded via user selection.
        """
        self.appliances = []
        self.current_file_path = None
        logging.debug("DataManager initialized without initial data")

    def load_data_from_file(self, file_path):
        """
        Load appliance data from a user-selected JSON file.

        Args:
            file_path (str): Path to the JSON file selected by the user.

        Returns:
            bool: True if loading is successful, False otherwise.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.appliances = json.load(f)
            self.current_file_path = file_path
            logging.debug(f"Loaded {len(self.appliances)} appliances from {file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to load data from {file_path}: {str(e)}")
            return False

    def delete_appliance_at_index(self, index):
        """
        Delete an appliance at the specified index from the list and JSON file.

        Args:
            index (int): Index of the appliance to delete.

        Returns:
            bool: True if deletion is successful, False otherwise.
        """
        if not self.current_file_path:
            logging.error("No JSON file loaded. Cannot delete appliance.")
            return False

        if index < 0 or index >= len(self.appliances):
            logging.error(f"Invalid index {index} for deletion.")
            return False

        try:
            self.appliances.pop(index)
            with open(self.current_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.appliances, f, indent=4)
            logging.debug(f"Deleted appliance at index {index} from {self.current_file_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete appliance at index {index}: {str(e)}")
            return False

    def get_appliances(self):
        """
        Get the list of appliances.

        Returns:
            list: List of appliance dictionaries.
        """
        return self.appliances

    def update_appliances(self, appliances):
        """
        Update the appliances list with new data and save to the JSON file.

        Args:
            appliances (list): Updated list of appliance dictionaries.
        """
        self.appliances = appliances
        if self.current_file_path:
            try:
                with open(self.current_file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.appliances, f, indent=4)
                logging.debug(f"Updated {self.current_file_path} with {len(appliances)} appliances")
            except Exception as e:
                logging.error(f"Failed to update {self.current_file_path}: {str(e)}")
        else:
            logging.warning("No JSON file loaded. Appliances updated in memory only.")
        logging.debug(f"Updated appliances list with {len(appliances)} items")