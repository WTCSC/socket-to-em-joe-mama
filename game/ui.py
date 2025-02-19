import pygame

class GameUI:
    def __init__(self, client):
        pygame.init()
        self.client = client
        self.screen = pygame.display.set_mode((800, 600))
        self.clock = pygame.time.Clock()
        self.players = []
        self.font = pygame.font.Font(None, 36)

    def handle_server_message(self, message):
        if message["type"] == "update_players":
            self.players = message["players"]
        elif message["type"] == "shot_fired":
            print(f"{message['player']} pulled the trigger...")
            if message["bullet_fires"]:
                print(f"{message['player']} is eliminated!")
                if "winner" in message:
                    print(f"Winner: {message['winner']}")

    def run(self):
        running = True
        while running:
            self.screen.fill((0, 0, 0))  # Clear screen
            for i, player in enumerate(self.players):
                text = self.font.render(player, True, (255, 255, 255))
                self.screen.blit(text, (100, 100 + i * 40))
            
            pygame.display.flip()
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.client.send_fire()

        pygame.quit()
