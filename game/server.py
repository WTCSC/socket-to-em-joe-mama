import socket
import threading
import json

HOST = "0.0.0.0"  # Listen on all interfaces
MAX_PLAYERS = 8

class RussianRouletteServer:
    def __init__(self, port):
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((HOST, port))
        self.server.listen(MAX_PLAYERS)
        self.clients = []
        self.usernames = []
        self.game_started = False
        self.current_turn = 0

    def broadcast(self, message):
        """Send a message to all connected clients."""
        for client in self.clients:
            try:
                client.sendall(json.dumps(message).encode())
            except:
                pass

    def handle_client(self, client):
        """Handles individual client communication."""
        try:
            username = client.recv(1024).decode()
            self.usernames.append(username)
            self.broadcast({"type": "update_players", "players": self.usernames})

            while True:
                data = client.recv(1024).decode()
                if not data:
                    break
                message = json.loads(data)

                if message["type"] == "fire":
                    self.handle_fire()

        except:
            pass
        finally:
            index = self.clients.index(client)
            self.clients.remove(client)
            client.close()
            self.usernames.pop(index)
            self.broadcast({"type": "update_players", "players": self.usernames})

    def handle_fire(self):
        """Handles a player's trigger pull."""
        import random
        bullet_fires = random.choice([False, False, False, False, False, True])  # 1/6 chance
        result = {"type": "shot_fired", "player": self.usernames[self.current_turn], "bullet_fires": bullet_fires}

        if bullet_fires:
            self.usernames.pop(self.current_turn)
            self.clients.pop(self.current_turn)
            if len(self.usernames) == 1:
                result["winner"] = self.usernames[0]  # Declare winner
                self.broadcast(result)
                return

        self.current_turn = (self.current_turn + 1) % len(self.usernames)
        self.broadcast(result)

    def start(self):
        print(f"Server started on port {self.port}")
        while not self.game_started:
            client, _ = self.server.accept()
            if len(self.clients) >= MAX_PLAYERS:
                client.sendall(json.dumps({"type": "full"}).encode())
                client.close()
                continue

            self.clients.append(client)
            threading.Thread(target=self.handle_client, args=(client,)).start()

if __name__ == "__main__":
    port = int(input("Enter port: "))
    server = RussianRouletteServer(port)
    server.start()
