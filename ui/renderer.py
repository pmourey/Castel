import pygame

# ============================================================================
# LAYOUT CONSTANTS
# ============================================================================
SCREEN_W, SCREEN_H = 1800, 900
CELL = 80  # castle tile pixel size

# Panel widths (left to right)
LEFT_W     = 130
CASTLE_W   = CELL * 6 + 20  # 500: tiles -1..4 + margins
EXCHANGE_W = 240
LOG_W      = 280
HAND_W     = SCREEN_W - LEFT_W - CASTLE_W - EXCHANGE_W - LOG_W  # 650

# Panel X origins
LEFT_X     = 0
CASTLE_X   = LEFT_X + LEFT_W          # 130
EXCHANGE_X = CASTLE_X + CASTLE_W      # 630
LOG_X      = EXCHANGE_X + EXCHANGE_W  # 870
HAND_X     = LOG_X + LOG_W            # 1150

# Vertical layout
TOP_H   = 75   # header
BTM_H   = 26   # footer
INNER_Y = TOP_H
INNER_H = SCREEN_H - TOP_H - BTM_H   # 799

# Castle coordinate system
# Tile at grid (tx,ty) maps to screen pixel (CASTLE_ORIGIN_X + tx*CELL, CASTLE_ORIGIN_Y + ty*CELL)
# tile(-1,-1) is at (CASTLE_X+20, INNER_Y+10) = (150, 85)
# So CASTLE_ORIGIN_X = CASTLE_X+20+CELL = 230, CASTLE_ORIGIN_Y = INNER_Y+10+CELL = 165
CASTLE_ORIGIN_X = CASTLE_X + 20 + CELL   # 230
CASTLE_ORIGIN_Y = INNER_Y + 10 + CELL    # 165
CASTLE_GRID_BOTTOM = CASTLE_ORIGIN_Y + 5 * CELL  # 565

# Exterior strip (green zone) below castle
EXTERIOR_LABEL_Y = CASTLE_GRID_BOTTOM + 4   # 569
EXTERIOR_Y       = EXTERIOR_LABEL_Y + 18    # 587
EXTERIOR_H       = SCREEN_H - BTM_H - EXTERIOR_Y  # 287


class CastelWindow:
    def __init__(self, game):
        self.game = game
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
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
        self.max_log_lines              = 35
        self.mouse_pos                  = (0, 0)
        self.tooltip_card               = None
        self.exchange_mode              = False
        self.selected_hand_card_idx     = None
        self.selected_exchange_card_idx = None
        self.action_buttons             = {}
        self.game_over                  = False
        self.winner                     = None
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

    def _castle_px(self, tx, ty):
        return (CASTLE_ORIGIN_X + tx * CELL, CASTLE_ORIGIN_Y + ty * CELL)

    def _grid_from_px(self, px, py):
        tx = (px - CASTLE_ORIGIN_X) // CELL
        ty = (py - CASTLE_ORIGIN_Y) // CELL
        sx = CASTLE_ORIGIN_X + tx * CELL
        sy = CASTLE_ORIGIN_Y + ty * CELL
        if sx <= px < sx + CELL and sy <= py < sy + CELL:
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
            label = self.font_small.render(card.nom[:10], True, (230, 230, 230))
            self.screen.blit(label, (px + 4, py + size // 2 - 7))

    def _next_ext_pos(self):
        for x in range(5, 50):
            for y in range(0, 5):
                if (x, y) not in self.game.board.exterieur and (x, y) not in self.game.board.tiles:
                    return (x, y)
        return None

    def _hand_idx_at(self, x, y, player):
        lx = x - (HAND_X + 10)
        ly = y - (INNER_Y + 32)
        if lx < 0 or ly < 0:
            return None
        col = lx // (CELL + 8)
        row = ly // (CELL + 8)
        idx = row * 5 + col
        if 0 <= col < 5 and 0 <= idx < len(player.hand):
            return idx
        return None

    def _exchange_idx_at(self, x, y):
        lx = x - (EXCHANGE_X + 8)
        ly = y - (INNER_Y + 26)
        if lx < 0 or ly < 0:
            return None
        cw, ch, gap = 52, 66, 4
        cols = 4
        col = lx // (cw + gap)
        row = ly // (ch + gap)
        idx = row * cols + col
        if 0 <= col < cols and 0 <= idx < len(self.game.exchange):
            return idx
        return None

    def _in_exterior_strip(self, x, y):
        return CASTLE_X <= x <= CASTLE_X + CASTLE_W and EXTERIOR_Y <= y <= EXTERIOR_Y + EXTERIOR_H

    # -------------------------------------------------------------------------
    # Create buttons inside hand panel
    # -------------------------------------------------------------------------

    def _create_action_buttons(self):
        bw, bh = 118, 36
        gap = 10
        by = INNER_Y + INNER_H - bh - 10
        self.action_buttons = {
            "draw":     pygame.Rect(HAND_X + 10,              by, bw, bh),
            "exchange": pygame.Rect(HAND_X + 10 + bw + gap,   by, bw, bh),
            "skip":     pygame.Rect(HAND_X + 10 + 2*(bw+gap), by, bw, bh),
        }

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

        # Action buttons
        for name, rect in self.action_buttons.items():
            if rect.collidepoint(x, y):
                self._handle_button(name, current)
                return

        # Exchange mode: click on exchange card
        if self.exchange_mode and EXCHANGE_X <= x <= EXCHANGE_X + EXCHANGE_W:
            ei = self._exchange_idx_at(x, y)
            if ei is not None:
                self.selected_exchange_card_idx = ei
                self.add_log(f"Echange: {self.game.exchange[ei].nom}")
                if self.selected_hand_card_idx is not None:
                    self._perform_exchange(current)
                return

        # Hand card click/drag
        if HAND_X <= x <= HAND_X + HAND_W and INNER_Y <= y <= SCREEN_H - BTM_H:
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
                col = idx % 5
                row = idx // 5
                cx = HAND_X + 10 + col * (CELL + 8) + CELL // 2
                cy = INNER_Y + 32 + row * (CELL + 8) + CELL // 2
                self.drag_offset = (x - cx, y - cy)
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

        # Castle grid (cour + tiles)
        grid = self._grid_from_px(x, y)
        if grid is not None:
            placed = self._try_place(current, self.dragging_card, grid)

        # Exterior strip
        if not placed and self._in_exterior_strip(x, y):
            cw = CELL
            gap = 4
            cols = (CASTLE_W - 10) // (cw + gap)
            lx = x - (CASTLE_X + 5)
            ly = y - EXTERIOR_Y
            col = max(0, lx // (cw + gap))
            row = max(0, ly // (cw + gap))
            sorted_ext = sorted(self.game.board.exterieur.keys())
            idx = row * cols + col
            if idx < len(sorted_ext):
                placed = self._try_place(current, self.dragging_card, sorted_ext[idx])
            if not placed:
                free = self._next_ext_pos()
                if free:
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
        self._draw_exchange_panel()
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
        title = self.font_title.render(f"CASTEL  -  Tour {self.game.turn}", True, (220, 220, 220))
        self.screen.blit(title, (HAND_X + 10, 10))
        who = "HUMAIN" if current.is_human else f"IA {self.game.current_player+1}"
        color = (80, 220, 80) if current.is_human else (220, 100, 100)
        info = self.font.render(
            f"Joueur {self.game.current_player+1}/{len(self.game.players)}  {who}"
            f"   Actions: {self.game.actions_remaining}/2"
            f"   Main: {len(current.hand)}  Pioche: {len(current.deck)}",
            True, color)
        self.screen.blit(info, (HAND_X + 10, 46))

    def _draw_footer(self):
        current = self.game.players[self.game.current_player]
        if current.is_human:
            hint = "Glisser carte sur plateau pour placer  |  Piocher / Echanger / Passer  |  ESC: Quitter"
        else:
            hint = "Tour de l ordinateur...   |   ESC: Quitter"
        self.screen.blit(self.font_small.render(hint, True, (90, 90, 110)), (10, SCREEN_H - BTM_H + 7))

    def _draw_left_panel(self):
        r = pygame.Rect(LEFT_X + 3, INNER_Y + 3, LEFT_W - 6, INNER_H - 6)
        pygame.draw.rect(self.screen, (26, 26, 38), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)
        y = INNER_Y + 12
        self.screen.blit(self.font_small.render("PIOCHES", True, (150, 150, 185)), (LEFT_X + 7, y))
        y += 20
        for i, p in enumerate(self.game.players):
            active = (i == self.game.current_player)
            color = (80, 210, 80) if active else (140, 140, 160)
            icon = ">" if active else " "
            self.screen.blit(self.font_small.render(f"{icon} J{i+1}", True, color), (LEFT_X + 5, y))
            y += 15
            self.screen.blit(self.font_small.render(f"  M:{len(p.hand)} P:{len(p.deck)}", True, (120, 120, 140)),
                             (LEFT_X + 5, y))
            y += 18

    def _draw_castle_panel(self):
        r = pygame.Rect(CASTLE_X + 3, INNER_Y + 3, CASTLE_W - 6, INNER_H - 6)
        pygame.draw.rect(self.screen, (23, 23, 36), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)

        # Courtyard background
        pygame.draw.rect(self.screen, (200, 185, 155),
                         (CASTLE_ORIGIN_X, CASTLE_ORIGIN_Y, 4 * CELL, 4 * CELL))
        pygame.draw.rect(self.screen, (140, 115, 75),
                         (CASTLE_ORIGIN_X, CASTLE_ORIGIN_Y, 4 * CELL, 4 * CELL), 2)

        # Castle tiles (tours + remparts)
        for (tx, ty), tile in self.game.board.tiles.items():
            px, py = self._castle_px(tx, ty)
            img_key = "Tour" if tile["type"] == "tour" else "Rempart"
            img = self.game.board.card_images.get(img_key)
            bg = (195, 165, 105) if tile["type"] == "tour" else (165, 145, 105)
            if img:
                cropped = self._fit_image(img, CELL, CELL)
                rot = tile.get("rotation", 0)
                if rot:
                    cropped = pygame.transform.rotate(cropped, rot * 90)
                self.screen.blit(cropped, (px, py))
            else:
                pygame.draw.rect(self.screen, bg, (px, py, CELL, CELL))
                pygame.draw.rect(self.screen, (100, 80, 50), (px, py, CELL, CELL), 1)
            if tile["card"]:
                self._draw_card_on_cell(tile["card"], px, py, CELL)

        # Cour grid + cards
        for cy in range(4):
            for cx in range(4):
                px, py = self._castle_px(cx, cy)
                pygame.draw.rect(self.screen, (135, 110, 70), (px, py, CELL, CELL), 1)
                if self.game.board.cour[cy][cx]:
                    self._draw_card_on_cell(self.game.board.cour[cy][cx], px, py, CELL)

        # Exterior strip label
        lbl = self.font_small.render("Hors les murs (zone verte) - glisser ici les cartes VERTES", True, (90, 180, 90))
        self.screen.blit(lbl, (CASTLE_X + 8, EXTERIOR_LABEL_Y))

        # Exterior strip background
        ext_r = pygame.Rect(CASTLE_X + 4, EXTERIOR_Y, CASTLE_W - 8, EXTERIOR_H - 2)
        pygame.draw.rect(self.screen, (18, 38, 18), ext_r)
        pygame.draw.rect(self.screen, (55, 125, 55), ext_r, 1)

        # Exterior cards
        cw = CELL
        gap = 4
        cols = (CASTLE_W - 10) // (cw + gap)
        for idx, (pos, card) in enumerate(sorted(self.game.board.exterieur.items())):
            col = idx % cols
            row = idx // cols
            ex = CASTLE_X + 5 + col * (cw + gap)
            ey = EXTERIOR_Y + 3 + row * (cw + gap)
            if ey + cw > EXTERIOR_Y + EXTERIOR_H:
                break
            self._draw_card_on_cell(card, ex, ey, cw)

    def _draw_exchange_panel(self):
        r = pygame.Rect(EXCHANGE_X + 3, INNER_Y + 3, EXCHANGE_W - 6, INNER_H - 6)
        pygame.draw.rect(self.screen, (26, 23, 38), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)
        self.screen.blit(
            self.font_small.render(f"ECHANGE ({len(self.game.exchange)})", True, (170, 165, 200)),
            (EXCHANGE_X + 10, INNER_Y + 10))

        cw, ch, gap = 52, 66, 4
        cols = 4
        ey = INNER_Y + 26
        for i, card in enumerate(self.game.exchange):
            col = i % cols
            row = i // cols
            cx_ = EXCHANGE_X + 8 + col * (cw + gap)
            cy_ = ey + row * (ch + gap)
            if cy_ + ch > INNER_Y + INNER_H - 6:
                break
            selected = (self.exchange_mode and self.selected_exchange_card_idx == i)
            border = (255, 200, 0) if selected else (75, 75, 115)
            bw = 2 if selected else 1
            img = self.game.board.card_images.get(card.nom)
            if img:
                fitted = self._fit_image(img, cw - 2, ch - 2)
                fw, fh = fitted.get_size()
                pygame.draw.rect(self.screen, border, (cx_, cy_, cw, ch), bw)
                self.screen.blit(fitted, (cx_ + (cw - fw) // 2, cy_ + (ch - fh) // 2))
            else:
                pygame.draw.rect(self.screen, self._card_color(card), (cx_, cy_, cw, ch))
                pygame.draw.rect(self.screen, border, (cx_, cy_, cw, ch), bw)
                self.screen.blit(
                    self.font_small.render(card.nom[:7], True, (220, 220, 220)),
                    (cx_ + 2, cy_ + ch // 2 - 7))

    def _draw_log_panel(self):
        r = pygame.Rect(LOG_X + 3, INNER_Y + 3, LOG_W - 6, INNER_H - 6)
        pygame.draw.rect(self.screen, (20, 20, 34), r)
        pygame.draw.rect(self.screen, (70, 70, 100), r, 1)
        self.screen.blit(self.font_small.render("JOURNAL", True, (150, 150, 185)), (LOG_X + 10, INNER_Y + 10))

        line_h = 15
        y = INNER_Y + 26
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
            self.screen.blit(self.font_small.render(trunc, True, col), (LOG_X + 8, y))
            y += line_h
            if y > INNER_Y + INNER_H - 10:
                break

    def _draw_hand_panel(self):
        current = self.game.players[self.game.current_player]
        r = pygame.Rect(HAND_X + 3, INNER_Y + 3, HAND_W - 6, INNER_H - 6)
        pygame.draw.rect(self.screen, (23, 23, 36), r)
        pygame.draw.rect(self.screen, (95, 95, 135), r, 2)

        who = "VOTRE MAIN" if current.is_human else f"IA {self.game.current_player+1}"
        color = (90, 215, 90) if current.is_human else (215, 95, 95)
        self.screen.blit(self.font.render(who, True, color), (HAND_X + 12, INNER_Y + 10))

        if not current.is_human:
            self.screen.blit(
                self.font_small.render("Tour de l ordinateur en cours...", True, (155, 135, 95)),
                (HAND_X + 12, INNER_Y + 34))
            return

        bh = 36
        by = INNER_Y + INNER_H - bh - 10
        pygame.draw.line(self.screen, (75, 75, 105),
                         (HAND_X + 8, by - 5), (HAND_X + HAND_W - 8, by - 5))
        self._draw_hand_buttons(current, by)

        # Cards
        cw = CELL
        gap = 8
        cols = 5
        start_y = INNER_Y + 32
        max_rows = max(1, (by - 6 - start_y) // (cw + gap))

        for i, card in enumerate(current.hand):
            col = i % cols
            row = i // cols
            if row >= max_rows:
                break
            cx_ = HAND_X + 10 + col * (cw + gap)
            cy_ = start_y + row * (cw + gap)
            selected = (card is self.selected_card)
            exch_sel = (self.exchange_mode and self.selected_hand_card_idx == i)
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
                self.screen.blit(
                    self.font_small.render(card.nom[:9], True, (220, 220, 220)),
                    (cx_ + 3, cy_ + cw // 2 - 7))
            pygame.draw.circle(self.screen, self._card_color(card), (cx_ + cw - 8, cy_ + 8), 5)

    def _draw_hand_buttons(self, player, by):
        bw, bh = 118, 36
        gap = 10
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
            (HAND_X + 10, by + bh + 4))

    def _draw_dragged_card(self):
        card = self.dragging_card
        size = CELL + 14
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

    def _update_tooltip(self):
        mx, my = self.mouse_pos
        self.tooltip_card = None
        current = self.game.players[self.game.current_player]

        if current.is_human and HAND_X <= mx <= HAND_X + HAND_W:
            idx = self._hand_idx_at(mx, my, current)
            if idx is not None and 0 <= idx < len(current.hand):
                self.tooltip_card = current.hand[idx]
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

        if EXCHANGE_X <= mx <= EXCHANGE_X + EXCHANGE_W:
            idx = self._exchange_idx_at(mx, my)
            if idx is not None and 0 <= idx < len(self.game.exchange):
                self.tooltip_card = self.game.exchange[idx]

    def _draw_tooltip(self):
        if not self.tooltip_card:
            return
        c = self.tooltip_card
        action_text = getattr(c, "action", "") or ""
        cond_text = c.condition if c.condition else "-"
        lines = [c.nom, f"Zone: {c.lieu}", f"Cond: {cond_text}"]
        while action_text:
            lines.append(action_text[:48])
            action_text = action_text[48:]

        tw = max(200, max(len(l) for l in lines) * 8 + 20)
        th = len(lines) * 18 + 14
        mx, my = self.mouse_pos
        tx = mx + 15 if mx + 15 + tw < SCREEN_W else mx - tw - 15
        ty = my + 15 if my + 15 + th < SCREEN_H else my - th - 15

        pygame.draw.rect(self.screen, (38, 38, 55), (tx, ty, tw, th))
        pygame.draw.rect(self.screen, (145, 145, 195), (tx, ty, tw, th), 1)
        pygame.draw.rect(self.screen, self._card_color(c), (tx, ty, 4, th))
        for i, line in enumerate(lines):
            col = (255, 235, 90) if i == 0 else (210, 210, 210)
            self.screen.blit(self.font_small.render(line, True, col), (tx + 8, ty + 7 + i * 18))

    def _draw_win_overlay(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 165))
        self.screen.blit(overlay, (0, 0))

        is_human = getattr(self.winner, "is_human", False) if self.winner else False
        title_txt = "VICTOIRE !" if is_human else "L ordinateur a gagne"
        color = (255, 220, 50) if is_human else (220, 100, 80)

        title = self.font_big.render(title_txt, True, color)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 55))
        sub = self.font.render("Appuyez sur ESC pour quitter", True, (200, 200, 200))
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, SCREEN_H // 2 + 28))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()
