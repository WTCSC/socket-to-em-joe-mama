import sys
import socket
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox, QHBoxLayout
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QThread

# Sleek modern color scheme
BACKGROUND_COLOR = "#1E1E2E"
TEXT_COLOR = "#CDD6F4"
INPUT_COLOR = "#313244"
BUTTON_COLOR = "#89B4FA"
BUTTON_HOVER_COLOR = "#74C7EC"
SCROLLBAR_COLOR = "#585B70"

class LoginWindow(QWidget):
    """Login window for username, IP, and port input."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 250)
        self.setStyleSheet(f"""
            QWidget {{ background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; font-family: 'Inter', sans-serif; }}
            QLineEdit {{ background-color: {INPUT_COLOR}; border: 2px solid {BUTTON_COLOR}; border-radius: 8px; padding: 10px; color: {TEXT_COLOR}; font-size: 14px; }}
            QPushButton {{ background-color: {BUTTON_COLOR}; color: {TEXT_COLOR}; border-radius: 8px; padding: 10px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {BUTTON_HOVER_COLOR}; }}
        """)

        layout = QVBoxLayout()
        
        title = QLabel("Chat App Login")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_input)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter server IP (default: 127.0.0.1)")
        layout.addWidget(self.ip_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter server port (default: 5555)")
        layout.addWidget(self.port_input)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.on_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def on_login(self):
        """Handles login and opens the chat window."""
        username = self.username_input.text().strip()
        ip = self.ip_input.text().strip() or "127.0.0.1"
        port = self.port_input.text().strip() or "5555"

        if not username:
            QMessageBox.warning(self, "Error", "Username cannot be empty!")
            return

        try:
            port = int(port)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid port number!")
            return

        self.close()  # Close login window
        self.chat_window = ChatWindow(username, ip, port)
        self.chat_window.show()

class ChatWindow(QWidget):
    """Main chat window."""
    
    def __init__(self, username, ip, port):
        super().__init__()
        self.username = username
        self.ip = ip
        self.port = port
        self.client_socket = None
        self.init_ui()
        self.connect_to_server()

    def init_ui(self):
        """Initializes the chat UI."""
        self.setWindowTitle(f"Chat - {self.username}")
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet(f"""
            QWidget {{ background-color: {BACKGROUND_COLOR}; color: {TEXT_COLOR}; }}
            QTextEdit {{ background-color: {INPUT_COLOR}; border: none; padding: 10px; border-radius: 8px; color: {TEXT_COLOR}; font-size: 15px; }}
            QLineEdit {{ background-color: {INPUT_COLOR}; border: 2px solid {BUTTON_COLOR}; border-radius: 8px; padding: 10px; color: {TEXT_COLOR}; font-size: 14px; }}
            QPushButton {{ background-color: {BUTTON_COLOR}; color: {TEXT_COLOR}; border-radius: 8px; padding: 10px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: {BUTTON_HOVER_COLOR}; }}
            QScrollBar:vertical {{ background: {SCROLLBAR_COLOR}; width: 10px; border-radius: 5px; }}
        """)

        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    def connect_to_server(self):
        """Connects to the server."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.client_socket.send(self.username.encode('utf-8'))
            
            self.receive_thread = ReceiveThread(self.client_socket)
            self.receive_thread.message_received.connect(self.update_chat_display)
            self.receive_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect: {e}")
            self.close()

    def send_message(self):
        """Sends a message to the server and updates the UI."""
        message = self.message_input.text().strip()
        if message:
            try:
                formatted_message = f"{self.username}: {message}"
                self.client_socket.send(formatted_message.encode('utf-8'))
                self.update_chat_display(formatted_message)  # Update UI immediately
                self.message_input.clear()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to send message: {e}")

    def update_chat_display(self, message):
        """Updates the chat display."""
        self.chat_display.append(message)
        self.chat_display.ensureCursorVisible()

class ReceiveThread(QThread):
    """Thread to receive messages from the server."""
    message_received = pyqtSignal(str)

    def __init__(self, client_socket):
        super().__init__()
        self.client_socket = client_socket

    def run(self):
        """Receives messages from the server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message:
                    self.message_received.emit(message)
            except:
                break
        self.client_socket.close()

def run_client():
    """Launches the chat client."""
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_client()
