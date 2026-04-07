import pygame

# ============================================================================
# LAYOUT CONSTANTS - Positionnement systématique des panneaux
# ============================================================================
SCREEN_W, SCREEN_H = 2400, 900  # Wider, shorter for better layout

# Panneaux horizontaux (de gauche à droite)
PANEL_DECKS_W = 100         # Panneau des pioches à gauche
PANEL_CASTLE_W = 700        # Château central (4x4 cour + tiles)
PANEL_EXCHANGE_W = 400      # Panneau d'échange
PANEL_LOG_W = 600           # Journal des actions
PANEL_HAND_W = 600          # Main du joueur

# Vérification: 100 + 700 + 400 + 600 = 1800 < 2400 ✓

# Positions X (début de chaque panneau)
DECKS_X = 0
CASTLE_X = DECKS_X + PANEL_DECKS_W
EXCHANGE_X = CASTLE_X + PANEL_CASTLE_W
LOG_X = EXCHANGE_X + PANEL_EXCHANGE_W
HAND_X = LOG_X + PANEL_LOG_W

# Hauteurs et marges
TOP_MARGIN = 85
BOTTOM_MARGIN = 70
CONTENT_H = SCREEN_H - TOP_MARGIN - BOTTOM_MARGIN

# Taille des cellules du château
CASTLE_CELL_SIZE = 140

class CastelWindow:
    def __init__(self, game):
        self.game = game
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        pygame.display.set_caption("Castel - Jeu de Plateau")
        self.clock = pygame.time.Clock()
        self.running = True
        self.font = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 14)
        self.font_title = pygame.font.Font(None, 28)
        self.game.board.load_images()  # Load images after pygame.init
        self.selected_card = None
        self.ai_delay = 60  # Frames de délai pour les tours IA
        self.action_log = []  # Log des actions
        self.max_log_lines = 8  # Réduit de 15 à 8
        self.mouse_pos = (0, 0)  # Position de la souris
        self.tooltip_card = None  # Carte sur laquelle on hover
        self.dragging_card = None  # Carte en cours de drag
        self.drag_offset = (0, 0)  # Offset pour le drag
        self.exchange_mode = False  # Mode d'échange actif
        self.selected_hand_card_idx = None  # Index de la carte sélectionnée en main
        self.selected_exchange_card_idx = None  # Index de la carte sélectionnée à l'échange
        self.action_buttons = {}  # Bouttons d'action
        self._create_action_buttons()

    def add_log(self, message):
        """Ajouter un message au log des actions."""
        self.action_log.append(message)
        if len(self.action_log) > self.max_log_lines:
            self.action_log.pop(0)

    def _get_card_location_color(self, card):
        """Retourner la couleur basée sur le lieu de placement de la carte."""
        # Vérifier dans le CSV la couleur de la carte
        if hasattr(card, 'couleur'):
            couleur = card.couleur.lower()
            if couleur == 'bleu':
                return (100, 150, 200)  # Tours - Bleu
            elif couleur == 'orange':
                return (200, 150, 100)  # Remparts - Orange
            elif couleur == 'rouge':
                return (200, 100, 100)  # Cour - Rouge
            elif couleur == 'vert':
                return (100, 200, 100)  # Extérieur - Vert
            elif couleur == 'violet':
                return (180, 100, 200)  # Chevaliers - Violet
        return (150, 150, 150)  # Défaut

    def _get_card_zone_name(self, card):
        """Get the zone name where a card should be placed"""
        lieu = getattr(card, 'lieu', '').lower()
        if 'cour' in lieu:
            return 'cour'
        elif 'tour' in lieu:
            return 'tour'
        elif 'rempart' in lieu:
            return 'rempart'
        elif 'extérieur' in lieu or 'chevalier' not in lieu:
            return 'exterieur'
        return None

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            # Track mouse position for tooltips
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                self._update_tooltip()
            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                current_player = self.game.players[self.game.current_player]
                if current_player.is_human:
                    x, y = event.pos

                    # Check button clicks
                    if self.action_buttons['draw'].collidepoint(x, y):
                        if current_player.deck:
                            self.game.draw_card(current_player)
                            self.add_log(f"J{self.game.current_player + 1} a tiré une carte")
                            if self.game.advance_turn_if_done():
                                self.add_log(f"Tour suivant: J{self.game.current_player + 1}")
                        return

                    if self.action_buttons['exchange'].collidepoint(x, y):
                        # Toggle exchange mode
                        if current_player.hand and self.game.exchange:
                            self.exchange_mode = not self.exchange_mode
                            if self.exchange_mode:
                                self.add_log("Mode échange: Cliquez sur une carte en main")
                                self.selected_hand_card_idx = None
                                self.selected_exchange_card_idx = None
                            else:
                                self.add_log("Mode échange désactivé")
                        return

                    if self.action_buttons['skip'].collidepoint(x, y):
                        # Skip current action (counts as an action)
                        self.game.actions_remaining -= 1
                        if self.game.advance_turn_if_done():
                            self.add_log(f"Tour suivant: J{self.game.current_player + 1}")
                        else:
                            self.add_log("Action passée")
                        self.exchange_mode = False
                        return

                    # Handle exchange mode clicks
                    if self.exchange_mode:
                        # Check if clicked on exchange cards
                        exchange_x = EXCHANGE_X + 10
                        exchange_y = TOP_MARGIN + 20
                        exchange_card_size = 80

                        for i in range(min(8, len(self.game.exchange))):
                            card_y = exchange_y + i * (exchange_card_size + 10)
                            if exchange_x <= x <= exchange_x + exchange_card_size + 5 and card_y <= y <= card_y + exchange_card_size + 5:
                                self.selected_exchange_card_idx = i
                                self.add_log(f"Carte d'échange sélectionnée: {self.game.exchange[i].nom}")
                                return

                        # Check if clicked on hand cards in exchange mode
                        # Vérifier si le clic est dans la zone de la main
                        if x >= HAND_X and x <= HAND_X + PANEL_HAND_W and y >= TOP_MARGIN and y <= TOP_MARGIN + CONTENT_H:
                            # Calculer quel index de carte a été cliqué
                            card_size = 80
                            cards_per_row = 2
                            local_x = x - (HAND_X + 10)
                            local_y = y - (TOP_MARGIN + 20)
                            col = local_x // (card_size + 10)
                            row = local_y // (card_size + 10)
                            index = row * cards_per_row + col
                            
                            if 0 <= index < len(current_player.hand):
                                self.selected_hand_card_idx = index
                                self.add_log(f"Carte en main sélectionnée: {current_player.hand[index].nom}")

                                # If both cards are selected, perform exchange
                                if self.selected_exchange_card_idx is not None:
                                    try:
                                        self.game.exchange_card(current_player, self.selected_hand_card_idx, self.selected_exchange_card_idx)
                                        self.add_log(f"✓ Échange effectué!")
                                        self.exchange_mode = False
                                        self.selected_hand_card_idx = None
                                        self.selected_exchange_card_idx = None
                                        if self.game.advance_turn_if_done():
                                            self.add_log(f"Tour suivant: J{self.game.current_player + 1}")
                                    except Exception as e:
                                        self.add_log(f"❌ Échange impossible: {str(e)}")
                            return

                    # Handle hand card selection/drag (not in exchange mode)
                    if not self.exchange_mode and x >= HAND_X and x <= HAND_X + PANEL_HAND_W and y >= TOP_MARGIN and y <= TOP_MARGIN + CONTENT_H:
                        # Calculer quel index de carte a été cliqué
                        card_size = 80
                        cards_per_row = 2
                        local_x = x - (HAND_X + 10)
                        local_y = y - (TOP_MARGIN + 20)
                        col = local_x // (card_size + 10)
                        row = local_y // (card_size + 10)
                        index = row * cards_per_row + col
                        
                        if 0 <= index < len(current_player.hand):
                            card = current_player.hand[index]
                            self.selected_card = card
                            self.dragging_card = card
                            # Calculate offset from mouse to card center
                            card_x = HAND_X + 10 + col * (card_size + 10) + card_size // 2
                            card_y = TOP_MARGIN + 20 + row * (card_size + 10) + card_size // 2
                            self.drag_offset = (event.pos[0] - card_x, event.pos[1] - card_y)
                            self.add_log(f"Carte sélectionnée: {card.nom}")

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # Left mouse button
                if self.dragging_card:
                    x, y = event.pos
                    cour_start_x = CASTLE_X + 10
                    cour_start_y = TOP_MARGIN + 20
                    cell_size = CASTLE_CELL_SIZE
                    placed = False
                    current_player = self.game.players[self.game.current_player]

                    # Check courtyard placement
                    for cx in range(4):
                        for cy in range(4):
                            px = cour_start_x + cx * cell_size
                            py = cour_start_y + cy * cell_size
                            if px <= x <= px + cell_size and py <= y <= py + cell_size:
                                if self.game.board.cour[cy][cx] is None:
                                    position = (cx, cy)
                                    if self._is_valid_placement(self.dragging_card, position):
                                        result = self.game.place_card(current_player, self.dragging_card, position)
                                        if result == 'win':
                                            self.add_log(f"🏆 Joueur {self.game.current_player + 1} a gagné!")
                                        elif result:
                                            self.add_log(f"Carte placée: {self.dragging_card.nom}")
                                            self.game.advance_turn_if_done()
                                        placed = True
                                    else:
                                        self.add_log(f"❌ Placement invalide pour {self.dragging_card.nom}")
                                else:
                                    self.add_log(f"❌ Case occupée!")
                                break

                    # Check tile placement (towers and walls)
                    if not placed:
                        for (tx, ty), tile in self.game.board.tiles.items():
                            px = cour_start_x + tx * cell_size
                            py = cour_start_y + ty * cell_size
                            if px <= x <= px + cell_size and py <= y <= py + cell_size:
                                if tile['card'] is None:
                                    position = (tx, ty)
                                    if self._is_valid_placement(self.dragging_card, position):
                                        result = self.game.place_card(current_player, self.dragging_card, position)
                                        if result == 'win':
                                            self.add_log(f"🏆 Joueur {self.game.current_player + 1} a gagné!")
                                        elif result:
                                            self.add_log(f"Carte placée: {self.dragging_card.nom} sur {tile['type']}")
                                            self.game.advance_turn_if_done()
                                        placed = True
                                    else:
                                        self.add_log(f"❌ Placement invalide pour {self.dragging_card.nom}")
                                else:
                                    self.add_log(f"❌ {tile['type']} occupé!")
                                break

                    if not placed:
                        self.add_log(f"❌ Placement annulé")
                    self.dragging_card = None
                    self.selected_card = None

    def update(self):
        current_player = self.game.players[self.game.current_player]
        if not current_player.is_human:
            # AI turn with delay
            self.ai_delay -= 1
            if self.ai_delay <= 0:
                action = current_player.choose_action(self.game)
                if action[0] == 'place':
                    _, card, position = action
                    result = self.game.place_card(current_player, card, position)
                    if result == 'win':
                        self.add_log(f"🏆 IA {self.game.current_player + 1} a gagné!")
                    elif result:
                        self.add_log(f"IA joue: {card.nom} à {position}")
                    else:
                        # Placement rejected — fall back to draw or exchange
                        self.add_log(f"IA ne peut pas placer {card.nom}, pioche/échange")
                        if current_player.deck:
                            self.game.draw_card(current_player)
                        elif self.game.exchange and current_player.hand:
                            self.game.exchange_card(current_player, 0, 0)
                        else:
                            self.game.actions_remaining -= 1  # force skip
                elif action[0] == 'draw':
                    self.game.draw_card(current_player)
                    self.add_log(f"IA {self.game.current_player + 1} pioche")
                elif action[0] == 'exchange':
                    _, hi, ei = action
                    self.game.exchange_card(current_player, hi, ei)
                    self.add_log(f"IA {self.game.current_player + 1} échange")
                else:
                    # Truly stuck: force skip this action
                    self.game.actions_remaining -= 1
                    self.add_log(f"IA {self.game.current_player + 1} passe")

                if self.game.advance_turn_if_done():
                    self.ai_delay = 60
                else:
                    self.ai_delay = 30  # Same player still has actions

    def _update_tooltip(self):
        """Mettre à jour la carte sur laquelle on hover pour les tooltips."""
        mx, my = self.mouse_pos
        self.tooltip_card = None

        # Check hand cards
        if self.game.players[self.game.current_player].is_human:
            if mx >= HAND_X and mx <= HAND_X + PANEL_HAND_W and my >= TOP_MARGIN and my <= TOP_MARGIN + CONTENT_H:
                card_size = 80
                cards_per_row = 2
                hand_x = HAND_X + 10
                hand_y = TOP_MARGIN + 20
                local_x = mx - hand_x
                local_y = my - hand_y
                col = local_x // (card_size + 10)
                row = local_y // (card_size + 10)
                index = row * cards_per_row + col
                if 0 <= index < len(self.game.players[self.game.current_player].hand):
                    self.tooltip_card = self.game.players[self.game.current_player].hand[index]
                    return

        # Check cour cards
        cour_start_x = CASTLE_X + 10
        cour_start_y = TOP_MARGIN + 20
        cell_size = CASTLE_CELL_SIZE
        for cy in range(4):
            for cx in range(4):
                px = cour_start_x + cx * cell_size
                py = cour_start_y + cy * cell_size
                if px <= mx <= px + cell_size and py <= my <= py + cell_size:
                    if self.game.board.cour[cy][cx]:
                        self.tooltip_card = self.game.board.cour[cy][cx]
                        return

    def _draw_tooltip(self):
        """Dessiner l'info-bulle si une carte est en hover."""
        if not self.tooltip_card:
            return

        mx, my = self.mouse_pos

        # Préparer le texte de l'info-bulle
        lines = []
        lines.append(f"Carte: {self.tooltip_card.nom}")
        lines.append(f"Couleur: {getattr(self.tooltip_card, 'couleur', 'Inconnue')}")
        lines.append(f"Lieu: {getattr(self.tooltip_card, 'lieu', 'Inconnu')}")
        lines.append(f"Condition: {getattr(self.tooltip_card, 'condition', 'Aucune')}")
        lines.append(f"Action: {getattr(self.tooltip_card, 'action', 'Aucune')}")

        # Calculer la taille de l'info-bulle
        max_width = max(len(line) for line in lines) * 8
        tooltip_w = max(300, max_width)
        tooltip_h = len(lines) * 20 + 20

        # Positionner l'info-bulle près de la souris
        tooltip_x = mx + 15
        tooltip_y = my + 15

        # Ajuster si l'info-bulle dépasse l'écran
        if tooltip_x + tooltip_w > SCREEN_W:
            tooltip_x = mx - tooltip_w - 15
        if tooltip_y + tooltip_h > SCREEN_H:
            tooltip_y = my - tooltip_h - 15

        # Dessiner le fond de l'info-bulle
        pygame.draw.rect(self.screen, (50, 50, 70), (tooltip_x, tooltip_y, tooltip_w, tooltip_h))
        pygame.draw.rect(self.screen, (200, 200, 200), (tooltip_x, tooltip_y, tooltip_w, tooltip_h), 2)

        # Dessiner le texte
        for i, line in enumerate(lines):
            text = self.font_small.render(line, True, (255, 255, 255))
            self.screen.blit(text, (tooltip_x + 10, tooltip_y + 10 + i * 20))

    def _is_valid_placement(self, card, position):
        """Vérifier si le placement de la carte est valide selon son lieu."""
        lieu = getattr(card, 'lieu', '').lower()

        # Normaliser le texte pour gérer les accents mal encodés
        # Remplacer les variantes courantes
        lieu = lieu.replace('á', 'a').replace('à', 'a').replace('é', 'e')
        lieu = lieu.replace('è', 'e').replace('ê', 'e').replace('ù', 'u')
        lieu = lieu.replace('û', 'u').replace('ô', 'o').replace('ç', 'c')
        # Supprimer les espaces multiples
        lieu = ' '.join(lieu.split())

        if isinstance(position, tuple) and len(position) == 2:
            x, y = position
            if 0 <= x < 4 and 0 <= y < 4:
                # Courtyard
                return 'cour' in lieu
            elif (x, y) in self.game.board.tiles:
                # Tile (tower or wall)
                tile = self.game.board.tiles[(x, y)]
                if tile['type'] == 'tour':
                    return 'tour' in lieu
                elif tile['type'] == 'rempart':
                    return 'rempart' in lieu
                elif tile.get('card') is not None:
                    # Knight can be placed on another card
                    return 'autre carte' in lieu
            else:
                # Exterior
                return 'murs' in lieu or 'exterieur' in lieu

        return False

    def _create_action_buttons(self):
        """Create action buttons for human player"""
        self.action_buttons = {
            'draw': pygame.Rect(20, SCREEN_H - 60, 100, 40),
            'exchange': pygame.Rect(130, SCREEN_H - 60, 100, 40),
            'skip': pygame.Rect(240, SCREEN_H - 60, 100, 40),
        }

    def draw(self):
        self.screen.fill((20, 20, 30))

        # Draw title
        title = self.font_title.render(f"Castel - Tour {self.game.turn}", True, (200, 200, 200))
        self.screen.blit(title, (20, 20))

        # Draw current player
        current_player = self.game.players[self.game.current_player]
        player_text = f"Joueur: {'HUMAIN' if current_player.is_human else 'IA'} ({self.game.current_player + 1}/{len(self.game.players)}) - Actions: {self.game.actions_remaining}/2"
        player_label = self.font.render(player_text, True, (0, 255, 0) if current_player.is_human else (255, 100, 100))
        self.screen.blit(player_label, (20, 55))

        # ====================================================================
        # SECTION 1: PIOCHES (à gauche)
        # ====================================================================
        self._draw_decks_panel(current_player)

        # ====================================================================
        # SECTION 2: CHÂTEAU (centre-gauche)
        # ====================================================================
        self._draw_castle_panel(current_player)

        # ====================================================================
        # SECTION 3: ÉCHANGE (centre)
        # ====================================================================
        self._draw_exchange_panel()

        # ====================================================================
        # SECTION 4: JOURNAL (centre-droit)
        # ====================================================================
        self._draw_log_panel()

        # ====================================================================
        # SECTION 5: MAIN DU JOUEUR (droite)
        # ====================================================================
        if current_player.is_human:
            self._draw_hand_panel(current_player)

        # ====================================================================
        # SECTION 6: CARTE EN DRAG
        # ====================================================================
        if self.dragging_card:
            self._draw_dragged_card()

        # ====================================================================
        # SECTION 7: BOUTONS D'ACTION (bas)
        # ====================================================================
        self._draw_action_buttons(current_player)

        # ====================================================================
        # SECTION 8: INFO-BULLE
        # ====================================================================
        self._draw_tooltip()

        pygame.display.flip()

    def _draw_decks_panel(self, current_player):
        """Panneau des pioches à gauche"""
        deck_x = DECKS_X + 5
        deck_y = TOP_MARGIN
        deck_w = PANEL_DECKS_W - 10
        deck_h = CONTENT_H - 10
        
        # Panneau de fond
        pygame.draw.rect(self.screen, (30, 30, 40), (DECKS_X, deck_y - 5, PANEL_DECKS_W, deck_h + 10))
        pygame.draw.rect(self.screen, (100, 100, 120), (DECKS_X, deck_y - 5, PANEL_DECKS_W, deck_h + 10), 2)
        
        # Titre
        title = self.font_small.render("Pioches", True, (200, 200, 200))
        self.screen.blit(title, (deck_x, deck_y))
        
        # Afficher les pioches
        for i, player in enumerate(self.game.players):
            y = deck_y + 30 + i * 70
            deck_text = self.font_small.render(f"J{i+1}", True, (200, 200, 200))
            self.screen.blit(deck_text, (deck_x, y))
            cards_count = self.font_small.render(f"{len(player.deck)}", True, (180, 180, 180))
            self.screen.blit(cards_count, (deck_x, y + 20))

    def _draw_castle_panel(self, current_player):
        """Château central avec cour et tiles"""
        cour_start_x = CASTLE_X + 10
        cour_start_y = TOP_MARGIN + 20
        cell_size = CASTLE_CELL_SIZE

        # Draw castle tiles (Tours and Remparts) - around the cour at positions -1 to 4
        for (tx, ty), tile in self.game.board.tiles.items():
            px = cour_start_x + tx * cell_size
            py = cour_start_y + ty * cell_size

            # Draw tile using images
            if tile['type'] == 'tour':
                img = self.game.board.card_images.get('Tour')
                if img:
                    img_w, img_h = img.get_size()
                    if img_w > cell_size or img_h > cell_size:
                        crop_rect = pygame.Rect((img_w - cell_size) // 2, (img_h - cell_size) // 2, cell_size, cell_size)
                        cropped = img.subsurface(crop_rect).copy()
                    else:
                        cropped = img
                    rotation = tile['rotation']
                    if rotation > 0:
                        cropped = pygame.transform.rotate(cropped, rotation * 90)
                    self.screen.blit(cropped, (px, py))
                else:
                    pygame.draw.rect(self.screen, (200, 160, 100), (px, py, cell_size, cell_size))
                    pygame.draw.rect(self.screen, (160, 120, 60), (px, py, cell_size, cell_size), 2)

            elif tile['type'] == 'rempart':
                img = self.game.board.card_images.get('Rempart')
                if img:
                    img_w, img_h = img.get_size()
                    if img_w > cell_size or img_h > cell_size:
                        crop_rect = pygame.Rect((img_w - cell_size) // 2, (img_h - cell_size) // 2, cell_size, cell_size)
                        cropped = img.subsurface(crop_rect).copy()
                    else:
                        cropped = img
                    rotation = tile['rotation']
                    if rotation > 0:
                        cropped = pygame.transform.rotate(cropped, rotation * 90)
                    self.screen.blit(cropped, (px, py))
                else:
                    pygame.draw.rect(self.screen, (180, 150, 100), (px, py, cell_size, cell_size))
                    pygame.draw.rect(self.screen, (140, 110, 60), (px, py, cell_size, cell_size), 2)

            # Draw cards on tiles
            if tile['card']:
                card = tile['card']
                img = self.game.board.card_images.get(card.nom)
                if img:
                    img_w, img_h = img.get_size()
                    target_size = cell_size - 4
                    scale = min(target_size / img_w, target_size / img_h)
                    new_w = int(img_w * scale)
                    new_h = int(img_h * scale)
                    scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                    offset_x = (cell_size - new_w) // 2
                    offset_y = (cell_size - new_h) // 2
                    self.screen.blit(scaled, (px + offset_x, py + offset_y))
                else:
                    card_color = self._get_card_location_color(card)
                    pygame.draw.rect(self.screen, card_color, (px + 2, py + 2, cell_size - 4, cell_size - 4))
                    text = self.font_small.render(card.nom[:8], True, (200, 200, 200))
                    self.screen.blit(text, (px + 5, py + 15))

        # Draw cour background (interior 4x4)
        cour_interior_x = cour_start_x
        cour_interior_y = cour_start_y
        cour_interior_w = cell_size * 4
        cour_interior_h = cell_size * 4
        pygame.draw.rect(self.screen, (220, 200, 180), (cour_interior_x, cour_interior_y, cour_interior_w, cour_interior_h))
        pygame.draw.rect(self.screen, (100, 80, 60), (cour_interior_x, cour_interior_y, cour_interior_w, cour_interior_h), 3)

        # Draw cour grid and cards
        for y in range(4):
            for x in range(4):
                px = cour_start_x + x * cell_size
                py = cour_start_y + y * cell_size
                pygame.draw.rect(self.screen, (100, 80, 60), (px, py, cell_size, cell_size), 1)

                if self.game.board.cour[y][x]:
                    card = self.game.board.cour[y][x]
                    img = self.game.board.card_images.get(card.nom)
                    if img:
                        img_w, img_h = img.get_size()
                        target_size = cell_size - 4
                        scale = min(target_size / img_w, target_size / img_h)
                        new_w = int(img_w * scale)
                        new_h = int(img_h * scale)
                        scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                        offset_x = (cell_size - new_w) // 2
                        offset_y = (cell_size - new_h) // 2
                        self.screen.blit(scaled, (px + offset_x, py + offset_y))
                    else:
                        card_color = self._get_card_location_color(card)
                        pygame.draw.rect(self.screen, card_color, (px + 2, py + 2, cell_size - 4, cell_size - 4))
                        text = self.font_small.render(card.nom[:12], True, (200, 200, 200))
                        self.screen.blit(text, (px + 5, py + 35))

    def _draw_exchange_panel(self):
        """Panneau d'échange au centre"""
        if not self.game.exchange:
            return
        
        exchange_x = EXCHANGE_X + 10
        exchange_y = TOP_MARGIN + 20
        exchange_card_size = 80
        
        # Panneau de fond
        pygame.draw.rect(self.screen, (40, 40, 50), (EXCHANGE_X + 5, exchange_y - 25, PANEL_EXCHANGE_W - 10, CONTENT_H - 30))
        pygame.draw.rect(self.screen, (100, 100, 120), (EXCHANGE_X + 5, exchange_y - 25, PANEL_EXCHANGE_W - 10, CONTENT_H - 30), 2)
        
        # Titre
        exchange_title = self.font.render(f"Échange: {len(self.game.exchange)}", True, (200, 200, 200))
        self.screen.blit(exchange_title, (exchange_x, exchange_y - 20))
        
        # Afficher les cartes d'échange (en colonne)
        for i, card in enumerate(self.game.exchange[:8]):  # Max 8 cartes
            img = self.game.board.card_images.get(card.nom)
            card_y = exchange_y + i * (exchange_card_size + 10)
            
            if card_y + exchange_card_size > TOP_MARGIN + CONTENT_H:
                break
            
            border_color = (100, 100, 150)
            border_width = 1
            if self.exchange_mode and self.selected_exchange_card_idx == i:
                border_color = (255, 200, 0)
                border_width = 3
            
            if img:
                img_w, img_h = img.get_size()
                scale = min(exchange_card_size / img_w, exchange_card_size / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                pygame.draw.rect(self.screen, border_color, (exchange_x, card_y, exchange_card_size + 5, exchange_card_size + 5), border_width)
                self.screen.blit(scaled, (exchange_x + (exchange_card_size + 5 - new_w) // 2, card_y + (exchange_card_size + 5 - new_h) // 2))
            else:
                card_color = self._get_card_location_color(card)
                pygame.draw.rect(self.screen, card_color, (exchange_x, card_y, exchange_card_size + 5, exchange_card_size + 5), border_width)
                pygame.draw.rect(self.screen, border_color, (exchange_x, card_y, exchange_card_size + 5, exchange_card_size + 5), border_width)
                text = self.font_small.render(card.nom[:8], True, (200, 200, 200))
                self.screen.blit(text, (exchange_x + 5, card_y + 20))

    def _draw_log_panel(self):
        """Panneau du journal à droite"""
        log_x = LOG_X + 10
        log_y = TOP_MARGIN + 20
        log_w = PANEL_LOG_W - 20
        log_h = CONTENT_H - 30
        
        # Panneau de fond
        pygame.draw.rect(self.screen, (30, 30, 40), (LOG_X + 5, log_y - 25, PANEL_LOG_W - 10, log_h + 30))
        pygame.draw.rect(self.screen, (100, 100, 120), (LOG_X + 5, log_y - 25, PANEL_LOG_W - 10, log_h + 30), 2)
        
        # Titre
        log_title = self.font.render("Journal", True, (200, 200, 200))
        self.screen.blit(log_title, (log_x, log_y - 20))
        
        # Afficher les messages
        for i, message in enumerate(self.action_log):
            y_pos = log_y + i * 18
            if y_pos < log_y + log_h:
                log_text = self.font_small.render(message, True, (150, 200, 150))
                self.screen.blit(log_text, (log_x, y_pos))

    def _draw_hand_panel(self, current_player):
        """Panneau de la main du joueur à droite"""
        hand_x = HAND_X + 10
        hand_y = TOP_MARGIN + 20
        hand_w = PANEL_HAND_W - 20
        hand_h = CONTENT_H - 30
        
        # Panneau de fond
        pygame.draw.rect(self.screen, (30, 30, 40), (HAND_X + 5, hand_y - 25, PANEL_HAND_W - 10, hand_h + 30))
        pygame.draw.rect(self.screen, (100, 100, 120), (HAND_X + 5, hand_y - 25, PANEL_HAND_W - 10, hand_h + 30), 2)
        
        # Titre
        text_label = self.font.render("Main", True, (200, 200, 200))
        self.screen.blit(text_label, (hand_x, hand_y - 20))
        
        # Afficher les cartes de la main
        card_size = 80
        cards_per_row = 2
        for i, card in enumerate(current_player.hand):
            img = self.game.board.card_images.get(card.nom)
            row = i // cards_per_row
            col = i % cards_per_row
            card_x = hand_x + col * (card_size + 10)
            card_y = hand_y + row * (card_size + 10)
            
            if card_y + card_size > hand_y + hand_h:
                break
            
            border_color = (200, 200, 200)
            border_width = 1
            if card == self.selected_card:
                border_color = (0, 255, 0)
                border_width = 3
            elif self.exchange_mode and self.selected_hand_card_idx == i:
                border_color = (255, 200, 0)
                border_width = 3
            
            if img:
                img_w, img_h = img.get_size()
                scale = min(card_size / img_w, card_size / img_h)
                new_w = int(img_w * scale)
                new_h = int(img_h * scale)
                scaled = pygame.transform.smoothscale(img, (new_w, new_h))
                pygame.draw.rect(self.screen, border_color, (card_x, card_y, card_size + 2, card_size + 2), border_width)
                self.screen.blit(scaled, (card_x + (card_size - new_w) // 2, card_y + (card_size - new_h) // 2))
            else:
                card_color = self._get_card_location_color(card)
                pygame.draw.rect(self.screen, border_color, (card_x, card_y, card_size, card_size), border_width)
                text = self.font_small.render(card.nom[:4], True, (200, 200, 200))
                self.screen.blit(text, (card_x + 5, card_y + 15))

    def _draw_dragged_card(self):
        """Dessiner la carte en train d'être traînée"""
        img = self.game.board.card_images.get(self.dragging_card.nom)
        if img:
            img_w, img_h = img.get_size()
            scale = min(100 / img_w, 100 / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            scaled = pygame.transform.smoothscale(img, (new_w, new_h))
            drag_x = self.mouse_pos[0] - self.drag_offset[0] - new_w // 2
            drag_y = self.mouse_pos[1] - self.drag_offset[1] - new_h // 2
            scaled.set_alpha(200)
            self.screen.blit(scaled, (drag_x, drag_y))
        else:
            card_color = self._get_card_location_color(self.dragging_card)
            drag_x = self.mouse_pos[0] - self.drag_offset[0] - 50
            drag_y = self.mouse_pos[1] - self.drag_offset[1] - 50
            pygame.draw.rect(self.screen, card_color, (drag_x, drag_y, 100, 100), 2)
            text = self.font_small.render(self.dragging_card.nom[:6], True, (200, 200, 200))
            self.screen.blit(text, (drag_x + 5, drag_y + 25))

    def _draw_action_buttons(self, current_player):
        """Boutons d'action en bas"""
        if not current_player.is_human:
            controls = self.font_small.render("Tour de l'ordinateur... (ESC: Quitter)", True, (150, 150, 150))
            self.screen.blit(controls, (20, SCREEN_H - 25))
            return
        
        button_y = SCREEN_H - 60
        
        # Draw draw card button
        draw_btn = self.action_buttons['draw']
        btn_color = (50, 100, 50) if current_player.deck else (80, 80, 80)
        pygame.draw.rect(self.screen, btn_color, draw_btn)
        pygame.draw.rect(self.screen, (100, 200, 100), draw_btn, 2)
        draw_text = self.font_small.render("Tirer (+1)", True, (200, 200, 200))
        self.screen.blit(draw_text, (draw_btn.x + 10, draw_btn.y + 10))
        
        # Draw exchange button
        exchange_btn = self.action_buttons['exchange']
        btn_color = (50, 50, 100) if self.game.exchange and current_player.hand else (80, 80, 80)
        pygame.draw.rect(self.screen, btn_color, exchange_btn)
        pygame.draw.rect(self.screen, (100, 100, 200), exchange_btn, 2)
        exchange_text = self.font_small.render("Échanger", True, (200, 200, 200))
        self.screen.blit(exchange_text, (exchange_btn.x + 10, exchange_btn.y + 10))
        
        # Draw skip button
        skip_btn = self.action_buttons['skip']
        pygame.draw.rect(self.screen, (100, 50, 50), skip_btn)
        pygame.draw.rect(self.screen, (200, 100, 100), skip_btn, 2)
        skip_text = self.font_small.render("Passer", True, (200, 200, 200))
        self.screen.blit(skip_text, (skip_btn.x + 20, skip_btn.y + 10))
        
        # Draw info text
        info = self.font_small.render(
            "Glisser une carte pour la placer | Cliquez sur les boutons pour les actions | ESC: Quitter",
            True, (150, 150, 150))
        self.screen.blit(info, (20, SCREEN_H - 25))





