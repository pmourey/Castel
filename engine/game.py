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
        self.last_placed_card = None  # Pour les effets qui dépendent du dernier placement

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
            if self.actions_remaining <= 0:
                self.next_turn()
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
            if self.actions_remaining <= 0:
                self.next_turn()
            return exchange_card
        return None

    def check_win_condition(self, player):
        """Check if player has won according to official rules"""
        # Player wins if they have no cards in hand AND no cards in deck
        return len(player.hand) == 0 and len(player.deck) == 0

    def can_place_card(self, card, position):
        """Check if a card can be placed at a given position"""
        # Check if zone matches card's location requirement
        zone = self._get_zone_at_position(position)
        card_location = getattr(card, 'lieu', '').lower()

        if zone == 'cour' and 'cour' not in card_location:
            return False
        if zone == 'tour' and 'tour' not in card_location:
            return False
        if zone == 'rempart' and 'rempart' not in card_location:
            return False
        if zone == 'exterieur' and 'extérieur' not in card_location and 'chevalier' not in card_location:
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
        self.board.add_tile(-1, -1, 'tour', 0)  # Top-left
        self.board.add_tile(4, -1, 'tour', 1)   # Top-right
        self.board.add_tile(-1, 4, 'tour', 3)   # Bottom-left
        self.board.add_tile(4, 4, 'tour', 2)    # Bottom-right

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

        # Check for special rules
        zone = self._get_zone_at_position(position)

        # Soldier and siege engine rules
        if "Soldat" in card.nom and zone == 'rempart':
            # Count soldiers on this rempart
            soldiers_on_rempart = 0
            for (tx, ty), tile in self.board.tiles.items():
                if tile['type'] == 'rempart' and tile['card'] and "Soldat" in tile['card'].nom:
                    soldiers_on_rempart += 1

            # If 4th soldier, check for siege engine
            if soldiers_on_rempart >= 3:
                # Find siege engine opposite and remove it
                self._handle_fourth_soldier(card, position)

        if "Engin" in card.nom:
            # Siege engine rules
            engines_count = sum(1 for (_, _), tile in self.board.tiles.items()
                              if "Engin" in getattr(tile['card'], 'nom', ''))
            engines_count += sum(1 for card_in_ext in self.board.exterieur.values()
                                if card_in_ext and "Engin" in getattr(card_in_ext, 'nom', ''))

            # If 4th engine, remove all soldiers
            if engines_count >= 3:
                self._handle_fourth_siege_engine()

        # Remove from hand and place on board
        player.hand.remove(card)
        self.board.place_card(card, position)
        self.last_position = position
        self.last_placed_card = card

        # Place pion on card
        if player.pions_remaining > 0:
            player.pions_remaining -= 1

        # Apply card effect
        self.apply_effect(card, player)

        # Check win condition
        if self.check_win_condition(player):
            return True  # Player won

        # Decrement actions
        self.actions_remaining -= 1
        if self.actions_remaining <= 0:
            self.next_turn()

        return True

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





