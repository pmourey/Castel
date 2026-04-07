import random
from .player import Player

class AIPlayer(Player):
    def __init__(self, color='black'):
        super().__init__(is_human=False, color=color)

    def choose_action(self, game):
        """Choose the next action for the AI player"""
        # Priority: 
        # 1. If we have no cards in hand but have cards in deck, draw
        # 2. Try to play a card if possible
        # 3. Otherwise exchange or draw
        
        if len(self.hand) == 0 and len(self.deck) > 0:
            # Draw a card
            game.draw_card(self)
            return None, None
        
        if self.hand:
            # Simple AI: try to play a card
            card = random.choice(self.hand)
            # Choose position based on lieu
            lieu = card.lieu.lower()
            if "cour" in lieu:
                # Try to find empty courtyard position
                for y in range(4):
                    for x in range(4):
                        if game.board.cour[y][x] is None:
                            return card, (x, y)
            elif "tour" in lieu:
                # Try to find empty tower
                for (tx, ty), tile in game.board.tiles.items():
                    if tile['type'] == 'tour' and tile['card'] is None:
                        return card, (tx, ty)
            elif "rempart" in lieu:
                # Try to find empty wall
                for (tx, ty), tile in game.board.tiles.items():
                    if tile['type'] == 'rempart' and tile['card'] is None:
                        return card, (tx, ty)
            else:
                # Exterior - just pick a random position
                return card, (random.randint(5,10), random.randint(5,10))
            
            # If no placement found, try exchange
            if game.exchange and len(self.hand) > 0:
                game.exchange_card(self, 0, 0)
                return None, None
        
        # Draw if possible
        if len(self.deck) > 0:
            game.draw_card(self)
            return None, None
        
        return None, None