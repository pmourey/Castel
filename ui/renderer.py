import pygame

# ============================================================================
# FIXED LAYOUT CONSTANTS  (never change with window size)
# ============================================================================
TOP_H        = 42    # compact header (single line)
BTM_H        = 26    # footer height
LEFT_W       = 130   # player-pioche panel (fixed)
LOG_W        = 200   # action-log panel (fixed)
HAND_BTN_H   = 36    # action button height
HAND_BTN_GAP = 10    # gap between action buttons
EXCH_GAP     = 4     # gap between exchange cards
HAND_CARD_GAP  = 8   # gap between hand cards
HAND_CARD_COLS = 5   # number of hand card columns


# Canonical siege slot positions (one per rempart face)
SIEGE_SLOTS = (
    [(-2, y) for y in range(4)] +   # left wall
    [(5,  y) for y in range(4)] +   # right wall
    [(x, -2) for x in range(4)] +   # top wall
    [(x,  5) for x in range(4)]     # bottom wall
)


class CastelWindow:
    def __init__(self, game):
        self.game = game
        pygame.init()
        self._recompute_layout(1800, 900)
        self.screen = pygame.display.set_mode((self.sw, self.sh), pygame.RESIZABLE)
        pygame.display.set_caption("Castel - Jeu de Plateau")
        self.clock = pygame.time.Clock()
        self.running = True

        self.font       = pygame.font.Font(None, 20)
        self.font_small = pygame.font.Font(None, 16)
        self.font_title = pygame.font.Font(None, 30)
        self.font_big   = pygame.font.Font(None, 72)

        self.game.board.load_images()

        self.selected_card              = None
        self.dragging_card              = None
        self.drag_offset                = (0, 0)
        self.ai_delay                   = 60
        self.action_log                 = []
        self.max_log_lines              = 40
        self.mouse_pos                  = (0, 0)
        self.tooltip_card               = None
        self.exchange_mode              = False
        self.selected_hand_card_idx     = None
        self.selected_exchange_card_idx = None
        self.action_buttons             = {}
        self.game_over                  = False
        self.winner                     = None
        self.advanced_tooltip           = True
        self._create_action_buttons()


    def _recompute_layout(self, w, h):
        """Compute all layout variables from window size. Call on init and resize."""
        self.sw, self.sh = w, h
        self.inner_h = h - TOP_H - BTM_H

        # CELL: constrained by both vertical space and castle panel width
        cell_v = max(40, min(160, (h - TOP_H - BTM_H - 60) // 9))
        avail_w = w - LEFT_W - LOG_W
        cell_h  = max(40, min(160, (avail_w // 2 - 40) // 8))
        self.cell = min(cell_v, cell_h)
        c = self.cell

        self.castle_w = 8 * c + 40
        # Reduce LOG_W impact so hand area is larger: recompute hand_w from remaining space
        self.hand_w   = max(360, w - LEFT_W - self.castle_w - LOG_W)
        self.castle_x = LEFT_W
        self.log_x    = self.castle_x + self.castle_w
        self.hand_x   = self.log_x + LOG_W

        self.castle_origin_x = self.castle_x + 20 + 2 * c
        self.castle_origin_y = TOP_H + 20 + 2 * c

        self.castle_grid_bottom = self.castle_origin_y + 5 * c
        self.ext_strip_y = self.castle_grid_bottom + c + 4
        self.ext_strip_h = h - BTM_H - self.ext_strip_y

        # Exchange cards: compute columns based on available hand width
        # hand_card_size: fill available height while respecting horizontal limit
        hand_area_h = h - TOP_H - BTM_H - HAND_BTN_H - 10 - 32   # inner minus buttons minus title
        # Allocate ~40% of height to hand, ~40% to exchange, 20% to buttons/title
        slot_v = max(48, (hand_area_h * 45 // 100) // 3)          # fits 3 hand rows in 45% height
        horiz_limit = max(48, (self.hand_w - 20 - (HAND_CARD_COLS - 1) * HAND_CARD_GAP) // HAND_CARD_COLS)
        self.hand_card_size = min(horiz_limit, slot_v)
        hs = self.hand_card_size
        self.exch_cols = max(3, (self.hand_w - 20) // (hs + EXCH_GAP))

    def _on_resize(self, w, h):
        """Handle window resize: recompute layout and recreate buttons."""
        self._recompute_layout(w, h)
        self._create_action_buttons()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def add_log(self, message):
        self.action_log.append(message)
        if len(self.action_log) > self.max_log_lines:
            self.action_log.pop(0)

    def _card_color(self, card):
        mapping = {
            "bleu":   (100, 150, 210),
            "orange": (210, 150,  80),
            "rouge":  (210,  80,  80),
            "vert":   ( 80, 190,  80),
            "violet": (160,  80, 210),
        }
        return mapping.get(getattr(card, "couleur", "").lower(), (130, 130, 130))

    def _pawn_color(self, player):
        """Map player.pions_color string to an RGB color for pawn display."""
        if not player:
            return (220, 220, 220)
        mapping = {
            'black':  (20, 20, 20),
            'beige':  (200, 180, 140),
            'red':    (200, 60, 60),
            'green':  (80, 190, 80),
            'purple': (150, 80, 200),
        }
        return mapping.get(getattr(player, 'pions_color', '').lower(), (220, 220, 220))

    def _castle_px(self, tx, ty):
        """Return top-left screen pixel for castle grid position (tx, ty)."""
        return (self.castle_origin_x + tx * self.cell, self.castle_origin_y + ty * self.cell)

    def _grid_from_px(self, px, py):
        """Return (tx, ty) for screen position if inside the castle grid, else None."""
        tx = (px - self.castle_origin_x) // self.cell
        ty = (py - self.castle_origin_y) // self.cell
        sx = self.castle_origin_x + tx * self.cell
        sy = self.castle_origin_y + ty * self.cell
        if sx <= px < sx + self.cell and sy <= py < sy + self.cell:
            return (tx, ty)
        return None

    def _fit_image(self, img, w, h):
        iw, ih = img.get_size()
        scale = min(w / iw, h / ih)
        return pygame.transform.smoothscale(img, (int(iw * scale), int(ih * scale)))

    def _draw_card_on_cell(self, card, px, py, size):
        img = self.game.board.card_images.get(card.nom)
        if img:
            fitted = self._fit_image(img, size - 4, size - 4)
            fw, fh = fitted.get_size()
            self.screen.blit(fitted, (px + (size - fw) // 2, py + (size - fh) // 2))
        else:
            bg = self._card_color(card)
            pygame.draw.rect(self.screen, bg, (px + 2, py + 2, size - 4, size - 4))
            lbl = self.font_small.render(card.nom[:10], True, (230, 230, 230))
            self.screen.blit(lbl, (px + 4, py + size // 2 - 7))

        # Pawn color indicator (if card has a pion_owner)
        owner = getattr(card, 'pion_owner', None)
        if owner:
            col = self._pawn_color(owner)
            pygame.draw.circle(self.screen, col, (px + 8, py + 8), max(5, size // 18))
        else:
            # Draw zone color dot on cards without pawn (small top-right)
            if size >= 36:
                pygame.draw.circle(self.screen, self._card_color(card), (px + size - 10, py + 10), max(4, size // 22))

    def _hand_idx_at(self, x, y, player):
        bh = HAND_BTN_H
        btn_y = TOP_H + self.inner_h - bh - 10
        exch_rows = max(1, (len(self.game.exchange) + self.exch_cols - 1) // self.exch_cols)
        exch_h = exch_rows * (self.hand_card_size + EXCH_GAP) + 24   # title + rows
        exch_y = btn_y - 4 - exch_h
        hand_cards_bottom = exch_y - 6

        lx = x - (self.hand_x + 10)
        ly = y - (TOP_H + 32)
        if lx < 0 or ly < 0 or y >= hand_cards_bottom:
            return None
        cw = self.hand_card_size; gap = HAND_CARD_GAP
        col = lx // (cw + gap)
        row = ly // (cw + gap)
        idx = row * HAND_CARD_COLS + col
        if 0 <= col < HAND_CARD_COLS and 0 <= idx < len(player.hand):
            return idx
        return None

    def _exchange_idx_at(self, x, y):
        bh = HAND_BTN_H
        btn_y = TOP_H + self.inner_h - bh - 10
        exch_rows = max(1, (len(self.game.exchange) + self.exch_cols - 1) // self.exch_cols)
        exch_h = exch_rows * (self.hand_card_size + EXCH_GAP) + 24
        exch_y = btn_y - 4 - exch_h

        lx = x - (self.hand_x + 10)
        ly = y - (exch_y + 24)
        if lx < 0 or ly < 0:
            return None
        col = lx // (self.hand_card_size + EXCH_GAP)
        row = ly // (self.hand_card_size + EXCH_GAP)
        idx = row * self.exch_cols + col
        if 0 <= col < self.exch_cols and 0 <= idx < len(self.game.exchange):
            return idx
        return None

    def _in_ext_strip(self, x, y):
        return self.castle_x <= x <= self.castle_x + self.castle_w and self.ext_strip_y <= y <= self.ext_strip_y + self.ext_strip_h

    def _ext_strip_pos_from_px(self, x, y):
        """Map a pixel in the exterior strip to a game board position."""
        lx = x - (self.castle_x + 5)
        ly = y - self.ext_strip_y
        cw = self.cell; gap = 4
        cols = (self.castle_w - 10) // (cw + gap)
        col = max(0, lx // (cw + gap))
        row = max(0, ly // (cw + gap))
        # Use exterior positions starting at x=5, y=6 to avoid conflict with siege slots
        return (5 + col, 6 + row)

    def _ext_card_at(self, mx, my):
        """Return the exterior-strip card under pixel (mx, my), or None."""
        if not self._in_ext_strip(mx, my):
            return None
        cw = self.cell; gap = 4
        ext_cards = sorted(
            [(pos, c) for pos, c in self.game.board.exterieur.items() if pos not in SIEGE_SLOTS],
            key=lambda t: t[0]
        )
        cols = (self.castle_w - 10) // (cw + gap)
        for idx, (pos, card) in enumerate(ext_cards):
            col = idx % cols
            row = idx // cols
            ex = self.castle_x + 5 + col * (cw + gap)
            ey = self.ext_strip_y + 3 + row * (cw + gap)
            if ey + cw > self.ext_strip_y + self.ext_strip_h:
                break
            if ex <= mx < ex + cw and ey <= my < ey + cw:
                return card
        return None

    def _is_siege_card(self, card):
        return card is not None and card.nom == "Engin_de_siege"

    # -------------------------------------------------------------------------
    # Create action buttons at bottom of hand panel
    # -------------------------------------------------------------------------

    def _create_action_buttons(self):
        bw = max(80, (self.hand_w - 40) // 3 - HAND_BTN_GAP)
        bh = HAND_BTN_H
        gap = HAND_BTN_GAP
        by = TOP_H + self.inner_h - bh - 10
        self.action_buttons = {
            "draw":     pygame.Rect(self.hand_x + 10,               by, bw, bh),
            "exchange": pygame.Rect(self.hand_x + 10 + bw + gap,    by, bw, bh),
            "skip":     pygame.Rect(self.hand_x + 10 + 2*(bw+gap),  by, bw, bh),
        }
        # Tooltip mode toggle (small switch, top-right of hand panel)
        sw = 110; sh_ = 22
        self.tooltip_toggle_rect = pygame.Rect(self.hand_x + self.hand_w - sw - 8, 10, sw, sh_)

    # -------------------------------------------------------------------------
    # Event handling
    # -------------------------------------------------------------------------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
            if event.type == pygame.VIDEORESIZE:
                self._on_resize(event.w, event.h)
            if event.type == pygame.MOUSEMOTION:
                self.mouse_pos = event.pos
                self._update_tooltip()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_down(event.pos)
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_card:
                    self._handle_drop(event.pos)

    def _handle_mouse_down(self, pos):
        if self.game_over:
            return
        current = self.game.players[self.game.current_player]
        if not current.is_human:
            return
        x, y = pos

        if hasattr(self, "tooltip_toggle_rect") and self.tooltip_toggle_rect.collidepoint(x, y):
            self.advanced_tooltip = not self.advanced_tooltip
            return

        for name, rect in self.action_buttons.items():
            if rect.collidepoint(x, y):
                self._handle_button(name, current)
                return

        # Exchange section inside hand panel
        if self.exchange_mode and self.hand_x <= x <= self.hand_x + self.hand_w:
            ei = self._exchange_idx_at(x, y)
            if ei is not None:
                self.selected_exchange_card_idx = ei
                self.add_log(f"Echange: {self.game.exchange[ei].nom}")
                if self.selected_hand_card_idx is not None:
                    self._perform_exchange(current)
                return

        if self.hand_x <= x <= self.hand_x + self.hand_w and TOP_H <= y <= self.sh - BTM_H:
            idx = self._hand_idx_at(x, y, current)
            if idx is not None and 0 <= idx < len(current.hand):
                card = current.hand[idx]
                self.selected_card = card
                if self.exchange_mode:
                    self.selected_hand_card_idx = idx
                    self.add_log(f"Main: {card.nom}")
                    if self.selected_exchange_card_idx is not None:
                        self._perform_exchange(current)
                    return
                cw = self.hand_card_size; gap = HAND_CARD_GAP
                col = idx % 5; row = idx // 5
                cx_ = self.hand_x + 10 + col * (cw + gap) + cw // 2
                cy_ = TOP_H + 32 + row * (cw + gap) + cw // 2
                self.drag_offset = (x - cx_, y - cy_)
                self.dragging_card = card

    def _handle_button(self, name, player):
        if name == "draw":
            if player.deck:
                self.game.draw_card(player)
                self.add_log(f"J{self.game.current_player+1} pioche une carte")
                if self.game.advance_turn_if_done():
                    self.add_log(f"Tour J{self.game.current_player+1}")
        elif name == "exchange":
            if player.hand and self.game.exchange:
                self.exchange_mode = not self.exchange_mode
                if self.exchange_mode:
                    self.selected_hand_card_idx = None
                    self.selected_exchange_card_idx = None
                    self.add_log("Mode echange: cliquez main puis echange")
                else:
                    self.add_log("Mode echange annule")
        elif name == "skip":
            self.game.actions_remaining -= 1
            self.exchange_mode = False
            self.add_log("Action passee")
            if self.game.advance_turn_if_done():
                self.add_log(f"Tour J{self.game.current_player+1}")

    def _perform_exchange(self, player):
        try:
            self.game.exchange_card(player, self.selected_hand_card_idx, self.selected_exchange_card_idx)
            self.add_log("Echange effectue")
            self.exchange_mode = False
            self.selected_hand_card_idx = None
            self.selected_exchange_card_idx = None
            if self.game.advance_turn_if_done():
                self.add_log(f"Tour J{self.game.current_player+1}")
        except Exception as e:
            self.add_log(f"Echange impossible: {e}")

    def _handle_drop(self, pos):
        current = self.game.players[self.game.current_player]
        x, y = pos
        placed = False

        # Castle grid (includes cour, tiles, siege slots, and nearby exterior)
        grid = self._grid_from_px(x, y)
        if grid is not None:
            placed = self._try_place(current, self.dragging_card, grid)

        # Exterior strip (non-siege exterior cards)
        if not placed and self._in_ext_strip(x, y):
            # Try existing exterior positions first (drop on an occupied slot = invalid)
            free = self._ext_strip_pos_from_px(x, y)
            # Check if already occupied; if so find next free position
            if free in self.game.board.exterieur:
                for bx in range(5, 50):
                    for by2 in range(6, 12):
                        if (bx, by2) not in self.game.board.exterieur:
                            free = (bx, by2)
                            break
                    else:
                        continue
                    break
            placed = self._try_place(current, self.dragging_card, free)

        if not placed:
            self.add_log(f"Placement invalide: {self.dragging_card.nom}")

        self.dragging_card = None
        self.selected_card = None

    def _try_place(self, player, card, position):
        result = self.game.place_card(player, card, position)
        if result == "win":
            self.game_over = True
            self.winner = player
            self.add_log(f"Joueur {self.game.players.index(player)+1} a gagne!")
            return True
        elif result == "ok":
            self.add_log(f"{card.nom} place en {position}")
            self.game.advance_turn_if_done()
            return True
        return False

    # -------------------------------------------------------------------------
    # AI update
    # -------------------------------------------------------------------------

    def update(self):
        if self.game_over:
            return
        current = self.game.players[self.game.current_player]
        if not current.is_human:
            self.ai_delay -= 1
            if self.ai_delay <= 0:
                self._run_ai_action(current)

    def _run_ai_action(self, player):
        action = player.choose_action(self.game)
        if action[0] == "place":
            _, card, position = action
            result = self.game.place_card(player, card, position)
            if result == "win":
                self.game_over = True
                self.winner = player
                self.add_log(f"IA {self.game.current_player+1} a gagne!")
            elif result == "ok":
                self.add_log(f"IA: {card.nom} en {position}")
            else:
                self.add_log(f"IA bloquee ({card.nom}), repli")
                if player.deck:
                    self.game.draw_card(player)
                elif self.game.exchange and player.hand:
                    self.game.exchange_card(player, 0, 0)
                else:
                    self.game.actions_remaining -= 1
        elif action[0] == "draw":
            self.game.draw_card(player)
            self.add_log(f"IA {self.game.current_player+1} pioche")
        elif action[0] == "exchange":
            _, hi, ei = action
            self.game.exchange_card(player, hi, ei)
            self.add_log(f"IA {self.game.current_player+1} echange")
        else:
            self.game.actions_remaining -= 1
            self.add_log(f"IA {self.game.current_player+1} passe")

        if self.game.advance_turn_if_done():
            self.ai_delay = 60
        else:
            self.ai_delay = 30

    # -------------------------------------------------------------------------
    # Draw
    # -------------------------------------------------------------------------

    def draw(self):
        self.screen.fill((18, 18, 28))
        self._draw_header()
        self._draw_left_panel()
        self._draw_castle_panel()
        self._draw_log_panel()
        self._draw_hand_panel()
        if self.dragging_card:
            self._draw_dragged_card()
        self._draw_tooltip()
        self._draw_footer()
        if self.game_over:
            self._draw_win_overlay()
        pygame.display.flip()

    def _draw_header(self):
        current = self.game.players[self.game.current_player]
        who   = "HUMAIN" if current.is_human else f"IA {self.game.current_player+1}"
        color = (80, 220, 80) if current.is_human else (220, 100, 100)
        # Left side: title
        title = self.font_title.render(f"CASTEL", True, (220, 200, 80))
        self.screen.blit(title, (LEFT_W + 8, 8))
        # Centre-left: tour/player/actions
        info = self.font.render(
            f"Tour {self.game.turn}   "
            f"J{self.game.current_player+1}/{len(self.game.players)} {who}   "
            f"Actions: {self.game.actions_remaining}/2   "
            f"Main: {len(current.hand)}  Pioche: {len(current.deck)}",
            True, color)
        self.screen.blit(info, (self.log_x + 8, 12))
        # Tooltip mode toggle switch
        if hasattr(self, "tooltip_toggle_rect"):
            r = self.tooltip_toggle_rect
            bg = (40, 110, 40) if self.advanced_tooltip else (60, 60, 80)
            border = (100, 200, 100) if self.advanced_tooltip else (110, 110, 150)
            pygame.draw.rect(self.screen, bg, r, border_radius=6)
            pygame.draw.rect(self.screen, border, r, 1, border_radius=6)
            label = "Image" if self.advanced_tooltip else "Texte"
            lbl = self.font_small.render(f"Tooltip: {label}", True, (210, 210, 210))
            self.screen.blit(lbl, (r.x + (r.w - lbl.get_width()) // 2,
                                   r.y + (r.h - lbl.get_height()) // 2))

    def _draw_footer(self):
        current = self.game.players[self.game.current_player]
        if current.is_human:
            hint = "Glisser carte sur le plateau pour la placer  |  Piocher / Echanger / Passer  |  ESC: Quitter"
        else:
            hint = "Tour de l ordinateur...   |   ESC: Quitter"
        self.screen.blit(self.font_small.render(hint, True, (90, 90, 110)), (10, self.sh - BTM_H + 7))

    def _draw_left_panel(self):
        r = pygame.Rect(0 + 3, TOP_H + 3, LEFT_W - 6, self.inner_h - 6)
        pygame.draw.rect(self.screen, (26, 26, 38), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)
        y = TOP_H + 12
        self.screen.blit(self.font_small.render("PIOCHES", True, (150, 150, 185)), (0 + 7, y))
        y += 20
        for i, p in enumerate(self.game.players):
            active = (i == self.game.current_player)
            color = (80, 210, 80) if active else (140, 140, 160)
            icon = ">" if active else " "
            self.screen.blit(self.font_small.render(f"{icon} J{i+1}", True, color), (0 + 5, y))
            y += 15
            self.screen.blit(self.font_small.render(f"  M:{len(p.hand)} P:{len(p.deck)}", True, (120, 120, 140)),
                             (0 + 5, y))
            y += 20

    # -------------------------------------------------------------------------
    # Castle panel
    # -------------------------------------------------------------------------

    def _draw_castle_panel(self):
        r = pygame.Rect(self.castle_x + 3, TOP_H + 3, self.castle_w - 6, self.inner_h - 6)
        pygame.draw.rect(self.screen, (23, 23, 36), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)

        dragging_siege = self._is_siege_card(self.dragging_card)
        dragging_ext   = (self.dragging_card and not dragging_siege
                          and "hors les murs" in getattr(self.dragging_card, "lieu", "").lower())

        # Draw siege slot cells (highlight when dragging siege engine)
        for slot in SIEGE_SLOTS:
            sx, sy = self._castle_px(*slot)
            occupied = slot in self.game.board.exterieur
            if dragging_siege and not occupied:
                slot_bg = (30, 60, 30)
                border  = (55, 155, 55)
                bw = 2
            elif occupied:
                slot_bg = (22, 45, 22)
                border  = (55, 125, 55)
                bw = 1
            else:
                slot_bg = (20, 30, 20)
                border  = (40, 80, 40)
                bw = 1
            pygame.draw.rect(self.screen, slot_bg, (sx, sy, self.cell, self.cell))
            pygame.draw.rect(self.screen, border, (sx, sy, self.cell, self.cell), bw)
            if occupied:
                self._draw_card_on_cell(self.game.board.exterieur[slot], sx, sy, self.cell)
            else:
                lbl = self.font_small.render("Engin", True, (50, 100, 50))
                self.screen.blit(lbl, (sx + (self.cell - lbl.get_width()) // 2, sy + self.cell // 2 - 7))

        # Courtyard background
        pygame.draw.rect(self.screen, (200, 185, 155),
                         (self.castle_origin_x, self.castle_origin_y, 4 * self.cell, 4 * self.cell))
        pygame.draw.rect(self.screen, (140, 115, 75),
                         (self.castle_origin_x, self.castle_origin_y, 4 * self.cell, 4 * self.cell), 2)

        # Castle tiles (tours + remparts)
        for (tx, ty), tile in self.game.board.tiles.items():
            px, py = self._castle_px(tx, ty)
            # Use provided tile sprites if available (Tour.png / Rempart.png)
            img = self.game.board.tour_img if tile['type'] == 'tour' else self.game.board.rempart_img
            bg  = (195, 165, 105) if tile['type'] == 'tour' else (165, 145, 105)
            if img:
                cropped = self._fit_image(img, self.cell, self.cell)
                rot = tile.get('rotation', 0)
                if rot:
                    cropped = pygame.transform.rotate(cropped, rot * 90)
                # Center the (possibly rotated) tile inside the cell
                r = cropped.get_rect()
                bx = px + (self.cell - r.width)//2
                by = py + (self.cell - r.height)//2
                self.screen.blit(cropped, (bx, by))
            else:
                pygame.draw.rect(self.screen, bg, (px, py, self.cell, self.cell))
                pygame.draw.rect(self.screen, (100, 80, 50), (px, py, self.cell, self.cell), 1)
            if tile['card']:
                self._draw_card_on_cell(tile['card'], px, py, self.cell)

        # Cour grid cells + cards (+ Chevalier stacking)
        for cy in range(4):
            for cx in range(4):
                px, py = self._castle_px(cx, cy)
                pygame.draw.rect(self.screen, (135, 110, 70), (px, py, self.cell, self.cell), 1)
                card = self.game.board.cour[cy][cx]
                if card:
                    self._draw_cour_card(card, px, py)

        # Exterior strip (non-siege exterior cards)
        self._draw_exterior_strip(dragging_ext)

    def _draw_cour_card(self, card, px, py):
        """Draw a cour card, handling Chevalier stacking."""
        protected = getattr(card, "protects", None)
        if protected:
            # Protected card drawn slightly offset (bottom-right corner visible)
            offset = 12
            inner = self.cell - offset - 4
            self._draw_card_on_cell(protected, px + offset, py + offset, inner)
            # Chevalier on top (slightly smaller to reveal corner of protected card)
            self._draw_card_on_cell(card, px, py, self.cell - offset)
            # Shield icon to indicate protection
            pygame.draw.circle(self.screen, (100, 155, 255), (px + self.cell - 8, py + 8), 7)
            pygame.draw.circle(self.screen, (200, 220, 255), (px + self.cell - 8, py + 8), 7, 1)
        else:
            self._draw_card_on_cell(card, px, py, self.cell)

    def _draw_exterior_strip(self, highlight):
        # Label
        lbl_y = self.castle_grid_bottom + 4
        lbl = self.font_small.render("Hors les murs (drag cartes VERTES ici)", True, (80, 175, 80))
        self.screen.blit(lbl, (self.castle_x + 8, lbl_y))

        # Strip background
        strip_r = pygame.Rect(self.castle_x + 4, self.ext_strip_y, self.castle_w - 8, self.ext_strip_h - 2)
        strip_bg = (22, 42, 22) if highlight else (18, 36, 18)
        strip_brd = (70, 150, 70) if highlight else (45, 100, 45)
        pygame.draw.rect(self.screen, strip_bg, strip_r)
        pygame.draw.rect(self.screen, strip_brd, strip_r, 1)

        # Exterior cards (non-siege: positions where y>=6)
        cw = self.cell; gap = 4
        cols = (self.castle_w - 10) // (cw + gap)
        ext_cards = sorted(
            ((pos, c) for pos, c in self.game.board.exterieur.items()
             if pos not in SIEGE_SLOTS),
            key=lambda t: t[0]
        )
        for idx, (pos, card) in enumerate(ext_cards):
            col = idx % cols
            row = idx // cols
            ex = self.castle_x + 5 + col * (cw + gap)
            ey = self.ext_strip_y + 3 + row * (cw + gap)
            if ey + cw > self.ext_strip_y + self.ext_strip_h:
                break
            self._draw_card_on_cell(card, ex, ey, cw)

    # -------------------------------------------------------------------------
    # Log panel
    # -------------------------------------------------------------------------

    def _draw_log_panel(self):
        r = pygame.Rect(self.log_x + 3, TOP_H + 3, LOG_W - 6, self.inner_h - 6)
        pygame.draw.rect(self.screen, (20, 20, 34), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)
        self.screen.blit(self.font_small.render("JOURNAL", True, (150, 150, 185)), (self.log_x + 10, TOP_H + 10))

        line_h = 14
        y = TOP_H + 26
        max_chars = (LOG_W - 18) // 7
        for msg in self.action_log[-(self.max_log_lines):]:
            trunc = msg[:max_chars]
            if "gagne" in msg.lower() or "victoire" in msg.lower():
                col = (100, 230, 100)
            elif "invalide" in msg.lower() or "bloque" in msg.lower() or "impossible" in msg.lower():
                col = (230, 100, 100)
            elif msg.startswith("Tour "):
                col = (180, 180, 100)
            else:
                col = (150, 195, 155)
            self.screen.blit(self.font_small.render(trunc, True, col), (self.log_x + 8, y))
            y += line_h
            if y > TOP_H + self.inner_h - 10:
                break

    # -------------------------------------------------------------------------
    # Hand panel  (cards + action buttons + exchange section)
    # -------------------------------------------------------------------------

    def _draw_hand_panel(self):
        current = self.game.players[self.game.current_player]

        r = pygame.Rect(self.hand_x + 3, TOP_H + 3, self.hand_w - 6, self.inner_h - 6)
        pygame.draw.rect(self.screen, (23, 23, 36), r)
        pygame.draw.rect(self.screen, (95, 95, 135), r, 2)

        who = "VOTRE MAIN" if current.is_human else f"IA {self.game.current_player+1}"
        color = (90, 215, 90) if current.is_human else (215, 95, 95)
        self.screen.blit(self.font.render(who, True, color), (self.hand_x + 12, TOP_H + 10))

        if not current.is_human:
            self.screen.blit(
                self.font_small.render("Tour de l ordinateur en cours...", True, (155, 135, 95)),
                (self.hand_x + 12, TOP_H + 34))
            return

        # --- Compute layout heights ---
        bh = HAND_BTN_H
        btn_y = TOP_H + self.inner_h - bh - 10

        exch_rows = max(1, (len(self.game.exchange) + self.exch_cols - 1) // self.exch_cols)
        exch_h    = exch_rows * (self.hand_card_size + EXCH_GAP) + 24   # 24 = title line
        exch_y    = btn_y - 4 - exch_h

        hand_cards_bottom = exch_y - 8
        hand_cards_top    = TOP_H + 32

        # --- Separators ---
        pygame.draw.line(self.screen, (70, 70, 105),
                         (self.hand_x + 8, exch_y - 4), (self.hand_x + self.hand_w - 8, exch_y - 4))
        pygame.draw.line(self.screen, (70, 70, 105),
                         (self.hand_x + 8, btn_y - 4), (self.hand_x + self.hand_w - 8, btn_y - 4))

        # --- Action buttons ---
        self._draw_hand_buttons(current, btn_y)

        # --- Exchange section ---
        self._draw_exchange_in_hand(exch_y, exch_rows)

        # --- Hand cards ---
        cw = self.hand_card_size; gap = HAND_CARD_GAP; cols = 5
        max_rows = max(1, (hand_cards_bottom - hand_cards_top) // (cw + gap))

        for i, card in enumerate(current.hand):
            col = i % cols
            row = i // cols
            if row >= max_rows:
                break
            cx_ = self.hand_x + 10 + col * (cw + gap)
            cy_ = hand_cards_top + row * (cw + gap)
            selected  = (card is self.selected_card)
            exch_sel  = (self.exchange_mode and self.selected_hand_card_idx == i)
            border = (0, 255, 70) if selected else (255, 200, 0) if exch_sel else (95, 95, 135)
            bw = 3 if (selected or exch_sel) else 1
            img = self.game.board.card_images.get(card.nom)
            if img:
                fitted = self._fit_image(img, cw - 4, cw - 4)
                fw, fh = fitted.get_size()
                pygame.draw.rect(self.screen, border, (cx_, cy_, cw, cw), bw)
                self.screen.blit(fitted, (cx_ + (cw - fw) // 2, cy_ + (cw - fh) // 2))
            else:
                pygame.draw.rect(self.screen, self._card_color(card), (cx_, cy_, cw, cw))
                pygame.draw.rect(self.screen, border, (cx_, cy_, cw, cw), bw)
                self.screen.blit(self.font_small.render(card.nom[:9], True, (220, 220, 220)),
                                 (cx_ + 3, cy_ + cw // 2 - 7))
            # Zone colour dot
            pygame.draw.circle(self.screen, self._card_color(card), (cx_ + cw - 8, cy_ + 8), 5)

    def _draw_exchange_in_hand(self, exch_y, exch_rows):
        """Draw the exchange section inside the hand panel."""
        hs = self.hand_card_size
        self.screen.blit(
            self.font_small.render(f"ECHANGE ({len(self.game.exchange)})", True, (155, 150, 195)),
            (self.hand_x + 10, exch_y + 4))

        for i, card in enumerate(self.game.exchange):
            col = i % self.exch_cols
            row = i // self.exch_cols
            if row >= 4:
                break
            cx_ = self.hand_x + 10 + col * (hs + EXCH_GAP)
            cy_ = exch_y + 24 + row * (hs + EXCH_GAP)
            selected = (self.exchange_mode and self.selected_exchange_card_idx == i)
            border = (255, 200, 0) if selected else (75, 75, 115)
            bw = 2 if selected else 1
            img = self.game.board.card_images.get(card.nom)
            if img:
                fitted = self._fit_image(img, hs - 2, hs - 2)
                fw, fh = fitted.get_size()
                pygame.draw.rect(self.screen, border, (cx_, cy_, hs, hs), bw)
                self.screen.blit(fitted, (cx_ + (hs - fw) // 2, cy_ + (hs - fh) // 2))
            else:
                pygame.draw.rect(self.screen, self._card_color(card), (cx_, cy_, hs, hs))
                pygame.draw.rect(self.screen, border, (cx_, cy_, hs, hs), bw)
                self.screen.blit(self.font_small.render(card.nom[:7], True, (220, 220, 220)),
                                 (cx_ + 2, cy_ + hs // 2 - 7))

    def _draw_hand_buttons(self, player, btn_y):
        bw = 118; bh = HAND_BTN_H; gap = HAND_BTN_GAP
        defs = {
            "draw":     ("Piocher",  (38, 82, 38),  (78, 175, 78),  bool(player.deck)),
            "exchange": ("Echanger", (38, 38, 82),  (78, 78, 175),  bool(self.game.exchange and player.hand)),
            "skip":     ("Passer",   (82, 38, 38),  (175, 78, 78),  True),
        }
        for name, rect in self.action_buttons.items():
            label, bg, border, active = defs[name]
            if not active:
                bg = (45, 45, 45); border = (75, 75, 75)
            pygame.draw.rect(self.screen, bg, rect)
            pygame.draw.rect(self.screen, border, rect, 2)
            lbl = self.font_small.render(label, True, (210, 210, 210))
            self.screen.blit(lbl, (rect.x + (rect.w - lbl.get_width()) // 2,
                                   rect.y + (rect.h - lbl.get_height()) // 2))
        acts = self.game.actions_remaining
        self.screen.blit(
            self.font_small.render(f"Actions restantes: {acts}/2", True, (175, 175, 95)),
            (self.hand_x + 10, btn_y + bh + 4))

    # -------------------------------------------------------------------------
    # Dragged card
    # -------------------------------------------------------------------------

    def _draw_dragged_card(self):
        card = self.dragging_card
        size = self.hand_card_size + 14
        dx = self.mouse_pos[0] - size // 2
        dy = self.mouse_pos[1] - size // 2
        img = self.game.board.card_images.get(card.nom)
        if img:
            fitted = self._fit_image(img, size, size)
            s = fitted.copy()
            s.set_alpha(215)
            self.screen.blit(s, (dx, dy))
        else:
            s = pygame.Surface((size, size), pygame.SRCALPHA)
            bg = self._card_color(card)
            pygame.draw.rect(s, bg + (185,), (0, 0, size, size))
            self.screen.blit(s, (dx, dy))
        pygame.draw.rect(self.screen, self._card_color(card), (dx, dy, size, size), 2)

    # -------------------------------------------------------------------------
    # Tooltip
    # -------------------------------------------------------------------------

    def _update_tooltip(self):
        mx, my = self.mouse_pos
        self.tooltip_card = None
        current = self.game.players[self.game.current_player]

        if current.is_human and self.hand_x <= mx <= self.hand_x + self.hand_w:
            idx = self._hand_idx_at(mx, my, current)
            if idx is not None and 0 <= idx < len(current.hand):
                self.tooltip_card = current.hand[idx]
                return
            ei = self._exchange_idx_at(mx, my)
            if ei is not None and 0 <= ei < len(self.game.exchange):
                self.tooltip_card = self.game.exchange[ei]
                return

        # Exterior strip (non-siege cards displayed below castle)
        ext_card = self._ext_card_at(mx, my)
        if ext_card:
            self.tooltip_card = ext_card
            return

        grid = self._grid_from_px(mx, my)
        if grid is not None:
            tx, ty = grid
            if 0 <= tx < 4 and 0 <= ty < 4 and self.game.board.cour[ty][tx]:
                self.tooltip_card = self.game.board.cour[ty][tx]
                return
            if (tx, ty) in self.game.board.tiles and self.game.board.tiles[(tx, ty)]["card"]:
                self.tooltip_card = self.game.board.tiles[(tx, ty)]["card"]
                return
            if (tx, ty) in self.game.board.exterieur:
                self.tooltip_card = self.game.board.exterieur[(tx, ty)]

    def _draw_tooltip(self):
        if not self.tooltip_card:
            return
        c = self.tooltip_card
        mx, my = self.mouse_pos

        # Helper to draw a card image box at (tx,ty) with size tw,th and optionally a pawn dot
        def draw_card_box(card_obj, tx, ty, tw, th):
            img = self.game.board.card_images.get(card_obj.nom)
            if img:
                fitted = self._fit_image(img, tw, th)
                fw, fh = fitted.get_size()
                self.screen.blit(fitted, (tx + (tw - fw) // 2, ty + (th - fh) // 2))
            else:
                pygame.draw.rect(self.screen, self._card_color(card_obj), (tx, ty, tw, th))
                self.screen.blit(self.font_small.render(card_obj.nom[:10], True, (230, 230, 230)), (tx + 4, ty + th // 2 - 7))
            owner = getattr(card_obj, 'pion_owner', None)
            if owner:
                pygame.draw.circle(self.screen, self._pawn_color(owner), (tx + 10, ty + 10), max(5, tw // 18))

        if self.advanced_tooltip:
            # Advanced: if this is a chevalier protecting another card, show the stack
            stack = []
            cur = c
            stack.append(cur)
            while getattr(cur, 'protects', None):
                cur = cur.protects
                stack.append(cur)
            # If the selected card is the protected (not the chevalier), try to find its chevalier
            if getattr(c, 'protected', False) and not getattr(c, 'protects', None):
                # search for chevalier on that cell
                # Try to find top card at the last mouse-overed grid
                grid = self._grid_from_px(mx, my)
                if grid:
                    txg, tyg = grid
                    top = self.game.board.cour[tyg][txg]
                    if top and getattr(top, 'protects', None) is c:
                        stack.insert(0, top)
            # Draw stack vertically, largest on top
            if stack:
                tw = max(80, int(self.hand_card_size * 0.9))
                th = max(80, int(self.hand_card_size * 0.9))
                total_h = len(stack) * (th + 6) - 6
                tx = mx + 15 if mx + 15 + tw < self.sw else mx - tw - 15
                ty = my + 15 if my + 15 + total_h < self.sh else my - total_h - 15
                for i, card_obj in enumerate(stack):
                    draw_card_box(card_obj, tx, ty + i * (th + 6), tw, th)
                return
            # Fallback: show single image
            img = self.game.board.card_images.get(c.nom)
            if img:
                ow, oh = img.get_size()
                tw = max(80, int(ow * 0.20))
                th = max(80, int(oh * 0.20))
                tx = mx + 15 if mx + 15 + tw < self.sw else mx - tw - 15
                ty = my + 15 if my + 15 + th < self.sh else my - th - 15
                scaled = pygame.transform.smoothscale(img, (tw, th))
                s = scaled.copy(); s.set_alpha(230)
                self.screen.blit(s, (tx, ty))
                pygame.draw.rect(self.screen, self._card_color(c), (tx, ty, tw, th), 2)
                return

        # Basic text tooltip
        action_text = getattr(c, "action", "") or ""
        cond_text = c.condition if c.condition else "-"
        lines = [c.nom, f"Zone: {c.lieu}", f"Cond: {cond_text}"]
        while action_text:
            lines.append(action_text[:48])
            action_text = action_text[48:]

        tw = max(200, max(len(l) for l in lines) * 8 + 20)
        th = len(lines) * 18 + 14
        tx = mx + 15 if mx + 15 + tw < self.sw else mx - tw - 15
        ty = my + 15 if my + 15 + th < self.sh else my - th - 15

        pygame.draw.rect(self.screen, (38, 38, 55), (tx, ty, tw, th))
        pygame.draw.rect(self.screen, (145, 145, 195), (tx, ty, tw, th), 1)
        pygame.draw.rect(self.screen, self._card_color(c), (tx, ty, 4, th))
        for i, line in enumerate(lines):
            col = (255, 235, 90) if i == 0 else (210, 210, 210)
            self.screen.blit(self.font_small.render(line, True, col), (tx + 8, ty + 7 + i * 18))

    # -------------------------------------------------------------------------
    # Win overlay
    # -------------------------------------------------------------------------

    def _draw_win_overlay(self):
        overlay = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        is_human = getattr(self.winner, "is_human", False) if self.winner else False
        title_txt = "VICTOIRE !" if is_human else "L ordinateur a gagne"
        color = (255, 220, 50) if is_human else (220, 100, 80)

        title = self.font_big.render(title_txt, True, color)
        self.screen.blit(title, (self.sw // 2 - title.get_width() // 2, self.sh // 2 - 55))
        sub = self.font.render("Appuyez sur ESC pour quitter", True, (200, 200, 200))
        self.screen.blit(sub, (self.sw // 2 - sub.get_width() // 2, self.sh // 2 + 28))

    # -------------------------------------------------------------------------
    # Main loop
    # -------------------------------------------------------------------------

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
