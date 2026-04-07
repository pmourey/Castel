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
        actions = {
            # Bleu (tours)
            "Fantome":              CardEffects.fantome_effect,
            "Guetteur":             CardEffects.guetteur_effect,
            "Magicien":             CardEffects.magicien_effect,
            "Archer":               CardEffects.archer_effect,
            "Sorciere":             CardEffects.sorciere_effect,
            "Alchimiste":           CardEffects.alchimiste_effect,
            # Orange (remparts)
            "Capitaine":            CardEffects.capitaine_effect,
            "Traitre":              CardEffects.traitre_effect,
            "Soldat":               CardEffects.soldat_effect,
            # Rouge (cour)
            "Marchand":             CardEffects.marchand_effect,
            "Roi":                  CardEffects.roi_effect,
            "Baladin":              CardEffects.baladin_effect,
            "Courtisane":           CardEffects.courtisane_effect,
            "Reine":                CardEffects.reine_effect,
            "Princesse":            CardEffects.princesse_effect,
            "Prince":               CardEffects.prince_effect,
            "Intriguant":           CardEffects.intrigant_effect,
            "Espion":               CardEffects.espion_effect,
            "Ambassadeur":          CardEffects.ambassadeur_effect,
            "Voleur":               CardEffects.voleur_effect,
            "Bouffon":              CardEffects.bouffon_effect,
            "Fou":                  CardEffects.fou_effect,
            "Pretre":               CardEffects.pretre_effect,
            "Dame_de_compagnie":    CardEffects.dame_compagnie_effect,
            "Courtisan":            CardEffects.courtisan_effect,
            "Assassin":             CardEffects.assassin_effect,
            "Conseiller_du_roi":    CardEffects.conseiller_roi_effect,
            "Favorite":             CardEffects.favorite_effect,
            "Prince_charmant":      CardEffects.prince_charmant_effect,
            "Chevalier_noir":       CardEffects.chevalier_noir_effect,
            # Vert (hors les murs)
            "Barbare":              CardEffects.barbare_effect,
            "Fee":                  CardEffects.fee_effect,
            "Enchanteur":           CardEffects.enchanteur_effect,
            "Engin_de_siege":       CardEffects.engin_siege_effect,
            "Dragon":               CardEffects.dragon_effect,
            "Herault":              CardEffects.herault_effect,
            # Violet (sur une autre carte)
            "Chevalier":            CardEffects.chevalier_effect,
        }
        return actions.get(card_name, CardEffects.default_effect)

    @staticmethod
    def default_effect(game, player, card, position):
        """Default effect: card is placed but has no special action."""
        pass

    @staticmethod
    def _return_card(game, card):
        """Return a card to its owner's hand, or to exchange if owner unknown."""
        owner = getattr(card, 'pion_owner', None)
        if owner:
            owner.hand.append(card)
        else:
            game.exchange.append(card)

    # Bleu effects
    @staticmethod
    def fantome_effect(game, player, card, position):
        """Le fantôme renvoie la carte dont il prend la place."""
        displaced = game.last_displaced_card
        if displaced:
            CardEffects._return_card(game, displaced)
            game.last_displaced_card = None

    @staticmethod
    def guetteur_effect(game, player, card, position):
        """Le guetteur déplace un soldat vers une autre case de rempart libre."""
        for (tx, ty), tile in game.board.tiles.items():
            if tile['type'] == 'rempart' and tile['card'] and 'Soldat' in tile['card'].nom:
                soldat = tile['card']
                # Move to another free rempart
                for (nx, ny), ntile in game.board.tiles.items():
                    if ntile['type'] == 'rempart' and ntile['card'] is None and (nx, ny) != (tx, ty):
                        ntile['card'] = soldat
                        tile['card'] = None
                        return
                # No free rempart: return soldat to owner
                CardEffects._return_card(game, soldat)
                tile['card'] = None
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
        if game.board.exterieur:
            ext_pos = next(iter(game.board.exterieur))
            removed = game.board.exterieur.pop(ext_pos)
            if removed:
                CardEffects._return_card(game, removed)

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
        """Le capitaine protège tous les soldats sur le même rempart."""
        for (tx, ty), tile in game.board.tiles.items():
            if tile['type'] == 'rempart' and tile['card'] and 'Soldat' in tile['card'].nom:
                tile['card'].protected = True

    @staticmethod
    def traitre_effect(game, player, card, position):
        """Le traître renvoie une carte se trouvant sur une case de cour voisine."""
        x, y = position
        # Adjacent cour cells for a rempart tile
        candidates = []
        for cx in range(4):
            for cy in range(4):
                if game.board.cour[cy][cx] is not None:
                    candidates.append((cx, cy))
        if candidates:
            cx, cy = random.choice(candidates)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
            game.board.cour[cy][cx] = None

    @staticmethod
    def soldat_effect(game, player, card, position):
        """Le quatrième soldat arrivant sur un rempart renvoie l'engin de siège qui se trouve en face."""
        soldat_count = sum(
            1 for (tx, ty), tile in game.board.tiles.items()
            if tile['type'] == 'rempart' and tile['card'] and 'Soldat' in tile['card'].nom
        )
        if soldat_count >= 4:
            for ext_pos, ext_card in list(game.board.exterieur.items()):
                if ext_card and 'Engin' in ext_card.nom:
                    del game.board.exterieur[ext_pos]
                    CardEffects._return_card(game, ext_card)
                    return

    # Rouge effects
    @staticmethod
    def marchand_effect(game, player, card, position):
        """Le marchand vous fait effectuer une troisième action. Remplacez 3 pions d'autres joueurs."""
        # Grant extra action and place 3 pions
        player.extra_actions = (getattr(player, 'extra_actions', 0) or 0) + 1
    
    @staticmethod
    def roi_effect(game, player, card, position):
        """Le roi renvoie du château n'importe quelle autre carte."""
        cards_on_board = [
            (cx, cy) for cy in range(4) for cx in range(4)
            if game.board.cour[cy][cx] and game.board.cour[cy][cx] is not card
        ]
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
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
        cards_on_board = [
            (cx, cy) for cy in range(4) for cx in range(4)
            if game.board.cour[cy][cx] and game.board.cour[cy][cx] is not card
        ]
        if cards_on_board:
            cx, cy = random.choice(cards_on_board)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
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
        """Chaque joueur pioche une carte au hasard du jeu de son voisin de droite (simultané)."""
        # Determine what each player will steal BEFORE any removal
        to_steal = []
        for i, p in enumerate(game.players):
            next_idx = (i + 1) % len(game.players)
            other = game.players[next_idx]
            stolen = random.choice(other.hand) if other.hand else None
            to_steal.append((p, stolen, other))
        # Apply simultaneously: remove then give
        for p, stolen, other in to_steal:
            if stolen is not None and stolen in other.hand:
                other.hand.remove(stolen)
                p.hand.append(stolen)
    
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
        occupied = [(pos, tile) for pos, tile in game.board.tiles.items() if tile['card']]
        if occupied:
            pos, tile = random.choice(occupied)
            removed = tile['card']
            tile['card'] = None
            CardEffects._return_card(game, removed)

    @staticmethod
    def fee_effect(game, player, card, position):
        """La fée attire hors les murs l'un des personnages se trouvant dans le château."""
        cards_in_cour = [
            (cx, cy) for cy in range(4) for cx in range(4)
            if game.board.cour[cy][cx]
        ]
        if cards_in_cour:
            cx, cy = random.choice(cards_in_cour)
            pulled = game.board.cour[cy][cx]
            game.board.cour[cy][cx] = None
            # Place in exterior at a free position
            ext_x = 6
            while (ext_x, 0) in game.board.exterieur:
                ext_x += 1
            game.board.exterieur[(ext_x, 0)] = pulled

    @staticmethod
    def enchanteur_effect(game, player, card, position):
        """L'enchanteur renvoie la dernière carte à avoir été placée (avant lui)."""
        prev = game.previous_placed_card
        if prev:
            # Remove it from wherever it is on the board
            for cy in range(4):
                for cx in range(4):
                    if game.board.cour[cy][cx] is prev:
                        game.board.cour[cy][cx] = None
                        CardEffects._return_card(game, prev)
                        game.previous_placed_card = None
                        return
            for (tx, ty), tile in game.board.tiles.items():
                if tile['card'] is prev:
                    tile['card'] = None
                    CardEffects._return_card(game, prev)
                    game.previous_placed_card = None
                    return
            for ext_pos, ext_card in list(game.board.exterieur.items()):
                if ext_card is prev:
                    del game.board.exterieur[ext_pos]
                    CardEffects._return_card(game, prev)
                    game.previous_placed_card = None
                    return

    @staticmethod
    def engin_siege_effect(game, player, card, position):
        """Le quatrième engin de siège renvoie tous les soldats se trouvant sur les remparts."""
        engine_count = sum(
            1 for ext_card in game.board.exterieur.values()
            if ext_card and 'Engin' in ext_card.nom
        )
        if engine_count >= 4:
            for (tx, ty), tile in list(game.board.tiles.items()):
                if tile['type'] == 'rempart' and tile['card']:
                    if not getattr(tile['card'], 'protected', False):
                        CardEffects._return_card(game, tile['card'])
                        tile['card'] = None

    @staticmethod
    def dragon_effect(game, player, card, position):
        """Le dragon renvoie une carte hors les murs et une carte dans une tour ou rempart."""
        if game.board.exterieur:
            ext_pos = next(iter(game.board.exterieur))
            removed = game.board.exterieur.pop(ext_pos)
            if removed:
                CardEffects._return_card(game, removed)

        occupied_tiles = [(pos, tile) for pos, tile in game.board.tiles.items() if tile['card']]
        if occupied_tiles:
            pos, tile = random.choice(occupied_tiles)
            removed = tile['card']
            tile['card'] = None
            CardEffects._return_card(game, removed)



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
