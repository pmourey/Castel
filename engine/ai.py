import random
from .player import Player

class AIPlayer(Player):
    def __init__(self, color='black'):
        super().__init__(is_human=False, color=color)

    def choose_action(self, game):
        """Choose the next action.
        Returns one of:
          ('place', card, position)
          ('draw',)
          ('exchange', hand_idx, exch_idx)
          ('skip',)
        Never calls game methods directly to avoid double turn-advance.
        """
        # Try to place a card (shuffle order to avoid always picking same card)
        cards = list(self.hand)
        random.shuffle(cards)
        for card in cards:
            position = self._find_valid_position(game, card)
            if position is not None:
                return ('place', card, position)

        # Can't place: try exchange
        if game.exchange and self.hand:
            return ('exchange', 0, 0)

        # Try to draw
        if self.deck:
            return ('draw',)

        return ('skip',)

    def _find_valid_position(self, game, card):
        """Return the first valid board position for this card, or None."""
        lieu = card.lieu.lower()
        if 'cour' in lieu:
            for y in range(4):
                for x in range(4):
                    if game.board.cour[y][x] is None:
                        return (x, y)
        elif 'tour' in lieu:
            for (tx, ty), tile in game.board.tiles.items():
                if tile['type'] == 'tour' and tile['card'] is None:
                    return (tx, ty)
        elif 'rempart' in lieu:
            for (tx, ty), tile in game.board.tiles.items():
                if tile['type'] == 'rempart' and tile['card'] is None:
                    return (tx, ty)
        elif card.couleur.lower() == 'violet':
            # Chevalier: place on any occupied cour cell
            for y in range(4):
                for x in range(4):
                    if game.board.cour[y][x] is not None:
                        return (x, y)
        else:
            # Hors les murs: find a free exterior position
            for ext_x in range(5, 20):
                for ext_y in range(0, 5):
                    if (ext_x, ext_y) not in game.board.exterieur:
                        return (ext_x, ext_y)
        return None
