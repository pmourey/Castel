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
                    if game.board.cour[y][x] is None and game.can_place_card(card, (x, y)):
                        return (x, y)
        elif 'sur une autre carte' in lieu:
            # Chevalier: must go on an occupied cour cell
            for y in range(4):
                for x in range(4):
                    if game.board.cour[y][x] is not None and game.can_place_card(card, (x, y)):
                        return (x, y)
        elif 'tour' in lieu:
            for (tx, ty), tile in game.board.tiles.items():
                if tile['type'] == 'tour' and tile['card'] is None:
                    return (tx, ty)
        elif 'rempart' in lieu:
            for (tx, ty), tile in game.board.tiles.items():
                if tile['type'] == 'rempart' and tile['card'] is None:
                    return (tx, ty)
        elif 'hors les murs' in lieu:
            if card.nom == 'Engin_de_siege':
                # Must face a rempart; search all 16 canonical siege slots
                siege_slots = (
                    [(-2, y) for y in range(4)] +   # left wall
                    [(5,  y) for y in range(4)] +   # right wall
                    [(x, -2) for x in range(4)] +   # top wall
                    [(x,  5) for x in range(4)]     # bottom wall
                )
                random.shuffle(siege_slots)
                for pos in siege_slots:
                    if pos not in game.board.exterieur and game.can_place_card(card, pos):
                        return pos
            else:
                # Non-siege exterior cards go anywhere free outside the castle
                for ext_x in range(5, 25):
                    for ext_y in range(0, 5):
                        pos = (ext_x, ext_y)
                        if pos not in game.board.exterieur and pos not in game.board.tiles:
                            return pos
        return None
