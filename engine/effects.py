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
        """Return a card to its owner's hand, or to exchange if owner unknown.
        If the card was marked 'stolen' (pion removed by Voleur), it always goes to exchange."""
        if getattr(card, 'stolen', False):
            game.exchange.append(card)
            card.stolen = False
            return
        owner = getattr(card, 'pion_owner', None)
        if owner is not None:
            owner.hand.append(card)
        else:
            game.exchange.append(card)

    @staticmethod
    def _pending_pick_return(game, player, effect_name, zone, valid_positions, next_action=None):
        """Set pending_action so the human player can interactively select a card to return."""
        game.pending_action = {
            'type': 'pick_return',
            'effect': effect_name,
            'zone': zone,          # 'cour' | 'ext' | 'tile'
            'valid': valid_positions,
            'player': player,
            'next': next_action,   # chained pick_return dict for Dragon (2nd pick)
        }

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
        # Find soldiers on remparts
        soldiers = [pos for pos, tile in game.board.tiles.items()
                    if tile['type'] == 'rempart' and tile['card']
                    and 'Soldat' in tile['card'].nom]
        if not soldiers:
            return  # Nothing to do
        if not player.is_human:
            # AI: move first soldier to first free rempart (original logic)
            for src in soldiers:
                soldat = game.board.tiles[src]['card']
                for (nx, ny), ntile in game.board.tiles.items():
                    if ntile['type'] == 'rempart' and ntile['card'] is None and (nx, ny) != src:
                        ntile['card'] = soldat
                        game.board.tiles[src]['card'] = None
                        return
                # No free rempart: return to owner
                CardEffects._return_card(game, soldat)
                game.board.tiles[src]['card'] = None
                return
        # Human: request interactive selection
        game.pending_action = {
            'type': 'guetteur',
            'step': 1,   # step 1 = select soldier source; step 2 = select destination
            'player': player,
            'source_pos': None,
            'valid_sources': soldiers,
        }

    @staticmethod
    def magicien_effect(game, player, card, position):
        """Le magicien renvoie n'importe quelle carte et l'ajoute aux cartes de l'échange."""
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                c = game.board.cour[cy][cx]
                if c and not getattr(c, 'protected', False):
                    cards_on_board.append((cx, cy))
        if not cards_on_board:
            return
        if not player.is_human:
            cx, cy = random.choice(cards_on_board)
            card_to_move = game.board.cour[cy][cx]
            CardEffects._return_card(game, card_to_move)
            game.board.cour[cy][cx] = None
            return
        CardEffects._pending_pick_return(game, player, 'Magicien', 'cour', cards_on_board)

    @staticmethod
    def archer_effect(game, player, card, position):
        """L'archer renvoie une carte se trouvant hors les murs."""
        ext_positions = list(game.board.exterieur.keys())
        if not ext_positions:
            return
        if not player.is_human:
            ext_pos = ext_positions[0]
            removed = game.board.exterieur.pop(ext_pos)
            if removed:
                CardEffects._return_card(game, removed)
            return
        CardEffects._pending_pick_return(game, player, 'Archer', 'ext', ext_positions)

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
        candidates = [
            (cx, cy) for cx in range(4) for cy in range(4)
            if game.board.cour[cy][cx] is not None
            and not getattr(game.board.cour[cy][cx], 'protected', False)
        ]
        if not candidates:
            return
        if not player.is_human:
            cx, cy = random.choice(candidates)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
            game.board.cour[cy][cx] = None
            return
        CardEffects._pending_pick_return(game, player, 'Traitre', 'cour', candidates)

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
            and not getattr(game.board.cour[cy][cx], 'protected', False)
        ]
        if not cards_on_board:
            return
        if not player.is_human:
            cx, cy = random.choice(cards_on_board)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
            game.board.cour[cy][cx] = None
            return
        CardEffects._pending_pick_return(game, player, 'Roi', 'cour', cards_on_board)
    
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
            and not getattr(game.board.cour[cy][cx], 'protected', False)
        ]
        if not cards_on_board:
            return
        if not player.is_human:
            cx, cy = random.choice(cards_on_board)
            removed = game.board.cour[cy][cx]
            CardEffects._return_card(game, removed)
            game.board.cour[cy][cx] = None
            return
        CardEffects._pending_pick_return(game, player, 'Reine', 'cour', cards_on_board)
    
    @staticmethod
    def princesse_effect(game, player, card, position):
        """La princesse déplace un chevalier."""
        for cy in range(4):
            for cx in range(4):
                c = game.board.cour[cy][cx]
                if c and "Chevalier" in c.nom:
                    CardEffects._return_card(game, c)
                    game.board.cour[cy][cx] = None
                    return
    
    @staticmethod
    def prince_effect(game, player, card, position):
        """Si le roi est absent, les cartes devant être placées à côté du roi peuvent être placées à côté du prince."""
        # Mark card as king-adjacent substitute
        card.king_substitute = True
    
    @staticmethod
    @staticmethod
    def intrigant_effect(game, player, card, position):
        """L'intrigant échange les pions (positions) de deux autres cartes."""
        cards_on_board = []
        for cy in range(4):
            for cx in range(4):
                if game.board.cour[cy][cx] and game.board.cour[cy][cx] is not card:
                    cards_on_board.append((cx, cy))
        if len(cards_on_board) < 2:
            return
        if not player.is_human:
            idx1, idx2 = random.sample(range(len(cards_on_board)), 2)
            x1, y1 = cards_on_board[idx1]
            x2, y2 = cards_on_board[idx2]
            game.board.cour[y1][x1], game.board.cour[y2][x2] = game.board.cour[y2][x2], game.board.cour[y1][x1]
            return
        # Human: interactive 2-step selection
        game.pending_action = {
            'type': 'intrigant',
            'step': 1,
            'player': player,
            'valid': cards_on_board,
            'first_pos': None,
        }
    
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
        """Le voleur retire le pion d'une carte voisine non protégée. Si elle est renvoyée, elle va à l'échange."""
        x, y = position
        valid = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                neighbor = game.board.cour[y][nx]
                if getattr(neighbor, 'pion_owner', None) and not getattr(neighbor, 'protected', False):
                    valid.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                neighbor = game.board.cour[ny][x]
                if getattr(neighbor, 'pion_owner', None) and not getattr(neighbor, 'protected', False):
                    valid.append((x, ny))
        if not valid:
            return
        if not player.is_human:
            cx2, cy2 = valid[0]
            target = game.board.cour[cy2][cx2]
            target.pion_owner = None
            target.stolen = True
            return
        # Human: select which neighbor to steal pion from
        game.pending_action = {
            'type': 'voleur',
            'player': player,
            'valid': valid,
        }
    
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
        """Le prêtre protège les cartes voisines appartenant au même joueur (même pion_owner)."""
        x, y = position
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4:
                neighbor = game.board.cour[y][nx]
                if neighbor and getattr(neighbor, 'pion_owner', None) is player:
                    neighbor.protected = True
                    neighbor.protected_by = card
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4:
                neighbor = game.board.cour[ny][x]
                if neighbor and getattr(neighbor, 'pion_owner', None) is player:
                    neighbor.protected = True
                    neighbor.protected_by = card
    
    @staticmethod
    def dame_compagnie_effect(game, player, card, position):
        """La dame de compagnie renvoie de la cour un personnage masculin voisin."""
        x, y = position
        male_cards = ["Roi", "Prince", "Chevalier"]
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if any(m in game.board.cour[y][nx].nom for m in male_cards):
                    CardEffects._return_card(game, game.board.cour[y][nx])
                    game.board.cour[y][nx] = None
                    return
    
    @staticmethod
    def courtisan_effect(game, player, card, position):
        """Le courtisan renvoie du château une carte se trouvant sur une case voisine."""
        x, y = position
        valid = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if not getattr(game.board.cour[y][nx], 'protected', False):
                    valid.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                if not getattr(game.board.cour[ny][x], 'protected', False):
                    valid.append((x, ny))
        if not valid:
            return
        if not player.is_human:
            cx2, cy2 = valid[0]
            CardEffects._return_card(game, game.board.cour[cy2][cx2])
            game.board.cour[cy2][cx2] = None
            return
        CardEffects._pending_pick_return(game, player, 'Courtisan', 'cour', valid)
    
    @staticmethod
    def assassin_effect(game, player, card, position):
        """L'assassin retire définitivement du jeu n'importe quelle carte (sauf le roi) voisine."""
        x, y = position
        valid = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                target = game.board.cour[y][nx]
                if "Roi" not in target.nom and not getattr(target, 'protected', False):
                    valid.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                target = game.board.cour[ny][x]
                if "Roi" not in target.nom and not getattr(target, 'protected', False):
                    valid.append((x, ny))
        if not valid:
            return
        if not player.is_human:
            cx2, cy2 = valid[0]
            game.board.cour[cy2][cx2] = None  # permanently remove
            return
        # Human: select target to permanently eliminate
        game.pending_action = {
            'type': 'assassin',
            'player': player,
            'valid': valid,
        }
    
    @staticmethod
    def conseiller_roi_effect(game, player, card, position):
        """Le conseiller du roi met en jeu l'une des cartes se trouvant dans l'échange."""
        if not game.exchange:
            return
        if not player.is_human:
            # AI: take first exchange card and put in first free cour cell
            card_from_exchange = game.exchange.pop(0)
            for cy in range(4):
                for cx in range(4):
                    if game.board.cour[cy][cx] is None:
                        game.board.cour[cy][cx] = card_from_exchange
                        return
            return
        # Human: request interactive selection
        game.pending_action = {
            'type': 'conseiller',
            'step': 1,   # step 1 = pick exchange card; step 2 = pick board position
            'player': player,
            'exchange_idx': None,
            'dragging_card': None,
        }
    
    @staticmethod
    def favorite_effect(game, player, card, position):
        """La favorite déplace librement le roi et un chevalier."""
        # Build valid sources: Roi + Chevalier(s) on cour
        valid = []
        for cy in range(4):
            for cx in range(4):
                c = game.board.cour[cy][cx]
                if c and ("Roi" in c.nom or "Chevalier" in c.nom):
                    if not getattr(c, 'protected', False):
                        valid.append((cx, cy))
        if not valid:
            return
        if not player.is_human:
            for src in valid:
                sx, sy = src
                src_card = game.board.cour[sy][sx]
                for ty in range(4):
                    for tx in range(4):
                        if (tx, ty) != (sx, sy) and game.board.cour[ty][tx] is None:
                            game.board.cour[ty][tx] = src_card
                            game.board.cour[sy][sx] = None
                            break
                    else:
                        continue
                    break
            return
        # Human: move up to 2 pieces; start with step 1 (pick first card)
        game.pending_action = {
            'type': 'favorite',
            'step': 1,
            'player': player,
            'valid': valid,
            'moves_left': 2,
            'source_pos': None,
        }
    
    @staticmethod
    def prince_charmant_effect(game, player, card, position):
        """Le prince charmant déplace un personnage féminin."""
        female_names = ["Reine", "Princesse", "Sorciere", "Fee"]
        females = [(cx, cy) for cy in range(4) for cx in range(4)
                   if game.board.cour[cy][cx]
                   and any(f in game.board.cour[cy][cx].nom for f in female_names)]
        if not females:
            return
        if not player.is_human:
            # AI: move first female to first free cour cell
            fx, fy = females[0]
            female_card = game.board.cour[fy][fx]
            for ty in range(4):
                for tx in range(4):
                    if (tx, ty) != (fx, fy) and game.board.cour[ty][tx] is None:
                        game.board.cour[ty][tx] = female_card
                        game.board.cour[fy][fx] = None
                        return
            return
        # Human: request interactive selection
        game.pending_action = {
            'type': 'prince_charmant',
            'step': 1,   # step 1 = select female; step 2 = select destination
            'player': player,
            'valid_sources': females,
            'source_pos': None,
        }
    
    @staticmethod
    def chevalier_noir_effect(game, player, card, position):
        """Le chevalier noir renvoie un chevalier se trouvant sur une case voisine."""
        x, y = position
        valid = []
        for dx in [-1, 1]:
            nx = x + dx
            if 0 <= nx < 4 and game.board.cour[y][nx]:
                if "Chevalier" in game.board.cour[y][nx].nom and not getattr(game.board.cour[y][nx], 'protected', False):
                    valid.append((nx, y))
        for dy in [-1, 1]:
            ny = y + dy
            if 0 <= ny < 4 and game.board.cour[ny][x]:
                if "Chevalier" in game.board.cour[ny][x].nom and not getattr(game.board.cour[ny][x], 'protected', False):
                    valid.append((x, ny))
        if not valid:
            return
        if not player.is_human:
            cx2, cy2 = valid[0]
            CardEffects._return_card(game, game.board.cour[cy2][cx2])
            game.board.cour[cy2][cx2] = None
            return
        CardEffects._pending_pick_return(game, player, 'Chevalier_noir', 'cour', valid)

    # Vert effects
    @staticmethod
    def barbare_effect(game, player, card, position):
        """Le barbare renvoie une carte se trouvant dans une tour ou sur un rempart."""
        occupied = [(pos, tile) for pos, tile in game.board.tiles.items() if tile['card']]
        if not occupied:
            return
        if not player.is_human:
            pos, tile = random.choice(occupied)
            removed = tile['card']
            tile['card'] = None
            CardEffects._return_card(game, removed)
            return
        # Human: pick which tile card to return
        valid_positions = [pos for pos, tile in occupied]
        game.pending_action = {
            'type': 'pick_return',
            'effect': 'Barbare',
            'zone': 'tile',
            'valid': valid_positions,
            'player': player,
            'next': None,
        }

    @staticmethod
    def fee_effect(game, player, card, position):
        """La fée attire hors les murs l'un des personnages se trouvant dans le château."""
        cards_in_cour = [
            (cx, cy) for cy in range(4) for cx in range(4)
            if game.board.cour[cy][cx]
        ]
        if not cards_in_cour:
            return
        if not player.is_human:
            cx2, cy2 = random.choice(cards_in_cour)
            pulled = game.board.cour[cy2][cx2]
            game.board.cour[cy2][cx2] = None
            ext_x = 6
            while (ext_x, 0) in game.board.exterieur:
                ext_x += 1
            game.board.exterieur[(ext_x, 0)] = pulled
            return
        # Human: select which cour card to attract outside
        game.pending_action = {
            'type': 'fee',
            'player': player,
            'valid': cards_in_cour,
        }

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
        """Le quatrième engin de siège renvoie tous les soldats se trouvant sur les remparts.
        Les soldats protégés par un capitaine restent en place, mais le capitaine est renvoyé.
        Le capitaine ne se protège pas lui-même."""
        engine_count = sum(
            1 for ext_card in game.board.exterieur.values()
            if ext_card and 'Engin' in ext_card.nom
        )
        if engine_count < 4:
            return
        # Return captains first (they do not protect themselves)
        for (tx, ty), tile in list(game.board.tiles.items()):
            if tile['type'] == 'rempart' and tile['card'] and 'Capitaine' in tile['card'].nom:
                CardEffects._return_card(game, tile['card'])
                tile['card'] = None
        # Return unprotected soldiers; protected ones stay but lose protection (captain gone)
        for (tx, ty), tile in list(game.board.tiles.items()):
            if tile['type'] == 'rempart' and tile['card']:
                if getattr(tile['card'], 'protected', False):
                    tile['card'].protected = False   # captain gone, protection lifted for future
                else:
                    CardEffects._return_card(game, tile['card'])
                    tile['card'] = None

    @staticmethod
    def dragon_effect(game, player, card, position):
        """Le dragon renvoie une carte hors les murs et une carte dans une tour ou rempart.
        Le dragon ne peut pas se renvoyer lui-même."""
        # Exclude the dragon card itself from ext candidates
        ext_positions = [pos for pos, c in game.board.exterieur.items() if c is not card]
        tile_positions = [pos for pos, tile in game.board.tiles.items() if tile['card']]

        if not player.is_human:
            if ext_positions:
                ext_pos = ext_positions[0]
                removed = game.board.exterieur.pop(ext_pos)
                if removed:
                    CardEffects._return_card(game, removed)
            if tile_positions:
                pos = random.choice(tile_positions)
                removed = game.board.tiles[pos]['card']
                game.board.tiles[pos]['card'] = None
                CardEffects._return_card(game, removed)
            return

        # Human: chain two interactive picks (ext first, then tile)
        next_action = None
        if tile_positions:
            next_action = {
                'type': 'pick_return',
                'effect': 'Dragon',
                'zone': 'tile',
                'valid': tile_positions,
                'player': player,
                'next': None,
            }
        if ext_positions:
            CardEffects._pending_pick_return(game, player, 'Dragon', 'ext', ext_positions, next_action=next_action)
        elif next_action:
            game.pending_action = next_action



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
