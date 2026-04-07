"""
Card Effects Interpreter
Parses and applies card effects from the Inventaire.csv
"""
import random

class CardEffects:
    """Interprets and applies card effects based on the action text from CSV."""

    @staticmethod
    def parse_effect(card_name, action_text):
        """Parse the action text and return effect callable."""
        # This will be expanded as we implement each card's effect
        actions = {
            "Fantôme": CardEffects.fantome_effect,
            "Guetteur": CardEffects.guetteur_effect,
            "Magicien": CardEffects.magicien_effect,
            "Archer": CardEffects.archer_effect,
            "Sorcière": CardEffects.sorciere_effect,
            "Alchimiste": CardEffects.alchimiste_effect,
            "Capitaine": CardEffects.capitaine_effect,
            "Traître": CardEffects.traitre_effect,
            "Soldat": CardEffects.soldat_effect,
            "Marchand": CardEffects.marchand_effect,
            "Roi": CardEffects.roi_effect,
            "Baladin": CardEffects.baladin_effect,
            "Courtisane": CardEffects.courtisane_effect,
            "Reine": CardEffects.reine_effect,
            "Princesse": CardEffects.princesse_effect,
            "Prince": CardEffects.prince_effect,
            "Intrigant": CardEffects.intrigant_effect,
            "Espion": CardEffects.espion_effect,
            "Ambassadeur": CardEffects.ambassadeur_effect,
            "Voleur": CardEffects.voleur_effect,
            "Bouffon": CardEffects.bouffon_effect,
            "Fou": CardEffects.fou_effect,
            "Prêtre": CardEffects.pretre_effect,
            "Dame de compagnie": CardEffects.dame_compagnie_effect,
            "Courtisan": CardEffects.courtisan_effect,
            "Assassin": CardEffects.assassin_effect,
            "Conseiller du roi": CardEffects.conseiller_roi_effect,
            "Favorite": CardEffects.favorite_effect,
            "Prince charmant": CardEffects.prince_charmant_effect,
            "Chevalier noir": CardEffects.chevalier_noir_effect,
            "Barbare": CardEffects.barbare_effect,
            "Fée": CardEffects.fee_effect,
            "Enchanteur": CardEffects.enchanteur_effect,
            "Engin de siège": CardEffects.engin_siege_effect,
            "Dragon": CardEffects.dragon_effect,
            "Hérault": CardEffects.herault_effect,
            "Chevalier": CardEffects.chevalier_effect,
        }
        return actions.get(card_name, CardEffects.default_effect)

    @staticmethod
    def default_effect(game, player, card, position):
        """Default effect: card is placed but has no special action."""
        pass

    # Bleu effects
    @staticmethod
    def fantome_effect(game, player, card, position):
        """Le fantôme renvoie la carte dont il prend la place."""
        x, y = position
        existing_card = game.board.cour[y][x]
        if existing_card:
            game.board.cour[y][x] = None
            game.exchange.append(existing_card)

    @staticmethod
    def guetteur_effect(game, player, card, position):
        """Le guetteur déplace un soldat."""
        # Find a soldat and move it
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and "Soldat" in game.board.cour[cy][cx].nom:
                    # Simple displacement: just remove it
                    game.exchange.append(game.board.cour[cy][cx])
                    game.board.cour[cy][cx] = None
                    return

    @staticmethod
    def magicien_effect(game, player, card, position):
        """Le magicien renvoie n'importe quelle carte et l'ajoute aux cartes de l'échange."""
        # Return a random card from the board to exchange
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx]:
                    cards_on_board.append((game.board.cour[cy][cx], cx, cy))
        if cards_on_board:
            card_to_move, cx, cy = random.choice(cards_on_board)
            game.exchange.append(card_to_move)
            game.board.cour[cy][cx] = None

    @staticmethod
    def archer_effect(game, player, card, position):
        """L'archer renvoie une carte se trouvant hors les murs."""
        if game.exchange:
            game.exchange.pop(0)  # Remove from exchange

    @staticmethod
    def sorciere_effect(game, player, card, position):
        """La sorcière renvoie l'une des cartes de l'échange dans la main d'un joueur de votre choix."""
        if game.exchange:
            moved_card = game.exchange.pop(0)
            random_player = random.choice(game.players)
            random_player.hand.append(moved_card)

    @staticmethod
    def alchimiste_effect(game, player, card, position):
        """L'alchimiste vous fait échanger immédiatement deux cartes de votre main contre le même nombre de cartes de l'échange."""
        if len(player.hand) >= 2 and len(game.exchange) >= 2:
            # Remove 2 from hand
            for _ in range(2):
                if player.hand:
                    player.hand.pop(0)
            # Add 2 from exchange
            for _ in range(2):
                if game.exchange:
                    player.hand.append(game.exchange.pop(0))

    # Orange effects
    @staticmethod
    def capitaine_effect(game, player, card, position):
        """Le capitaine est un soldat. Protège tous les autres soldats sur le même rempart."""
        # Mark surrounding soldiers as protected
        x, y = position
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 4 and 0 <= ny < 4:
                    nearby_card = game.board.cour[ny][nx]
                    if nearby_card and "Soldat" in nearby_card.nom:
                        nearby_card.protected = True

    @staticmethod
    def traitre_effect(game, player, card, position):
        """Le traître est un soldat. Renvoie une carte se trouvant sur une case de cour voisine."""
        x, y = position
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < 4 and 0 <= ny < 4:
                    card_to_remove = game.board.cour[ny][nx]
                    if card_to_remove:
                        game.exchange.append(card_to_remove)
                        game.board.cour[ny][nx] = None
                        break

    @staticmethod
    def soldat_effect(game, player, card, position):
        """Le quatrième soldat arrivant sur un rempart renvoie l'engin de siège qui se trouve en face."""
        # Count soldiers already placed
        soldat_count = sum(1 for cy in range(4) for cx in range(4)
                          if game.board.cour[cy][cx] and "Soldat" in game.board.cour[cy][cx].nom)
        if soldat_count >= 4:
            # Remove a siege engine from exchange
            for i, card_in_exchange in enumerate(game.exchange):
                if "Engin" in card_in_exchange.nom:
                    game.exchange.pop(i)
                    break

    # Rouge effects
    @staticmethod
    def marchand_effect(game, player, card, position):
        """Le marchand vous fait effectuer une troisième action. Remplacez 3 pions d'autres joueurs."""
        # Grant extra action and place 3 pions
        player.extra_actions = (getattr(player, 'extra_actions', 0) or 0) + 1
    
    @staticmethod
    def roi_effect(game, player, card, position):
        """Le roi renvoie du château n'importe quelle autre carte."""
        # Remove a random card from board
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and game.board.cour[cy][cx] != card:
                    cards_on_board.append((cx, cy))
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            removed_card = game.board.cour[cy][cx]
            game.exchange.append(removed_card)
            game.board.cour[cy][cx] = None
    
    @staticmethod
    def baladin_effect(game, player, card, position):
        """Le baladin intervertit les cartes se trouvant sur des cases de cour voisines."""
        x, y = position
        adjacent_cards = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                adjacent_cards.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                adjacent_cards.append((x, ny))
        
        if len(adjacent_cards) >= 2:
            x1, y1 = adjacent_cards[0]
            x2, y2 = adjacent_cards[1]
            game.board.cour[y1][x1], game.board.cour[y2][x2] = game.board.cour[y2][x2], game.board.cour[y1][x1]
    
    @staticmethod
    def courtisane_effect(game, player, card, position):
        """La courtisane vous fait échanger une carte de votre main contre une carte aléatoire d'un autre joueur."""
        other_player = random.choice([p for p in game.players if p != player])
        if player.hand and other_player.hand:
            card_from_player = player.hand.pop(0)
            card_from_other = random.choice(other_player.hand)
            other_player.hand.remove(card_from_other)
            player.hand.append(card_from_other)
            other_player.hand.append(card_from_player)
    
    @staticmethod
    def reine_effect(game, player, card, position):
        """La reine renvoie de la cour n'importe quelle autre carte."""
        # Remove a random card from court
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and game.board.cour[cy][cx] != card:
                    cards_on_board.append((cx, cy))
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            removed_card = game.board.cour[cy][cx]
            game.exchange.append(removed_card)
            game.board.cour[cy][cx] = None
    
    @staticmethod
    def princesse_effect(game, player, card, position):
        """La princesse déplace un chevalier."""
        # Find and remove a knight
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and "Chevalier" in game.board.cour[cy][cx].nom:
                    game.exchange.append(game.board.cour[cy][cx])
                    game.board.cour[cy][cx] = None
                    return
    
    @staticmethod
    def prince_effect(game, player, card, position):
        """Si le roi est absent, les cartes devant être placées à côté du roi peuvent être placées à côté du prince."""
        # Mark card as king-adjacent substitute
        card.king_substitute = True
    
    @staticmethod
    def intrigant_effect(game, player, card, position):
        """L'intrigant échange les pions de deux autres cartes."""
        # Swap positions of two random cards
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and game.board.cour[cy][cx] != card:
                    cards_on_board.append((cx, cy))
        if len(cards_on_board) >= 2:
            idx1, idx2 = random.sample(range(len(cards_on_board)), 2)
            x1, y1 = cards_on_board[idx1]
            x2, y2 = cards_on_board[idx2]
            game.board.cour[y1][x1], game.board.cour[y2][x2] = game.board.cour[y2][x2], game.board.cour[y1][x1]
    
    @staticmethod
    def espion_effect(game, player, card, position):
        """L'espion permute les pions des cartes situées sur les cases voisines."""
        x, y = position
        adjacent_positions = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                adjacent_positions.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                adjacent_positions.append((x, ny))
        
        if len(adjacent_positions) >= 2:
            x1, y1 = adjacent_positions[0]
            x2, y2 = adjacent_positions[1]
            game.board.cour[y1][x1], game.board.cour[y2][x2] = game.board.cour[y2][x2], game.board.cour[y1][x1]
    
    @staticmethod
    def ambassadeur_effect(game, player, card, position):
        """L'ambassadeur est protégé."""
        card.protected = True
    
    @staticmethod
    def voleur_effect(game, player, card, position):
        """Le voleur retire le pion d'une carte voisine. Si elle est renvoyée, elle va à l'échange."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                game.board.cour[y][nx].stolen = True
                return
    
    @staticmethod
    def bouffon_effect(game, player, card, position):
        """Chaque joueur passe une carte à son voisin de gauche."""
        cards_to_pass = []
        for p in game.players:
            if p.hand:
                cards_to_pass.append(p.hand.pop(0))
            else:
                cards_to_pass.append(None)
        for i, p in enumerate(game.players):
            prev_idx = (i - 1) % len(game.players)
            if cards_to_pass[prev_idx]:
                p.hand.append(cards_to_pass[prev_idx])
    
    @staticmethod
    def fou_effect(game, player, card, position):
        """Chaque joueur pioche une carte au hasard du jeu de son voisin de droite."""
        for i, p in enumerate(game.players):
            next_idx = (i + 1) % len(game.players)
            other_player = game.players[next_idx]
            if other_player.hand:
                stolen_card = random.choice(other_player.hand)
                other_player.hand.remove(stolen_card)
                p.hand.append(stolen_card)
    
    @staticmethod
    def pretre_effect(game, player, card, position):
        """Le prêtre protège les personnages des cases voisines ayant un pion de même couleur."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                game.board.cour[y][nx].protected = True
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                game.board.cour[ny][x].protected = True
    
    @staticmethod
    def dame_compagnie_effect(game, player, card, position):
        """La dame de compagnie renvoie de la cour un personnage masculin voisin."""
        x, y = position
        male_cards = ["Roi", "Prince", "Chevalier"]
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if any(m in game.board.cour[y][nx].nom for m in male_cards):
                    game.exchange.append(game.board.cour[y][nx])
                    game.board.cour[y][nx] = None
                    return
    
    @staticmethod
    def courtisan_effect(game, player, card, position):
        """Le courtisan renvoie du château une carte se trouvant sur une case voisine."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                game.exchange.append(game.board.cour[y][nx])
                game.board.cour[y][nx] = None
                return
    
    @staticmethod
    def assassin_effect(game, player, card, position):
        """L'assassin retire définitivement du jeu n'importe quelle carte (sauf le roi) voisine."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if "Roi" not in game.board.cour[y][nx].nom:
                    # Remove permanently
                    game.board.cour[y][nx] = None
                    return
    
    @staticmethod
    def conseiller_roi_effect(game, player, card, position):
        """Le conseiller du roi met en jeu l'une des cartes se trouvant dans l'échange."""
        if game.exchange:
            card_from_exchange = game.exchange.pop(0)
            # Place it on the board if possible
            for cy in range(4):
                for cx in range(4):
                    if game.board.cour[cy][cx] is None:
                        game.board.cour[cy][cx] = card_from_exchange
                        return
    
    @staticmethod
    def favorite_effect(game, player, card, position):
        """La favorite déplace librement le roi et un chevalier."""
        # Mark for special movement
        card.can_move_king = True
    
    @staticmethod
    def prince_charmant_effect(game, player, card, position):
        """Le prince charmant déplace un personnage féminin."""
        female_cards = ["Reine", "Princesse", "Sorcière", "Fée"]
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx]:
                    if any(f in game.board.cour[cy][cx].nom for f in female_cards):
                        game.exchange.append(game.board.cour[cy][cx])
                        game.board.cour[cy][cx] = None
                        return
    
    @staticmethod
    def chevalier_noir_effect(game, player, card, position):
        """Le chevalier noir renvoie un chevalier se trouvant sur une case voisine."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if "Chevalier" in game.board.cour[y][nx].nom:
                    game.exchange.append(game.board.cour[y][nx])
                    game.board.cour[y][nx] = None
                    return

    # Vert effects
    @staticmethod
    def barbare_effect(game, player, card, position):
        """Le barbare renvoie une carte se trouvant dans une tour ou sur un rempart."""
        # Remove a random card from court
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx]:
                    cards_on_board.append((cx, cy))
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            game.exchange.append(game.board.cour[cy][cx])
            game.board.cour[cy][cx] = None

    @staticmethod
    def fee_effect(game, player, card, position):
        """La fée attire hors les murs l'un des personnages se trouvant dans le château."""
        # Pull a random card from court to exterior
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx]:
                    cards_on_board.append((cx, cy))
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            pulled_card = game.board.cour[cy][cx]
            game.board.cour[cy][cx] = None
            game.exchange.append(pulled_card)

    @staticmethod
    def enchanteur_effect(game, player, card, position):
        """L'enchanteur renvoie la dernière carte à avoir été placée."""
        # Find the last placed card and remove it
        # For now, remove the card at the position just before this one
        if hasattr(game, 'last_placed_card') and game.last_placed_card:
            game.exchange.append(game.last_placed_card)
            game.last_placed_card = None

    @staticmethod
    def engin_siege_effect(game, player, card, position):
        """Le quatrième engin de siège renvoie tous les soldats se trouvant sur les remparts."""
        # Count siege engines
        siege_count = sum(1 for cy in range(4) for cx in range(4) 
                         if game.board.cour[cy][cx] and "Engin" in game.board.cour[cy][cx].nom)
        if siege_count >= 4:
            # Remove all soldiers
            for cy in range(4):
                for cx in range(4):
                    if game.board.cour[cy][cx] and "Soldat" in game.board.cour[cy][cx].nom:
                        game.exchange.append(game.board.cour[cy][cx])
                        game.board.cour[cy][cx] = None

    @staticmethod
    def dragon_effect(game, player, card, position):
        """Le dragon renvoie une carte hors les murs et une carte dans une tour ou rempart."""
        # Remove two random cards from board
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx]:
                    cards_on_board.append((cx, cy))
        
        if len(cards_on_board) >= 2:
            selections = random.sample(cards_on_board, 2)
            for cx, cy in selections:
                game.exchange.append(game.board.cour[cy][cx])
                game.board.cour[cy][cx] = None

    @staticmethod
    def herault_effect(game, player, card, position):
        """Si le hérault est en jeu, le joueur ayant le roi doit le jouer quand vient son tour."""
        # Set flag on all players
        for p in game.players:
            p.must_play_king = True

    # Violet effects
    @staticmethod
    def chevalier_effect(game, player, card, position):
        """Le chevalier protège la carte sur laquelle il est posé."""
        # Mark the card below as protected
        card.protecting = True
