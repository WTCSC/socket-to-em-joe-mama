import sys
import socket
import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QListWidget, QHBoxLayout
)
from PyQt6.QtCore import QTimer, Qt

clients = []
usernames = {}
chatrooms = {"General": []}

class ServerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.server_running = False
        self.server_socket = None
        self.admin_username = "Server"

    def init_ui(self):
        """Setup the server UI."""
        self.setWindowTitle("Chat Server")
        self.setGeometry(100, 100, 650, 500)
        self.setStyleSheet("""
            QWidget { background-color: #2C2F33; color: #FFFFFF; font-family: Arial; }
            QTextEdit, QListWidget { background-color: #23272A; border: none; padding: 8px; border-radius: 5px; }
            QLineEdit { background-color: #40444B; border: 1px solid #7289DA; padding: 8px; border-radius: 5px; color: #FFFFFF; }
            QPushButton { background-color: #7289DA; color: #FFFFFF; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #5B6EAE; }
            QLabel { font-size: 14px; font-weight: bold; }
        """)

        main_layout = QHBoxLayout()
        sidebar_layout = QVBoxLayout()
        chat_layout = QVBoxLayout()

        # Sidebar (User List & Server Status)
        self.status_label = QLabel("Server Stopped")
        self.status_label.setStyleSheet("font-size: 16px; color: #FF5555;")
        sidebar_layout.addWidget(self.status_label)

        self.user_list = QListWidget()
        sidebar_layout.addWidget(self.user_list)

        # Chat log
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Admin username input
        self.admin_username_input = QLineEdit()
        self.admin_username_input.setPlaceholderText("Enter Admin Username (Default: Server)")
        chat_layout.addWidget(self.admin_username_input)

        # Message input
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        input_layout.addWidget(self.message_input)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        # Server controls
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Enter IP (default: 127.0.0.1)")
        chat_layout.addWidget(self.ip_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("Enter Port (default: 5555)")
        chat_layout.addWidget(self.port_input)

        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        chat_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        chat_layout.addWidget(self.stop_button)

        # Layout setup
        main_layout.addLayout(sidebar_layout, 1)
        main_layout.addLayout(chat_layout, 3)
        self.setLayout(main_layout)

    def log_message(self, message):
        """Safely update the chat log from any thread."""
        QTimer.singleShot(0, lambda: self.chat_display.append(message))
        print(message)

    def broadcast(self, message, chatroom, sender_socket=None):
        """Send a message to all clients in a chatroom except the sender."""
        print(f"Broadcasting: {message}")
        disconnected_clients = []
        
        for client in chatrooms[chatroom]:
            if client != sender_socket:
                try:
                    client.send(message.encode('utf-8'))
                except:
                    client.close()
                    disconnected_clients.append(client)

        for client in disconnected_clients:
            chatrooms[chatroom].remove(client)
            clients.remove(client)

    def handle_client(self, client_socket):
        """Handle messages from a client."""
        try:
            username = client_socket.recv(1024).decode('utf-8')
            usernames[client_socket] = username
            self.user_list.addItem(username)
            self.log_message(f"{username} joined the chat.")

            chatroom = "General"
            chatrooms[chatroom].append(client_socket)
            self.broadcast(f"{username} joined {chatroom}.", chatroom, client_socket)

            while self.server_running:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                if message.startswith("/join"):
                    new_chatroom = message.split(" ")[1]
                    if new_chatroom not in chatrooms:
                        chatrooms[new_chatroom] = []
                    chatrooms[chatroom].remove(client_socket)
                    chatroom = new_chatroom
                    chatrooms[chatroom].append(client_socket)
                    self.broadcast(f"{username} joined {chatroom}.", chatroom, client_socket)
                elif message.startswith("/list"):
                    client_socket.send(f"Available chatrooms: {', '.join(chatrooms.keys())}".encode('utf-8'))
                elif message.startswith("/dm"):
                    parts = message.split(" ")
                    if len(parts) >= 3:
                        target_user = parts[1]
                        dm_message = " ".join(parts[2:])
                        for client, uname in usernames.items():
                            if uname == target_user:
                                client.send(f"[DM from {username}]: {dm_message}".encode('utf-8'))
                                break
                else:
                    self.broadcast(f"{username}: {message}", chatroom, client_socket)
                    self.log_message(f"{username}: {message}")
        except:
            pass
        finally:
            client_socket.close()
            clients.remove(client_socket)
            chatrooms[chatroom].remove(client_socket)
            self.user_list.takeItem(self.user_list.row(self.user_list.findItems(username, Qt.MatchExactly)[0]))
            self.log_message(f"{username} left the chat.")

    def start_server(self):
        """Start the chat server."""
        if self.server_running:
            return

        self.admin_username = self.admin_username_input.text().strip() or "Server"
        host = self.ip_input.text().strip() or "127.0.0.1"
        port = self.port_input.text().strip() or "5555"
        
        try:
            port = int(port)
        except ValueError:
            self.log_message("Invalid port number.")
            return

        self.server_running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server_socket.bind((host, port))
        except Exception as e:
            self.log_message(f"Failed to bind server: {e}")
            self.server_running = False
            return

        self.server_socket.listen(5)

        self.log_message(f"Server started on {host}:{port}")
        self.status_label.setText(f"Server Running on {host}:{port}")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        threading.Thread(target=self.accept_clients, daemon=True).start()

    def accept_clients(self):
        """Accept new clients and start a new thread for each."""
        while self.server_running:
            try:
                client_socket, _ = self.server_socket.accept()
                clients.append(client_socket)
                threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            except:
                break

    def send_message(self):
        """Send a message from the server with the admin username."""
        message = self.message_input.text().strip()
        if message:
            for chatroom in chatrooms:
                self.broadcast(f"{self.admin_username}: {message}", chatroom)
            self.log_message(f"{self.admin_username}: {message}")
            self.message_input.clear()

    def stop_server(self):
        """Stop the server and disconnect all clients."""
        self.server_running = False
        for client in clients:
            client.close()
        if self.server_socket:
            self.server_socket.close()

        self.log_message("Server stopped.")
        self.status_label.setText("Server Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

def run_server():
    """Launch the chat server UI."""
    app = QApplication(sys.argv)
    server = ServerApp()
    server.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    run_server()
