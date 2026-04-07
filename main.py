import pygame
from engine.game import GameState
from ui.renderer import CastelWindow

def main():
    print("=== Castel ===")
    print("Combien de joueurs ? (2-5, défaut: 2)")
    try:
        num_players = int(input("Nombre de joueurs: ") or "2")
        num_players = max(2, min(5, num_players))  # Clamp between 2 and 5
    except ValueError:
        num_players = 2
    
    print(f"Lancement du jeu avec {num_players} joueurs (1 humain, {num_players-1} ordinateurs)...")
    game = GameState(num_players=num_players)
    window = CastelWindow(game)
    window.run()
    pygame.quit()

if __name__ == "__main__":
    main()