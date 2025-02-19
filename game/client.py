import socket
import json
import threading
import pygame
import ui

class RussianRouletteClient:
    def __init__(self, server_ip, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((server_ip, port))
        self.username = input("Enter your username: ")
        self.client.sendall(self.username.encode())
        self.ui = ui.GameUI(self)
        threading.Thread(target=self.receive_messages, daemon=True).start()
        self.ui.run()

    def send_fire(self):
        self.client.sendall(json.dumps({"type": "fire"}).encode())

    def receive_messages(self):
        while True:
            try:
                data = self.client.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)
                self.ui.handle_server_message(message)
            except:
                break

if __name__ == "__main__":
    server_ip = input("Enter server IP: ")
    port = int(input("Enter port: "))
    client = RussianRouletteClient(server_ip, port)
