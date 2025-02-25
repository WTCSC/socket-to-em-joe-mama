import sys
import socket
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QComboBox, QLabel, QMessageBox, QHBoxLayout, QListWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# Discord-like color scheme
DISCORD_DARK = "#36393F"
DISCORD_GRAY = "#2F3136"
DISCORD_LIGHT_GRAY = "#40444B"
DISCORD_BLUE = "#5865F2"
DISCORD_TEXT = "#FFFFFF"
DISCORD_PLACEHOLDER = "#72767D"

class MessageReceiver(QObject):
    """A helper class to handle signals for updating the chat display."""
    new_message = pyqtSignal(str)  # Signal to emit new messages

class LoginWindow(QWidget):
    """A window for users to input their username, IP, and port."""
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Setup the login UI with Discord-like styling."""
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DISCORD_DARK};
                color: {DISCORD_TEXT};
            }}
            QLineEdit {{
                background-color: {DISCORD_LIGHT_GRAY};
                border: 1px solid {DISCORD_GRAY};
                border-radius: 5px;
                padding: 10px;
                color: {DISCORD_TEXT};
            }}
            QLineEdit::placeholder {{
                color: {DISCORD_PLACEHOLDER};
            }}
            QPushButton {{
                background-color: {DISCORD_BLUE};
                color: {DISCORD_TEXT};
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4752C4;
            }}
        """)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Welcome to Chat App")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        layout.addWidget(self.username_input)

        # IP input
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter server IP (default: 127.0.0.1)")
        layout.addWidget(self.ip_input)

        # Port input
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter server port (default: 5555)")
        layout.addWidget(self.port_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.on_login)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def on_login(self):
        """Handle the login button click."""
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

        self.close()  # Close the login window
        self.chat_window = ChatWindow(username, ip, port)
        self.chat_window.show()

class ChatWindow(QWidget):
    """The main chat window."""
    def __init__(self, username, ip, port):
        super().__init__()
        self.username = username
        self.ip = ip
        self.port = port
        self.client_socket = None
        self.message_receiver = MessageReceiver()  # Create a message receiver
        self.init_ui()
        self.connect_to_server()

    def init_ui(self):
        """Setup the chat client UI with Discord-like styling."""
        self.setWindowTitle(f"Chat Client - {self.username}")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {DISCORD_DARK};
                color: {DISCORD_TEXT};
            }}
            QTextEdit {{
                background-color: {DISCORD_GRAY};
                border: none;
                padding: 10px;
                color: {DISCORD_TEXT};
                font-size: 14px;
            }}
            QLineEdit {{
                background-color: {DISCORD_LIGHT_GRAY};
                border: 1px solid {DISCORD_GRAY};
                border-radius: 5px;
                padding: 10px;
                color: {DISCORD_TEXT};
            }}
            QLineEdit::placeholder {{
                color: {DISCORD_PLACEHOLDER};
            }}
            QPushButton {{
                background-color: {DISCORD_BLUE};
                color: {DISCORD_TEXT};
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #4752C4;
            }}
            QListWidget {{
                background-color: {DISCORD_GRAY};
                border: none;
                padding: 10px;
                color: {DISCORD_TEXT};
                font-size: 14px;
            }}
        """)

        main_layout = QHBoxLayout()

        # Sidebar
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 10, 10, 10)

        # Profile area
        profile_label = QLabel(f"Profile: {self.username}")
        profile_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        sidebar_layout.addWidget(profile_label)

        # Chatrooms list
        self.chatrooms_list = QListWidget()
        self.chatrooms_list.addItem("General")
        self.chatrooms_list.addItem("Room 1")
        self.chatrooms_list.addItem("Room 2")
        self.chatrooms_list.itemClicked.connect(self.join_chatroom)
        sidebar_layout.addWidget(QLabel("Chatrooms:"))
        sidebar_layout.addWidget(self.chatrooms_list)

        main_layout.addLayout(sidebar_layout, 1)

        # Chat area
        chat_layout = QVBoxLayout()

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        chat_layout.addLayout(input_layout)

        main_layout.addLayout(chat_layout, 3)

        self.setLayout(main_layout)

        # Connect the message receiver signal to update the chat display
        self.message_receiver.new_message.connect(self.update_chat_display)

    def connect_to_server(self):
        """Establish connection with the chat server."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.ip, self.port))
            self.client_socket.send(self.username.encode('utf-8'))
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to connect: {e}")
            self.close()

    def receive_messages(self):
        """Receive messages from server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                print(f"Received message: {message}")  # Debug: Print received message
                # Emit the new message signal
                self.message_receiver.new_message.emit(message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                break
        self.client_socket.close()

    def update_chat_display(self, message):
        """Update the chat display with a new message."""
        print(f"Updating chat display with: {message}")  # Debug: Print message being added to chat display
        self.chat_display.append(message)

    def send_message(self):
        """Send a message to the server."""
        message = self.message_input.text().strip()
        if message:
            self.client_socket.send(message.encode('utf-8'))
            self.message_input.clear()

    def join_chatroom(self, item):
        """Join a chatroom."""
        chatroom = item.text()
        self.client_socket.send(f"/join {chatroom}".encode('utf-8'))

def run_client():
    """Launch the chat client UI."""
    app = QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_client()