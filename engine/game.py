from .board import Board
from .card import CARDS
from .player import Player
from .ai import AIPlayer
from .effects import CardEffects
import random

class GameState:
    def __init__(self, num_players=2):
        self.board = Board()
        self.players = []
        self.num_players = num_players

        # Define player colors and initial card distribution based on number of players
        player_colors = ['black', 'beige', 'red', 'green', 'purple']
        cards_in_hand = [9, 7, 5, 5]  # Index 0=2j, 1=3j, 2=4j, 3=5j
        cards_in_deck = [13, 8, 6, 4]  # Index 0=2j, 1=3j, 2=4j, 3=5j
        exchange_cards = [10, 11, 12, 11]  # Index 0=2j, 1=3j, 2=4j, 3=5j

        # Initialize players
        for i in range(num_players):
            if i == 0:
                player = Player(is_human=True, color=player_colors[i])
            else:
                player = AIPlayer(color=player_colors[i])
            self.players.append(player)

        self.current_player = 0
        self.all_cards = CARDS.copy()
        
        # Remove Fou and Bouffon for 2 players (official rules)
        if num_players == 2:
            self.all_cards = [card for card in self.all_cards if card.nom not in ['Fou', 'Bouffon']]
        
        random.shuffle(self.all_cards)

        self.exchange = []  # Cartes d'échange visibles
        self.turn = 0
        self.actions_remaining = 2  # Chaque joueur a 2 actions par tour
        self.current_action = 0  # 0=draw, 1=exchange, 2=place
        self.last_placed_card = None    # Dernière carte placée (pour enchanteur)
        self.previous_placed_card = None  # Avant-dernière carte placée
        self.last_displaced_card = None   # Carte déplacée lors du dernier placement (pour fantôme)

        # Generate initial castle
        self.generate_castle()

        # Distribute initial cards according to rules
        self._distribute_cards(num_players, cards_in_hand, cards_in_deck, exchange_cards)

    def _distribute_cards(self, num_players, cards_in_hand, cards_in_deck, exchange_cards):
        """Distribute cards according to official rules"""
        idx = num_players - 2  # Index 0 for 2 players, 1 for 3 players, etc.
        hand_count = cards_in_hand[idx]
        deck_count = cards_in_deck[idx]
        exchange_count = exchange_cards[idx]

        cards_used = 0

        # Distribute decks (pioche)
        for player in self.players:
            for _ in range(deck_count):
                if cards_used < len(self.all_cards):
                    player.deck.append(self.all_cards[cards_used])
                    cards_used += 1

        # Distribute hands
        for player in self.players:
            for _ in range(hand_count):
                if cards_used < len(self.all_cards):
                    player.hand.append(self.all_cards[cards_used])
                    cards_used += 1

        # Distribute exchange
        for _ in range(exchange_count):
            if cards_used < len(self.all_cards):
                self.exchange.append(self.all_cards[cards_used])
                cards_used += 1

    def next_turn(self):
        self.current_player = (self.current_player + 1) % len(self.players)
        self.turn += 1
        self.actions_remaining = 2

    def draw_card(self, player):
        """ACTION 1: Draw a card from player's deck (pioche)"""
        if player.deck:
            card = player.deck.pop(0)
            player.hand.append(card)
            self.actions_remaining -= 1
            return card
        return None

    def exchange_card(self, player, hand_card_index, exchange_card_index):
        """ACTION 2: Exchange a card from hand with exchange pile"""
        if 0 <= hand_card_index < len(player.hand) and 0 <= exchange_card_index < len(self.exchange):
            hand_card = player.hand.pop(hand_card_index)
            exchange_card = self.exchange.pop(exchange_card_index)
            player.hand.append(exchange_card)
            self.exchange.append(hand_card)
            self.actions_remaining -= 1
            return exchange_card
        return None

    def advance_turn_if_done(self):
        """Call after each action. Returns True if the turn was advanced.
        Consumes one extra_action from the Marchand before ending the turn."""
        if self.actions_remaining <= 0:
            player = self.players[self.current_player]
            extra = getattr(player, 'extra_actions', 0) or 0
            if extra > 0:
                player.extra_actions = extra - 1
                self.actions_remaining = 1   # grant one extra action
                return False
            self.next_turn()
            return True
        return False

    def check_win_condition(self, player):
        """Check if player has won according to official rules"""
        # Player wins if they have no cards in hand AND no cards in deck
        return len(player.hand) == 0 and len(player.deck) == 0

    def can_place_card(self, card, position):
        """Check if a card can be placed at a given position"""
        zone = self._get_zone_at_position(position)
        lieu = getattr(card, 'lieu', '').lower()

        # Global: Chevalier can be placed on top of an existing card anywhere
        if 'sur une autre carte' in lieu:
            x, y = position
            if 0 <= x < 4 and 0 <= y < 4:
                return self.board.cour[y][x] is not None
            if (x, y) in self.board.tiles:
                return self.board.tiles[(x, y)].get('card') is not None
            return False

        if zone == 'cour':
            return 'cour' in lieu
        if zone == 'tour':
            return 'tour' in lieu
        if zone == 'rempart':
            return 'rempart' in lieu
        if zone == 'exterieur':
            if 'hors les murs' not in lieu:
                return False
            if card.nom == 'Engin_de_siege':
                return self._is_valid_siege_position(position)
            return True
        return False

    def _is_valid_siege_position(self, position):
        """Engin de siège must face a rempart, and only one per rempart face."""
        if self.board.exterieur.get(position) is not None:
            return False
        x, y = position
        facing_rempart = None
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) in self.board.tiles and self.board.tiles[(nx, ny)]['type'] == 'rempart':
                facing_rempart = (nx, ny)
                break
        if facing_rempart is None:
            return False
        # Only one engin de siège may face each rempart
        fx, fy = facing_rempart
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = fx + dx, fy + dy
            if (nx, ny) != position:
                existing = self.board.exterieur.get((nx, ny))
                if existing and 'Engin' in getattr(existing, 'nom', ''):
                    return False
        return True

    def _get_zone_at_position(self, position):
        """Determine the zone for a given position"""
        if isinstance(position, tuple) and len(position) == 2:
            x, y = position
            if 0 <= x < 4 and 0 <= y < 4:
                return 'cour'
            elif (x, y) in self.board.tiles:
                tile_type = self.board.tiles[(x, y)]['type']
                return 'tour' if tile_type == 'tour' else 'rempart'
        return 'exterieur'

    def apply_effect(self, card, player):
        if card.used:
            return
        # Get and call the appropriate effect
        effect = CardEffects.parse_effect(card.nom, card.action)
        # Call the effect with the last position where the card was placed
        if hasattr(self, 'last_position'):
            effect(self, player, card, self.last_position)
        card.used = True

    def generate_castle(self):
        # Add tiles AROUND the cour 4x4
        # Cour interior is at positions (0,0) to (3,3)
        # Tiles surround the cour at positions (-1 to 4)

        # Corners with Tours (towers)
        # Adjust rotations so that rotation=0 corresponds to the reference tile
        # (Tour.png) oriented as the lower-right tower. Rotations are multiples
        # of 90 degrees counter-clockwise (pygame.transform.rotate uses CCW angles).
        # Therefore: Bottom-right = 0, Bottom-left = 1 (90° CCW),
        # Top-left = 2 (180°), Top-right = 3 (270°).
        self.board.add_tile(-1, -1, 'tour', 2)  # Top-left
        # Swap Top-right and Bottom-left rotations to fix orientation
        self.board.add_tile(4, -1, 'tour', 1)   # Top-right
        self.board.add_tile(-1, 4, 'tour', 3)   # Bottom-left
        self.board.add_tile(4, 4, 'tour', 0)    # Bottom-right

        # Top and bottom walls (remparts)
        for i in range(4):
            self.board.add_tile(i, -1, 'rempart', 0)  # Top
            self.board.add_tile(i, 4, 'rempart', 0)   # Bottom

        # Left and right walls (remparts)
        for i in range(4):
            self.board.add_tile(-1, i, 'rempart', 1)  # Left
            self.board.add_tile(4, i, 'rempart', 1)   # Right

    def place_card(self, player, card, position):
        """ACTION 3: Place a card on the board according to rules"""
        if card not in player.hand:
            return False

        # Validate placement based on card's location requirement
        if not self.can_place_card(card, position):
            return False

        # Save the card currently at this position (for fantôme effect)
        x, y = position
        if (x, y) in self.board.tiles:
            self.last_displaced_card = self.board.tiles[(x, y)].get('card')
        elif 0 <= x < 4 and 0 <= y < 4:
            self.last_displaced_card = self.board.cour[y][x]
        else:
            self.last_displaced_card = self.board.exterieur.get((x, y))

        # Check for special rules
        zone = self._get_zone_at_position(position)

        # Soldier and siege engine rules
        if "Soldat" in card.nom and zone == 'rempart':
            self._handle_fourth_soldier(card, position)

        if "Engin" in card.nom:
            engines_count = sum(
                1 for ext_card in self.board.exterieur.values()
                if ext_card and "Engin" in getattr(ext_card, 'nom', '')
            )
            if engines_count >= 3:
                self._handle_fourth_siege_engine()

        # Chevalier: link to the card it protects (for stacked display)
        lieu_card = getattr(card, 'lieu', '').lower()
        if 'sur une autre carte' in lieu_card:
            cx, cy = position
            existing = None
            if 0 <= cx < 4 and 0 <= cy < 4:
                existing = self.board.cour[cy][cx]
            elif (cx, cy) in self.board.tiles:
                existing = self.board.tiles[(cx, cy)].get('card')
            if existing:
                card.protects = existing
                existing.protected = True

        # Track card ownership for pion rules
        card.pion_owner = player

        # Remove from hand and place on board
        player.hand.remove(card)
        self.board.place_card(card, position)
        self.last_position = position
        self.previous_placed_card = self.last_placed_card
        self.last_placed_card = card

        # Place pion on card
        if player.pions_remaining > 0:
            player.pions_remaining -= 1

        # Apply card effect
        self.apply_effect(card, player)

        # Check win condition
        if self.check_win_condition(player):
            return 'win'

        # Decrement actions
        self.actions_remaining -= 1
        return 'ok'

    def _handle_fourth_soldier(self, card, position):
        """Handle the special rule for 4th soldier on a rempart"""
        x, y = position
        # Find opposite siege engine
        # TODO: Implement based on actual board layout
        pass

    def _handle_fourth_siege_engine(self):
        """Handle the special rule for 4th siege engine"""
        # Remove all soldiers from remparts
        for (tx, ty), tile in self.board.tiles.items():
            if tile['type'] == 'rempart' and tile['card'] and "Soldat" in tile['card'].nom:
                # Check if protected
                if not getattr(tile['card'], 'protected', False):
                    # Return soldier to exchange
                    self.exchange.append(tile['card'])
                    tile['card'] = None





