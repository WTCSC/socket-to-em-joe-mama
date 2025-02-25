import sys
import socket
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QComboBox

HOST = '127.0.0.1'
PORT = 5555

class ClientApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.client_socket = None
        self.username = input("Enter your username: ").strip()
        if not self.username:
            print("Username cannot be empty!")
            sys.exit()
        self.connect_to_server()

    def init_ui(self):
        """Setup the chat client UI."""
        self.setWindowTitle("Chat Client")
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        self.message_input = QLineEdit()
        layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.chatroom_input = QComboBox()
        self.chatroom_input.addItem("General")
        self.chatroom_input.currentTextChanged.connect(self.join_chatroom)
        layout.addWidget(self.chatroom_input)

        self.setLayout(layout)

    def connect_to_server(self):
        """Establish connection with the chat server."""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))
            self.client_socket.send(self.username.encode('utf-8'))
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except:
            print("Failed to connect.")
            sys.exit()

    def receive_messages(self):
        """Receive messages from server."""
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                self.chat_display.append(message)
            except:
                break
        self.client_socket.close()

    def send_message(self):
        """Send a message to the server."""
        message = self.message_input.text().strip()
        if message:
            self.client_socket.send(message.encode('utf-8'))
            self.message_input.clear()

    def join_chatroom(self, chatroom):
        """Join a chatroom."""
        self.client_socket.send(f"/join {chatroom}".encode('utf-8'))

def run_client():
    """Launch the chat client UI."""
    app = QApplication(sys.argv)
    client = ClientApp()
    client.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_client()