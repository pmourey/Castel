"""
Tests unitaires pour les effets de chaque carte du jeu Castel.
Couvre les 37 types de cartes dfinis dans Inventaire.csv.
"""
import unittest
from engine.game import GameState
from engine.card import Card, CARDS
from engine.effects import CardEffects


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_card(nom, couleur='Rouge', lieu='Arrive  la cour'):
    return Card(couleur, nom, 1, lieu, '', '')


def make_game():
    """Return a fresh 2-player game with a cleared board for controlled testing."""
    game = GameState(num_players=2)
    game.board.cour = [[None] * 4 for _ in range(4)]
    game.exchange.clear()
    for p in game.players:
        p.hand.clear()
        p.deck.clear()
    game.last_displaced_card = None
    game.previous_placed_card = None
    game.last_placed_card = None
    return game


def apply(game, card_nom, player=None, position=(0, 0)):
    """Directly call an effect by CSV card name."""
    if player is None:
        player = game.players[0]
    card = make_card(card_nom)
    effect_fn = CardEffects.parse_effect(card_nom, '')
    effect_fn(game, player, card, position)


def place_in_cour(game, card, x, y, owner=None):
    if owner:
        card.pion_owner = owner
    game.board.cour[y][x] = card


def place_on_tile(game, card, pos, owner=None):
    if owner:
        card.pion_owner = owner
    game.board.tiles[pos]['card'] = card


def place_in_ext(game, card, pos, owner=None):
    if owner:
        card.pion_owner = owner
    game.board.exterieur[pos] = card


# ---------------------------------------------------------------------------
# Tests: lookup
# ---------------------------------------------------------------------------

class TestEffectLookup(unittest.TestCase):
    ALL_NAMES = [
        'Fantome', 'Guetteur', 'Magicien', 'Archer', 'Sorciere', 'Alchimiste',
        'Capitaine', 'Traitre', 'Soldat',
        'Marchand', 'Roi', 'Baladin', 'Courtisane', 'Reine', 'Princesse', 'Prince',
        'Intriguant', 'Espion', 'Ambassadeur', 'Voleur', 'Bouffon', 'Fou', 'Pretre',
        'Dame_de_compagnie', 'Courtisan', 'Assassin', 'Conseiller_du_roi',
        'Favorite', 'Prince_charmant', 'Chevalier_noir',
        'Barbare', 'Fee', 'Enchanteur', 'Engin_de_siege', 'Dragon', 'Herault',
        'Chevalier',
    ]

    def test_all_37_names_resolve(self):
        for name in self.ALL_NAMES:
            fn = CardEffects.parse_effect(name, '')
            self.assertIsNot(fn, CardEffects.default_effect,
                             f"'{name}' resolves to default_effect (name mismatch)")

    def test_all_csv_cards_have_effect(self):
        for nom in {c.nom for c in CARDS}:
            fn = CardEffects.parse_effect(nom, '')
            self.assertIsNot(fn, CardEffects.default_effect,
                             f"CSV card '{nom}' has no effect")


# ---------------------------------------------------------------------------
# Tests: Bleu
# ---------------------------------------------------------------------------

class TestBleuEffects(unittest.TestCase):
    def test_fantome_displaces_existing_tower_card(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Roi')
        victim.pion_owner = player
        game.last_displaced_card = victim
        apply(game, 'Fantome', player, (-1, -1))
        self.assertIn(victim, player.hand)
        self.assertIsNone(game.last_displaced_card)

    def test_fantome_no_victim_is_safe(self):
        game = make_game()
        game.last_displaced_card = None
        apply(game, 'Fantome')
        self.assertEqual(len(game.exchange), 0)

    def test_guetteur_moves_soldat_off_rempart(self):
        game = make_game()
        soldat = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        rempart_positions = [pos for pos, t in game.board.tiles.items() if t['type'] == 'rempart']
        src = rempart_positions[0]
        place_on_tile(game, soldat, src)
        apply(game, 'Guetteur', position=(-1, -1))
        self.assertIsNot(game.board.tiles[src]['card'], soldat)

    def test_guetteur_no_soldat_is_safe(self):
        game = make_game()
        apply(game, 'Guetteur', position=(-1, -1))
        self.assertEqual(len(game.exchange), 0)

    def test_magicien_removes_cour_card_to_exchange(self):
        game = make_game()
        victim = make_card('Roi')
        place_in_cour(game, victim, 1, 1)
        apply(game, 'Magicien', position=(-1, 0))
        self.assertIn(victim, game.exchange)
        self.assertIsNone(game.board.cour[1][1])

    def test_archer_removes_exterior_card(self):
        game = make_game()
        player = game.players[0]
        ext_card = make_card('Barbare', 'Vert')
        ext_card.pion_owner = player
        place_in_ext(game, ext_card, (7, 0), owner=player)
        apply(game, 'Archer', position=(-1, 1))
        self.assertNotIn((7, 0), game.board.exterieur)
        self.assertIn(ext_card, player.hand)

    def test_archer_empty_exterior_is_safe(self):
        game = make_game()
        apply(game, 'Archer')

    def test_sorciere_moves_exchange_to_player(self):
        game = make_game()
        ex_card = make_card('Roi')
        game.exchange.append(ex_card)
        total_before = sum(len(p.hand) for p in game.players)
        apply(game, 'Sorciere')
        self.assertEqual(len(game.exchange), 0)
        self.assertEqual(sum(len(p.hand) for p in game.players), total_before + 1)

    def test_alchimiste_swaps_two_hand_cards(self):
        game = make_game()
        player = game.players[0]
        h1, h2 = make_card('Roi'), make_card('Reine')
        e1, e2 = make_card('Prince'), make_card('Princesse')
        player.hand += [h1, h2]
        game.exchange += [e1, e2]
        apply(game, 'Alchimiste', player)
        self.assertIn(e1, player.hand)
        self.assertIn(e2, player.hand)
        self.assertNotIn(h1, player.hand)


# ---------------------------------------------------------------------------
# Tests: Orange
# ---------------------------------------------------------------------------

class TestOrangeEffects(unittest.TestCase):
    def test_capitaine_protects_rempart_soldiers(self):
        game = make_game()
        s1 = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        remparts = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        place_on_tile(game, s1, remparts[0])
        apply(game, 'Capitaine', position=remparts[1])
        self.assertTrue(getattr(s1, 'protected', False))

    def test_traitre_removes_cour_card(self):
        game = make_game()
        victim = make_card('Roi')
        place_in_cour(game, victim, 2, 2)
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        apply(game, 'Traitre', position=rempart_pos)
        self.assertIsNone(game.board.cour[2][2])

    def test_soldat_fourth_triggers_engine_removal(self):
        game = make_game()
        remparts = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        for i in range(3):
            place_on_tile(game, make_card('Soldat', 'Orange'), remparts[i])
        # The 4th soldat must be ON the board when the effect fires (mimics place_card behaviour)
        fourth_soldat = make_card('Soldat', 'Orange')
        place_on_tile(game, fourth_soldat, remparts[3])
        engine = make_card('Engin_de_siege', 'Vert')
        place_in_ext(game, engine, (7, 1))
        CardEffects.soldat_effect(game, game.players[0], fourth_soldat, remparts[3])
        self.assertNotIn((7, 1), game.board.exterieur)

    def test_soldat_fewer_than_four_no_removal(self):
        game = make_game()
        engine = make_card('Engin_de_siege', 'Vert')
        place_in_ext(game, engine, (7, 1))
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        apply(game, 'Soldat', position=rempart_pos)
        self.assertIn((7, 1), game.board.exterieur)


# ---------------------------------------------------------------------------
# Tests: Rouge
# ---------------------------------------------------------------------------

class TestRougeEffects(unittest.TestCase):
    def test_roi_removes_cour_card(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Courtisan')
        victim.pion_owner = player
        place_in_cour(game, victim, 1, 0)
        roi = make_card('Roi')
        place_in_cour(game, roi, 0, 0)
        CardEffects.roi_effect(game, player, roi, (0, 0))
        self.assertIsNone(game.board.cour[1][0])

    def test_reine_removes_cour_card(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Courtisan')
        victim.pion_owner = player
        place_in_cour(game, victim, 2, 2)
        reine = make_card('Reine')
        place_in_cour(game, reine, 0, 0)
        CardEffects.reine_effect(game, player, reine, (0, 0))
        self.assertIsNone(game.board.cour[2][2])

    def test_baladin_swaps_adjacent_cards(self):
        game = make_game()
        player = game.players[0]
        c1, c2, bal = make_card('Roi'), make_card('Reine'), make_card('Baladin')
        place_in_cour(game, bal, 1, 1)
        place_in_cour(game, c1, 0, 1)
        place_in_cour(game, c2, 2, 1)
        CardEffects.baladin_effect(game, player, bal, (1, 1))
        self.assertIs(game.board.cour[1][0], c2)
        self.assertIs(game.board.cour[1][2], c1)

    def test_courtisane_swaps_hand_cards(self):
        game = make_game()
        p0, p1 = game.players[0], game.players[1]
        c0, c1 = make_card('Roi'), make_card('Reine')
        p0.hand.append(c0)
        p1.hand.append(c1)
        CardEffects.courtisane_effect(game, p0, make_card('Courtisane'), (0, 0))
        self.assertIn(c1, p0.hand)
        self.assertIn(c0, p1.hand)

    def test_princesse_moves_chevalier(self):
        game = make_game()
        chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        place_in_cour(game, chev, 2, 2)
        apply(game, 'Princesse')
        self.assertIsNone(game.board.cour[2][2])

    def test_ambassadeur_is_protected(self):
        game = make_game()
        amb = make_card('Ambassadeur')
        CardEffects.ambassadeur_effect(game, game.players[0], amb, (0, 0))
        self.assertTrue(amb.protected)

    def test_voleur_marks_neighbor(self):
        game = make_game()
        neighbor = make_card('Roi')
        place_in_cour(game, neighbor, 1, 0)
        apply(game, 'Voleur', position=(0, 0))
        self.assertTrue(getattr(neighbor, 'stolen', False))

    def test_bouffon_passes_cards_left(self):
        game = make_game()
        p0, p1 = game.players[0], game.players[1]
        c0, c1 = make_card('Roi'), make_card('Reine')
        p0.hand.append(c0)
        p1.hand.append(c1)
        apply(game, 'Bouffon')
        self.assertIn(c1, p0.hand)
        self.assertIn(c0, p1.hand)

    def test_fou_steals_from_right_neighbor(self):
        game = make_game()
        p0, p1 = game.players[0], game.players[1]
        c1 = make_card('Reine')
        p1.hand.append(c1)
        apply(game, 'Fou', player=p0)
        self.assertIn(c1, p0.hand)
        self.assertNotIn(c1, p1.hand)

    def test_intriguant_swaps_two_cour_cards(self):
        game = make_game()
        c1, c2, intr = make_card('Roi'), make_card('Reine'), make_card('Intriguant')
        place_in_cour(game, intr, 0, 0)
        place_in_cour(game, c1, 1, 0)
        place_in_cour(game, c2, 2, 0)
        CardEffects.intrigant_effect(game, game.players[0], intr, (0, 0))
        pos1, pos2 = game.board.cour[0][1], game.board.cour[0][2]
        self.assertIn(pos1, [c1, c2])
        self.assertIn(pos2, [c1, c2])
        self.assertIsNot(pos1, pos2)

    def test_courtisan_removes_neighbor(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Roi')
        victim.pion_owner = player
        place_in_cour(game, victim, 1, 0)
        CardEffects.courtisan_effect(game, player, make_card('Courtisan'), (0, 0))
        self.assertIsNone(game.board.cour[0][1])

    def test_assassin_removes_neighbor_permanently(self):
        game = make_game()
        victim = make_card('Reine')
        place_in_cour(game, victim, 1, 0)
        CardEffects.assassin_effect(game, game.players[0], make_card('Assassin'), (0, 0))
        self.assertIsNone(game.board.cour[0][1])
        self.assertNotIn(victim, game.exchange)

    def test_assassin_spares_roi(self):
        game = make_game()
        roi = make_card('Roi')
        place_in_cour(game, roi, 1, 0)
        CardEffects.assassin_effect(game, game.players[0], make_card('Assassin'), (0, 0))
        self.assertIs(game.board.cour[0][1], roi)

    def test_pretre_protects_neighbors(self):
        game = make_game()
        neighbor = make_card('Roi')
        place_in_cour(game, neighbor, 1, 0)
        CardEffects.pretre_effect(game, game.players[0], make_card('Pretre'), (0, 0))
        self.assertTrue(getattr(neighbor, 'protected', False))

    def test_marchand_grants_extra_action(self):
        game = make_game()
        player = game.players[0]
        CardEffects.marchand_effect(game, player, make_card('Marchand'), (0, 0))
        self.assertGreater(getattr(player, 'extra_actions', 0), 0)

    def test_prince_marks_king_substitute(self):
        game = make_game()
        prince = make_card('Prince')
        CardEffects.prince_effect(game, game.players[0], prince, (1, 1))
        self.assertTrue(getattr(prince, 'king_substitute', False))

    def test_espion_swaps_neighbor_pions(self):
        game = make_game()
        c1, c2, esp = make_card('Roi'), make_card('Reine'), make_card('Espion')
        place_in_cour(game, esp, 1, 1)
        place_in_cour(game, c1, 0, 1)
        place_in_cour(game, c2, 2, 1)
        CardEffects.espion_effect(game, game.players[0], esp, (1, 1))
        self.assertIs(game.board.cour[1][0], c2)
        self.assertIs(game.board.cour[1][2], c1)

    def test_favorite_marks_can_move_king(self):
        game = make_game()
        fav = make_card('Favorite')
        CardEffects.favorite_effect(game, game.players[0], fav, (0, 0))
        self.assertTrue(getattr(fav, 'can_move_king', False))

    def test_dame_compagnie_removes_male_neighbor(self):
        game = make_game()
        roi = make_card('Roi')
        place_in_cour(game, roi, 1, 0)
        CardEffects.dame_compagnie_effect(game, game.players[0], make_card('Dame_de_compagnie'), (0, 0))
        self.assertIsNone(game.board.cour[0][1])

    def test_prince_charmant_removes_female(self):
        game = make_game()
        reine = make_card('Reine')
        place_in_cour(game, reine, 2, 0)
        CardEffects.prince_charmant_effect(game, game.players[0], make_card('Prince_charmant'), (0, 0))
        self.assertIsNone(game.board.cour[0][2])

    def test_chevalier_noir_removes_chevalier_neighbor(self):
        game = make_game()
        chev = make_card('Chevalier', 'Violet')
        place_in_cour(game, chev, 1, 0)
        CardEffects.chevalier_noir_effect(game, game.players[0], make_card('Chevalier_noir'), (0, 0))
        self.assertIsNone(game.board.cour[0][1])

    def test_conseiller_roi_places_exchange_card(self):
        game = make_game()
        ex_card = make_card('Reine')
        game.exchange.append(ex_card)
        CardEffects.conseiller_roi_effect(game, game.players[0], make_card('Conseiller_du_roi'), (0, 0))
        found = any(game.board.cour[y][x] is ex_card for y in range(4) for x in range(4))
        self.assertTrue(found)
        self.assertNotIn(ex_card, game.exchange)

    def test_herault_sets_must_play_king(self):
        game = make_game()
        CardEffects.herault_effect(game, game.players[0], make_card('Herault'), (5, 0))
        for p in game.players:
            self.assertTrue(getattr(p, 'must_play_king', False))


# ---------------------------------------------------------------------------
# Tests: Vert
# ---------------------------------------------------------------------------

class TestVertEffects(unittest.TestCase):
    def test_barbare_removes_tile_card(self):
        game = make_game()
        tile_card = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        place_on_tile(game, tile_card, tour_pos)
        apply(game, 'Barbare', position=(6, 0))
        self.assertIsNone(game.board.tiles[tour_pos]['card'])

    def test_barbare_empty_tiles_is_safe(self):
        game = make_game()
        apply(game, 'Barbare', position=(6, 0))

    def test_fee_moves_cour_card_to_exterior(self):
        game = make_game()
        victim = make_card('Roi')
        place_in_cour(game, victim, 1, 1)
        apply(game, 'Fee', position=(6, 0))
        self.assertIsNone(game.board.cour[1][1])
        self.assertIn(victim, game.board.exterieur.values())

    def test_fee_empty_cour_is_safe(self):
        game = make_game()
        apply(game, 'Fee', position=(6, 0))

    def test_enchanteur_returns_previous_card(self):
        game = make_game()
        player = game.players[0]
        previous = make_card('Roi')
        previous.pion_owner = player
        place_in_cour(game, previous, 1, 1)
        game.previous_placed_card = previous
        CardEffects.enchanteur_effect(game, player, make_card('Enchanteur'), (6, 0))
        self.assertIsNone(game.board.cour[1][1])
        self.assertIn(previous, player.hand)

    def test_enchanteur_no_previous_is_safe(self):
        game = make_game()
        game.previous_placed_card = None
        apply(game, 'Enchanteur', position=(6, 0))

    def test_engin_siege_fourth_removes_soldiers(self):
        game = make_game()
        remparts = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        for i in range(3):
            place_on_tile(game, make_card('Soldat', 'Orange'), remparts[i])
        for i in range(3):
            place_in_ext(game, make_card('Engin_de_siege', 'Vert'), (7 + i, 0))
        fourth = make_card('Engin_de_siege', 'Vert')
        place_in_ext(game, fourth, (10, 0))
        CardEffects.engin_siege_effect(game, game.players[0], fourth, (10, 0))
        for i in range(3):
            self.assertIsNone(game.board.tiles[remparts[i]]['card'])

    def test_engin_siege_fewer_than_four_is_safe(self):
        game = make_game()
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        s = make_card('Soldat', 'Orange')
        place_on_tile(game, s, rempart_pos)
        e = make_card('Engin_de_siege', 'Vert')
        place_in_ext(game, e, (7, 0))
        CardEffects.engin_siege_effect(game, game.players[0], e, (7, 0))
        self.assertIs(game.board.tiles[rempart_pos]['card'], s)

    def test_dragon_removes_exterior_and_tile_card(self):
        game = make_game()
        ext_card = make_card('Barbare', 'Vert')
        tile_card = make_card('Soldat', 'Orange')
        place_in_ext(game, ext_card, (7, 0))
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        place_on_tile(game, tile_card, tour_pos)
        apply(game, 'Dragon', position=(8, 0))
        self.assertNotIn((7, 0), game.board.exterieur)
        self.assertIsNone(game.board.tiles[tour_pos]['card'])

    def test_dragon_empty_board_is_safe(self):
        game = make_game()
        apply(game, 'Dragon', position=(8, 0))


# ---------------------------------------------------------------------------
# Tests: Violet
# ---------------------------------------------------------------------------

class TestVioletEffects(unittest.TestCase):
    def test_chevalier_protects_card_below(self):
        game = make_game()
        chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        CardEffects.chevalier_effect(game, game.players[0], chev, (0, 0))
        self.assertTrue(getattr(chev, 'protecting', False))


# ---------------------------------------------------------------------------
# Tests: can_place_card zone routing
# ---------------------------------------------------------------------------

class TestCanPlaceCard(unittest.TestCase):
    def test_rouge_allowed_in_cour(self):
        game = make_game()
        card = make_card('Roi', 'Rouge', 'Arrive à la cour')
        self.assertTrue(game.can_place_card(card, (0, 0)))

    def test_rouge_rejected_on_tour(self):
        game = make_game()
        card = make_card('Roi', 'Rouge', 'Arrive à la cour')
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        self.assertFalse(game.can_place_card(card, tour_pos))

    def test_bleu_allowed_on_tour(self):
        game = make_game()
        card = make_card('Fantome', 'Bleu', 'Arrive dans une tour')
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        self.assertTrue(game.can_place_card(card, tour_pos))

    def test_bleu_rejected_in_cour(self):
        game = make_game()
        card = make_card('Fantome', 'Bleu', 'Arrive dans une tour')
        self.assertFalse(game.can_place_card(card, (0, 0)))

    def test_orange_allowed_on_rempart(self):
        game = make_game()
        card = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        self.assertTrue(game.can_place_card(card, rempart_pos))

    def test_orange_rejected_in_cour(self):
        game = make_game()
        card = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        self.assertFalse(game.can_place_card(card, (0, 0)))

    def test_vert_allowed_in_exterior(self):
        game = make_game()
        card = make_card('Dragon', 'Vert', 'Arrive hors les murs')
        self.assertTrue(game.can_place_card(card, (8, 0)))

    def test_vert_engin_siege_must_face_rempart(self):
        """Engin de siege must be adjacent to a rempart tile."""
        game = make_game()
        card = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        # Position (8, 0) is not adjacent to any rempart — should be rejected
        self.assertFalse(game.can_place_card(card, (8, 0)))
        # Position (-2, 0) is adjacent to left rempart (-1, 0) — should be accepted
        self.assertTrue(game.can_place_card(card, (-2, 0)))
        # Position (5, 2) is adjacent to right rempart (4, 2) — should be accepted
        self.assertTrue(game.can_place_card(card, (5, 2)))
        # Position (1, -2) is adjacent to top rempart (1, -1) — should be accepted
        self.assertTrue(game.can_place_card(card, (1, -2)))
        # Position (3, 5) is adjacent to bottom rempart (3, 4) — should be accepted
        self.assertTrue(game.can_place_card(card, (3, 5)))

    def test_vert_rejected_in_cour(self):
        game = make_game()
        card = make_card('Dragon', 'Vert', 'Arrive hors les murs')
        self.assertFalse(game.can_place_card(card, (0, 0)))

    def test_chevalier_allowed_on_occupied_cour_cell(self):
        game = make_game()
        card = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        existing = make_card('Roi')
        place_in_cour(game, existing, 2, 2)
        self.assertTrue(game.can_place_card(card, (2, 2)))

    def test_chevalier_rejected_on_empty_cour_cell(self):
        game = make_game()
        card = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        self.assertFalse(game.can_place_card(card, (0, 0)))  # empty cell

    def test_chevalier_rejected_on_rempart(self):
        game = make_game()
        card = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        self.assertFalse(game.can_place_card(card, rempart_pos))

    def test_engin_siege_only_one_per_rempart_face(self):
        """Two engins de siege cannot face the same rempart."""
        game = make_game()
        card = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        first = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        # Place one engin at (-2, 1) facing rempart (-1, 1)
        game.board.exterieur[(-2, 1)] = first
        # Now try to place a second engin at the ONLY position facing (-1, 1) — should fail
        self.assertFalse(game.can_place_card(card, (-2, 1)))
        # But placing at (-2, 2) facing rempart (-1, 2) should still work
        self.assertTrue(game.can_place_card(card, (-2, 2)))

    def test_non_siege_vert_accepted_anywhere_exterior(self):
        """Non-siege vert cards (Dragon, Barbare, etc.) can go anywhere exterior."""
        game = make_game()
        card = make_card('Dragon', 'Vert', 'Arrive hors les murs')
        # Far from castle — accepted
        self.assertTrue(game.can_place_card(card, (8, 0)))
        # Adjacent to rempart — also accepted (no rempart-adjacency constraint for non-siege)
        self.assertTrue(game.can_place_card(card, (-2, 0)))


# ---------------------------------------------------------------------------
# Tests: Chevalier stacking
# ---------------------------------------------------------------------------

class TestChevalierStacking(unittest.TestCase):
    def test_place_card_sets_protects_on_chevalier(self):
        """When Chevalier is placed on an occupied cell, card.protects is set."""
        game = make_game()
        player = game.players[0]
        # Place a Roi in the cour
        roi = make_card('Roi', 'Rouge', 'Arrive a la cour')
        game.board.cour[0][0] = roi
        # Give player a Chevalier
        chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        chev.pion_owner = None
        player.hand.append(chev)
        result = game.place_card(player, chev, (0, 0))
        self.assertNotEqual(result, False, "Chevalier placement should succeed")
        self.assertEqual(chev.protects, roi, "Chevalier.protects should reference the Roi")

    def test_place_card_marks_protected_card(self):
        """The card under a Chevalier gets protected=True."""
        game = make_game()
        player = game.players[0]
        roi = make_card('Roi', 'Rouge', 'Arrive a la cour')
        game.board.cour[1][1] = roi
        chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        chev.pion_owner = None
        player.hand.append(chev)
        game.place_card(player, chev, (1, 1))
        self.assertTrue(getattr(roi, 'protected', False), "Roi should be marked protected")

    def test_chevalier_on_chevalier(self):
        """A Chevalier can be placed on another Chevalier (rules p.122)."""
        game = make_game()
        player = game.players[0]
        first_chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        game.board.cour[2][2] = first_chev
        second_chev = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        second_chev.pion_owner = None
        player.hand.append(second_chev)
        result = game.place_card(player, second_chev, (2, 2))
        self.assertNotEqual(result, False, "Chevalier on Chevalier should be allowed")
        self.assertEqual(second_chev.protects, first_chev)


# ---------------------------------------------------------------------------
# Tests: AI siege engine search
# ---------------------------------------------------------------------------

class TestAISiegeSearch(unittest.TestCase):
    def test_ai_places_engin_at_siege_slot(self):
        """AI finds a valid siege slot for Engin_de_siege."""
        game = make_game()
        ai = game.players[1]
        ai.hand = [make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')]
        ai.deck = []
        action = ai.choose_action(game)
        self.assertEqual(action[0], 'place')
        _, card, pos = action
        # Position should be adjacent to a rempart
        self.assertTrue(game.can_place_card(card, pos), f"AI chose invalid siege position {pos}")

    def test_ai_skips_engin_when_all_slots_taken(self):
        """AI does not loop when all siege slots are already taken."""
        from engine.ai import AIPlayer
        game = make_game()
        ai = game.players[1]
        # Fill all 16 siege slots
        for slot in [(-2, y) for y in range(4)] + [(5, y) for y in range(4)] + \
                    [(x, -2) for x in range(4)] + [(x, 5) for x in range(4)]:
            game.board.exterieur[slot] = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        ai.hand = [make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')]
        ai.deck = [make_card('Roi')]
        action = ai.choose_action(game)
        # Cannot place, so should draw or exchange or skip — never 'place'
        self.assertNotEqual(action[0], 'place', "AI should not try to place when all siege slots full")



class TestAIFallback(unittest.TestCase):
    def test_ai_draws_when_cannot_place(self):
        """AI should draw when no placement is possible but deck is not empty."""
        game = make_game()
        ai = game.players[1]
        # Give AI only exterior cards, but fill the exterior so it can't place either
        ai.hand = [make_card('Dragon', 'Vert', 'Arrive hors les murs')]
        for x in range(5, 25):
            for y in range(5):
                game.board.exterieur[(x, y)] = make_card('Barbare', 'Vert')
        ai.deck = [make_card('Roi')]
        action = ai.choose_action(game)
        self.assertEqual(action[0], 'draw', "AI should draw when no valid placement exists")

    def test_ai_exchanges_when_cannot_place_and_no_deck(self):
        """AI should exchange when no placement is possible and deck is empty."""
        game = make_game()
        ai = game.players[1]
        # Chevalier with empty cour — no valid target
        ai.hand = [make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')]
        ai.deck = []
        game.exchange = [make_card('Roi')]
        action = ai.choose_action(game)
        self.assertEqual(action[0], 'exchange', "AI should exchange when stuck and no deck")

    def test_ai_skips_when_fully_stuck(self):
        """AI should skip when no placement, no deck, no exchange."""
        game = make_game()
        ai = game.players[1]
        ai.hand = [make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')]
        ai.deck = []
        game.exchange = []
        action = ai.choose_action(game)
        self.assertEqual(action[0], 'skip', "AI should skip when fully stuck")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("CASTEL - Tests unitaires des effets de cartes")
    print("=" * 60)
    unittest.main(verbosity=2)
