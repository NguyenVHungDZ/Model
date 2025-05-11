from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
from PyQt5.QtCore import Qt
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class AdjustmentDialog(QDialog):
    def __init__(self, adjustments, appliances, parent=None):
        """
        Initialize the AdjustmentDialog to display usage time adjustments.

        Args:
            adjustments (dict): Dictionary of adjustments {index: adjustment_message}.
            appliances (list): List of appliance dictionaries.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("Usage Time Adjustments")
        self.setFixedSize(400, 300)
        self.init_ui(adjustments, appliances)

    def init_ui(self, adjustments, appliances):
        """
        Set up the dialog UI.

        Args:
            adjustments (dict): Dictionary of adjustments {index: adjustment_message}.
            appliances (list): List of appliance dictionaries.
        """
        layout = QVBoxLayout()

        # Text area to display adjustments
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        text_area.setStyleSheet("""
            QTextEdit {
                background-color: #3c3c3c;
                color: #eee;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px;
            }
        """)

        # Build the adjustment message
        if not adjustments:
            text_area.setText("No adjustments were necessary.")
        else:
            message = "Usage Time Adjustments:\n" + "=" * 50 + "\n\n"
            for idx, adjustment in adjustments.items():
                device = appliances[idx]["Device Type"]
                message += f"Device: {device}\n{adjustment}\n" + "-" * 50 + "\n"
            text_area.setText(message)

        layout.addWidget(text_area)

        # OK button to close the dialog
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #00e676; color: #111;
                border: none; padding: 8px 16px;
                font-size: 12pt; font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #00c853; }
        """)
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        logging.debug("AdjustmentDialog UI initialized")