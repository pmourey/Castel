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
        # Use an AI player so the effect acts immediately (human triggers pending_action)
        player = game.players[0]
        player.is_human = False
        soldat = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        rempart_positions = [pos for pos, t in game.board.tiles.items() if t['type'] == 'rempart']
        src = rempart_positions[0]
        place_on_tile(game, soldat, src)
        apply(game, 'Guetteur', player=player, position=(-1, -1))
        self.assertIsNot(game.board.tiles[src]['card'], soldat)

    def test_guetteur_no_soldat_is_safe(self):
        game = make_game()
        apply(game, 'Guetteur', position=(-1, -1))
        self.assertEqual(len(game.exchange), 0)

    def test_magicien_removes_cour_card_to_exchange(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        victim = make_card('Roi')
        place_in_cour(game, victim, 1, 1)
        apply(game, 'Magicien', player=player, position=(-1, 0))
        # AI resolves immediately: victim returned to owner or exchange
        self.assertIsNone(game.board.cour[1][1])

    def test_archer_removes_exterior_card(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        ext_card = make_card('Barbare', 'Vert')
        ext_card.pion_owner = player
        place_in_ext(game, ext_card, (7, 0), owner=player)
        apply(game, 'Archer', player=player, position=(-1, 1))
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
        player = game.players[0]
        player.is_human = False
        victim = make_card('Roi')
        place_in_cour(game, victim, 2, 2)
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        apply(game, 'Traitre', player=player, position=rempart_pos)
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
        player.is_human = False
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
        # Use AI player for immediate resolution; human gets interactive pending_action
        player = game.players[0]
        player.is_human = False
        reine = make_card('Reine')
        place_in_cour(game, reine, 2, 0)
        CardEffects.prince_charmant_effect(game, player, make_card('Prince_charmant'), (0, 0))
        self.assertIsNone(game.board.cour[0][2])

    def test_chevalier_noir_removes_chevalier_neighbor(self):
        game = make_game()
        chev = make_card('Chevalier', 'Violet')
        place_in_cour(game, chev, 1, 0)
        CardEffects.chevalier_noir_effect(game, game.players[0], make_card('Chevalier_noir'), (0, 0))
        self.assertIsNone(game.board.cour[0][1])

    def test_conseiller_roi_places_exchange_card(self):
        game = make_game()
        # Use AI player so the card is placed immediately
        player = game.players[0]
        player.is_human = False
        ex_card = make_card('Reine')
        game.exchange.append(ex_card)
        CardEffects.conseiller_roi_effect(game, player, make_card('Conseiller_du_roi'), (0, 0))
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
        player = game.players[0]
        player.is_human = False
        ext_card = make_card('Barbare', 'Vert')
        tile_card = make_card('Soldat', 'Orange')
        place_in_ext(game, ext_card, (7, 0))
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        place_on_tile(game, tile_card, tour_pos)
        apply(game, 'Dragon', player=player, position=(8, 0))
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

    def test_chevalier_allowed_on_occupied_rempart_tile(self):
        game = make_game()
        card = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        # Place a base card on a rempart tile
        rempart_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        base = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        place_on_tile(game, base, rempart_pos)
        self.assertTrue(game.can_place_card(card, rempart_pos))
        # Place chevalier on tile (must be in player's hand)
        game.players[0].hand.append(card)
        self.assertTrue(game.place_card(game.players[0], card, rempart_pos))
        # Now another chevalier should be allowed on same tile
        card2 = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        self.assertTrue(game.can_place_card(card2, rempart_pos))
        game.players[0].hand.append(card2)
        self.assertTrue(game.place_card(game.players[0], card2, rempart_pos))

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
# Tests: pion_owner & placement
# ---------------------------------------------------------------------------

class TestPionOwner(unittest.TestCase):
    """Verify that place_card correctly assigns pion_owner and pions_remaining."""

    def test_place_card_sets_pion_owner(self):
        game = make_game()
        player = game.players[0]
        card = make_card('Roi', 'Rouge', 'Arrive à la cour')
        player.hand.append(card)
        before_pions = player.pions_remaining
        game.place_card(player, card, (0, 0))
        self.assertIs(card.pion_owner, player)

    def test_place_card_decrements_pions(self):
        game = make_game()
        player = game.players[0]
        card = make_card('Reine', 'Rouge', 'Arrive à la cour')
        player.hand.append(card)
        before_pions = player.pions_remaining
        game.place_card(player, card, (0, 0))
        self.assertEqual(player.pions_remaining, before_pions - 1)

    def test_pion_owner_color_is_player_color(self):
        game = make_game()
        player = game.players[0]
        self.assertEqual(player.pions_color, 'black')   # first player is black (2-player)
        card = make_card('Baladin', 'Rouge', 'Arrive à la cour')
        player.hand.append(card)
        game.place_card(player, card, (0, 0))
        self.assertEqual(card.pion_owner.pions_color, 'black')


# ---------------------------------------------------------------------------
# Tests: extra_actions (Marchand) turn-flow integration
# ---------------------------------------------------------------------------

class TestMarchandTurnFlow(unittest.TestCase):
    """Verify that Marchand's extra action integrates with turn management."""

    def test_marchand_grants_extra_action_attribute(self):
        game = make_game()
        player = game.players[0]
        player.extra_actions = 0
        card = make_card('Marchand', 'Rouge', 'Arrive à la cour')
        CardEffects.marchand_effect(game, player, card, (0, 0))
        self.assertEqual(player.extra_actions, 1)

    def test_advance_turn_consumes_extra_action_before_passing(self):
        """With 1 extra_action, advance_turn_if_done should NOT advance the turn
        on the first call but should grant 1 more action."""
        game = make_game()
        player = game.players[0]
        player.extra_actions = 1
        game.current_player = 0
        game.actions_remaining = 0
        turn_before = game.turn

        advanced = game.advance_turn_if_done()

        self.assertFalse(advanced, "Turn should NOT advance while extra_action is pending")
        self.assertEqual(game.actions_remaining, 1, "One extra action should be granted")
        self.assertEqual(player.extra_actions, 0, "extra_actions should be consumed")
        self.assertEqual(game.turn, turn_before, "Turn counter should be unchanged")

    def test_advance_turn_passes_after_extra_action_used(self):
        """After the extra action is consumed, the next advance_turn_if_done should advance."""
        game = make_game()
        player = game.players[0]
        player.extra_actions = 0
        game.current_player = 0
        game.actions_remaining = 0
        turn_before = game.turn

        advanced = game.advance_turn_if_done()

        self.assertTrue(advanced, "Turn should advance when no extra actions remain")
        self.assertEqual(game.turn, turn_before + 1)


# ---------------------------------------------------------------------------
# Tests: protection (cards cannot be removed while protected)
# ---------------------------------------------------------------------------

class TestProtectedCards(unittest.TestCase):
    """Protected cards must be immune to return/remove effects."""

    def test_magicien_skips_protected_card(self):
        game = make_game()
        protected = make_card('Ambassadeur')
        protected.protected = True
        place_in_cour(game, protected, 1, 1)
        apply(game, 'Magicien')
        self.assertIs(game.board.cour[1][1], protected, "Protected card must not be moved by Magicien")

    def test_traitre_skips_protected_card(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        protected = make_card('Pretre')
        protected.protected = True
        place_in_cour(game, protected, 0, 0)
        apply(game, 'Traitre', player=player)
        self.assertIs(game.board.cour[0][0], protected, "Protected card must not be removed by Traitre")

    def test_traitre_removes_unprotected_card(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        unprotected = make_card('Baladin')
        place_in_cour(game, unprotected, 2, 2)
        apply(game, 'Traitre', player=player)
        self.assertIsNone(game.board.cour[2][2], "Unprotected card should be removed by Traitre")

    def test_roi_skips_protected_card(self):
        game = make_game()
        roi = make_card('Roi')
        protected = make_card('Ambassadeur')
        protected.protected = True
        place_in_cour(game, roi, 0, 0)
        place_in_cour(game, protected, 1, 0)        # cour[y=0][x=1]
        CardEffects.roi_effect(game, game.players[0], roi, (0, 0))
        self.assertIs(game.board.cour[0][1], protected, "Roi must not remove a protected card")

    def test_reine_skips_protected_card(self):
        game = make_game()
        reine = make_card('Reine')
        protected = make_card('Pretre')
        protected.protected = True
        place_in_cour(game, reine, 0, 0)
        place_in_cour(game, protected, 1, 0)        # cour[y=0][x=1]
        CardEffects.reine_effect(game, game.players[0], reine, (0, 0))
        self.assertIs(game.board.cour[0][1], protected, "Reine must not remove a protected card")

    def test_assassin_spares_protected_card(self):
        game = make_game()
        assassin = make_card('Assassin')
        protected = make_card('Baladin')
        protected.protected = True
        place_in_cour(game, assassin, 0, 0)
        place_in_cour(game, protected, 1, 0)        # cour[y=0][x=1]
        CardEffects.assassin_effect(game, game.players[0], assassin, (0, 0))
        self.assertIsNotNone(game.board.cour[0][1], "Assassin must spare a protected card")

    def test_courtisan_skips_protected_card(self):
        game = make_game()
        courtisan = make_card('Courtisan')
        protected = make_card('Baladin')
        protected.protected = True
        place_in_cour(game, courtisan, 0, 0)
        place_in_cour(game, protected, 1, 0)        # cour[y=0][x=1]
        CardEffects.courtisan_effect(game, game.players[0], courtisan, (0, 0))
        self.assertIsNotNone(game.board.cour[0][1], "Courtisan must skip a protected card")


# ---------------------------------------------------------------------------
# Tests: Chevalier stacking tooltip data
# ---------------------------------------------------------------------------

class TestChevalierTooltipStack(unittest.TestCase):
    """The tooltip stack logic must traverse the .protects chain."""

    def test_single_card_stack_is_just_itself(self):
        card = make_card('Baladin')
        stack = []
        cur = card
        stack.append(cur)
        while getattr(cur, 'protects', None):
            cur = cur.protects
            stack.append(cur)
        self.assertEqual(len(stack), 1)

    def test_chevalier_protects_chain_length_two(self):
        base = make_card('Roi')
        chevalier = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        chevalier.protects = base
        base.protected = True
        stack = []
        cur = chevalier
        stack.append(cur)
        while getattr(cur, 'protects', None):
            cur = cur.protects
            stack.append(cur)
        self.assertEqual(len(stack), 2)
        self.assertIs(stack[0], chevalier)
        self.assertIs(stack[1], base)

    def test_chevalier_on_chevalier_chain_length_three(self):
        base = make_card('Roi')
        chev1 = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        chev2 = make_card('Chevalier', 'Violet', 'Arrive sur une autre carte')
        chev1.protects = base
        chev2.protects = chev1
        stack = []
        cur = chev2
        stack.append(cur)
        while getattr(cur, 'protects', None):
            cur = cur.protects
            stack.append(cur)
        self.assertEqual(len(stack), 3)


# ---------------------------------------------------------------------------
# Tests: Interactive pending actions (human player gets pending_action,
#        AI player gets immediate resolution, resolve_* helpers work correctly)
# ---------------------------------------------------------------------------

class TestPendingActions(unittest.TestCase):
    """Verify that interactive card effects set pending_action for humans
    and that resolve_* helpers correctly apply the action."""

    # --- Guetteur ---

    def test_guetteur_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        self.assertTrue(player.is_human)
        soldat = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        src = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart'][0]
        place_on_tile(game, soldat, src)
        apply(game, 'Guetteur', player=player, position=(-1, -1))
        self.assertIsNotNone(game.pending_action, "Human player should get pending_action")
        self.assertEqual(game.pending_action['type'], 'guetteur')

    def test_guetteur_valid_sources_contains_soldat_tile(self):
        game = make_game()
        player = game.players[0]
        player.is_human = True
        soldat = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        rempart_tiles = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        src = rempart_tiles[0]
        place_on_tile(game, soldat, src)
        apply(game, 'Guetteur', player=player, position=(-1, -1))
        pa = game.pending_action
        self.assertIn(src, pa['valid_sources'])

    def test_resolve_guetteur_moves_soldat(self):
        game = make_game()
        soldat = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        rempart_tiles = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        src = rempart_tiles[0]
        dst = rempart_tiles[1] if len(rempart_tiles) > 1 else None
        if dst is None:
            return  # Skip if only one rempart
        place_on_tile(game, soldat, src)
        # Simulate pending action at step 2 (source selected)
        game.pending_action = {
            'type': 'guetteur',
            'step': 2,
            'player': game.players[0],
            'valid_sources': [src],
            'source_pos': src,
        }
        result = game.resolve_guetteur(src, dst)
        self.assertTrue(result)
        self.assertIsNone(game.board.tiles[src]['card'])
        self.assertIs(game.board.tiles[dst]['card'], soldat)
        self.assertIsNone(game.pending_action)

    # --- Conseiller du roi ---

    def test_conseiller_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        self.assertTrue(player.is_human)
        ex_card = make_card('Reine')
        game.exchange.append(ex_card)
        CardEffects.conseiller_roi_effect(game, player, make_card('Conseiller_du_roi'), (0, 0))
        self.assertIsNotNone(game.pending_action, "Human player should get pending_action")
        self.assertEqual(game.pending_action['type'], 'conseiller')

    def test_resolve_conseiller_places_card_in_valid_zone(self):
        game = make_game()
        player = game.players[0]
        ex_card = make_card('Reine', 'Rouge', 'Arrive à la cour')
        game.exchange.append(ex_card)
        result = game.resolve_conseiller(0, (1, 1))
        self.assertTrue(result)
        self.assertIs(game.board.cour[1][1], ex_card)
        self.assertIsNone(game.pending_action)

    def test_resolve_conseiller_rejects_wrong_zone(self):
        game = make_game()
        player = game.players[0]
        # Orange card cannot be placed in cour (it goes on tiles)
        ex_card = make_card('Soldat', 'Orange', 'Arrive sur les remparts')
        game.exchange.append(ex_card)
        # Try to place Orange card in cour — invalid zone
        result = game.resolve_conseiller(0, (0, 0))
        self.assertFalse(result)

    # --- Prince charmant ---

    def test_prince_charmant_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        self.assertTrue(player.is_human)
        reine = make_card('Reine')
        place_in_cour(game, reine, 2, 0)
        CardEffects.prince_charmant_effect(game, player, make_card('Prince_charmant'), (0, 0))
        self.assertIsNotNone(game.pending_action, "Human player should get pending_action")
        self.assertEqual(game.pending_action['type'], 'prince_charmant')

    def test_prince_charmant_valid_sources_has_female_card(self):
        game = make_game()
        player = game.players[0]
        player.is_human = True
        reine = make_card('Reine')
        place_in_cour(game, reine, 2, 0)
        CardEffects.prince_charmant_effect(game, player, make_card('Prince_charmant'), (0, 0))
        pa = game.pending_action
        self.assertIn((2, 0), pa['valid_sources'])

    def test_resolve_prince_charmant_moves_female_card(self):
        game = make_game()
        reine = make_card('Reine')
        place_in_cour(game, reine, 2, 0)
        # Simulate pending action at step 2 (source selected)
        game.pending_action = {
            'type': 'prince_charmant',
            'step': 2,
            'player': game.players[0],
            'valid_sources': [(2, 0)],
            'source_pos': (2, 0),
        }
        result = game.resolve_prince_charmant((2, 0), (3, 3))
        self.assertTrue(result)
        self.assertIsNone(game.board.cour[0][2])
        self.assertIs(game.board.cour[3][3], reine)
        self.assertIsNone(game.pending_action)

    def test_resolve_prince_charmant_rejects_occupied_destination(self):
        game = make_game()
        reine = make_card('Reine')
        blocker = make_card('Roi')
        place_in_cour(game, reine, 2, 0)
        place_in_cour(game, blocker, 3, 3)
        game.pending_action = {
            'type': 'prince_charmant',
            'step': 2,
            'player': game.players[0],
            'valid_sources': [(2, 0)],
            'source_pos': (2, 0),
        }
        result = game.resolve_prince_charmant((2, 0), (3, 3))
        self.assertFalse(result)
        self.assertIs(game.board.cour[0][2], reine)


# ---------------------------------------------------------------------------
# Tests: Return-to-owner rule & 4th siege engine captain handling
# ---------------------------------------------------------------------------

class TestReturnToOwner(unittest.TestCase):
    """Cards returned from the board go to pion_owner's hand; no owner → exchange."""

    def test_return_card_to_owner_hand(self):
        from engine.effects import CardEffects
        game = make_game()
        player = game.players[0]
        card = make_card('Roi')
        card.pion_owner = player
        before = len(player.hand)
        CardEffects._return_card(game, card)
        self.assertEqual(len(player.hand), before + 1)
        self.assertIn(card, player.hand)
        self.assertEqual(len(game.exchange), 0)

    def test_return_card_no_owner_goes_to_exchange(self):
        from engine.effects import CardEffects
        game = make_game()
        card = make_card('Roi')
        # no pion_owner
        CardEffects._return_card(game, card)
        self.assertIn(card, game.exchange)

    def test_return_card_stolen_always_exchange(self):
        from engine.effects import CardEffects
        game = make_game()
        player = game.players[0]
        card = make_card('Baladin')
        card.pion_owner = player
        card.stolen = True
        CardEffects._return_card(game, card)
        self.assertNotIn(card, player.hand)
        self.assertIn(card, game.exchange)
        self.assertFalse(card.stolen)

    def test_traitre_returns_card_to_owner(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        victim = make_card('Baladin')
        victim.pion_owner = player
        place_in_cour(game, victim, 1, 1)
        apply(game, 'Traitre', player=player)
        self.assertIsNone(game.board.cour[1][1])
        self.assertIn(victim, player.hand)

    def test_roi_returns_card_to_owner(self):
        game = make_game()
        p0, p1 = game.players[0], game.players[1]
        p0.is_human = False
        roi = make_card('Roi')
        victim = make_card('Baladin')
        victim.pion_owner = p1
        place_in_cour(game, roi, 0, 0)
        place_in_cour(game, victim, 2, 2)
        CardEffects.roi_effect(game, p0, roi, (0, 0))
        self.assertIsNone(game.board.cour[2][2])
        self.assertIn(victim, p1.hand)

    def test_magicien_returns_no_owner_to_exchange(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        card = make_card('Courtisan')
        # pion_owner is None
        place_in_cour(game, card, 1, 1)
        apply(game, 'Magicien', player=player)
        self.assertIsNone(game.board.cour[1][1])
        self.assertIn(card, game.exchange)

    def test_archer_returns_ext_card_to_owner(self):
        game = make_game()
        player = game.players[0]
        player.is_human = False
        barbare = make_card('Barbare', 'Vert')
        barbare.pion_owner = player
        place_in_ext(game, barbare, (8, 0), owner=player)
        apply(game, 'Archer', player=player)
        self.assertIn(barbare, player.hand)


class TestFourthEngineCapitaine(unittest.TestCase):
    """4th siege engine: capitaine returned, protected soldiers stay."""

    def _setup_four_engines(self, game):
        for i, slot in enumerate([(-2, 0), (5, 0), (0, -2), (0, 5)]):
            e = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
            game.board.exterieur[slot] = e

    def test_fourth_engine_returns_unprotected_soldier(self):
        game = make_game()
        player = game.players[0]
        remparts = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        soldat = make_card('Soldat', 'Orange')
        soldat.pion_owner = player
        place_on_tile(game, soldat, remparts[0])
        self._setup_four_engines(game)
        engine = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        CardEffects.engin_siege_effect(game, player, engine, (-2, 0))
        self.assertIsNone(game.board.tiles[remparts[0]]['card'])
        self.assertIn(soldat, player.hand)

    def test_fourth_engine_returns_capitaine_even_when_soldiers_protected(self):
        game = make_game()
        player = game.players[0]
        remparts = [p for p, t in game.board.tiles.items() if t['type'] == 'rempart']
        cap = make_card('Capitaine', 'Orange')
        cap.pion_owner = player
        soldat = make_card('Soldat', 'Orange')
        soldat.pion_owner = player
        place_on_tile(game, cap, remparts[0])
        place_on_tile(game, soldat, remparts[1])
        # Capitaine protects the soldat
        soldat.protected = True
        self._setup_four_engines(game)
        engine = make_card('Engin_de_siege', 'Vert', 'Arrive hors les murs')
        CardEffects.engin_siege_effect(game, player, engine, (-2, 0))
        # Captain must be returned
        self.assertIsNone(game.board.tiles[remparts[0]]['card'])
        self.assertIn(cap, player.hand)
        # Protected soldier stays
        self.assertIs(game.board.tiles[remparts[1]]['card'], soldat)
        # But loses its protection flag
        self.assertFalse(getattr(soldat, 'protected', False))


# ---------------------------------------------------------------------------
# Tests: pick_return interactive pending action
# ---------------------------------------------------------------------------

class TestPickReturn(unittest.TestCase):
    """Human player gets pending_action type='pick_return'; resolve_pick_return works."""

    def test_magicien_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        self.assertTrue(player.is_human)
        card = make_card('Courtisan')
        place_in_cour(game, card, 1, 1)
        apply(game, 'Magicien', player=player)
        self.assertIsNotNone(game.pending_action)
        self.assertEqual(game.pending_action['type'], 'pick_return')
        self.assertEqual(game.pending_action['zone'], 'cour')

    def test_roi_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        roi = make_card('Roi')
        victim = make_card('Baladin')
        place_in_cour(game, roi, 0, 0)
        place_in_cour(game, victim, 2, 2)
        CardEffects.roi_effect(game, player, roi, (0, 0))
        self.assertIsNotNone(game.pending_action)
        self.assertEqual(game.pending_action['type'], 'pick_return')
        self.assertIn((2, 2), game.pending_action['valid'])

    def test_resolve_pick_return_cour(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Baladin')
        victim.pion_owner = player
        place_in_cour(game, victim, 2, 2)
        game.pending_action = {
            'type': 'pick_return',
            'effect': 'Roi',
            'zone': 'cour',
            'valid': [(2, 2)],
            'player': player,
            'next': None,
        }
        result = game.resolve_pick_return((2, 2))
        self.assertTrue(result)
        self.assertIsNone(game.board.cour[2][2])
        self.assertIn(victim, player.hand)
        self.assertIsNone(game.pending_action)

    def test_resolve_pick_return_invalid_position(self):
        game = make_game()
        player = game.players[0]
        victim = make_card('Baladin')
        place_in_cour(game, victim, 2, 2)
        game.pending_action = {
            'type': 'pick_return',
            'effect': 'Roi',
            'zone': 'cour',
            'valid': [(1, 1)],  # (2,2) not in valid
            'player': player,
            'next': None,
        }
        result = game.resolve_pick_return((2, 2))
        self.assertFalse(result)
        self.assertIsNotNone(game.pending_action)  # still pending

    def test_archer_sets_pending_for_human(self):
        game = make_game()
        player = game.players[0]
        barbare = make_card('Barbare', 'Vert')
        place_in_ext(game, barbare, (8, 0))
        apply(game, 'Archer', player=player)
        self.assertIsNotNone(game.pending_action)
        self.assertEqual(game.pending_action['zone'], 'ext')
        self.assertIn((8, 0), game.pending_action['valid'])

    def test_resolve_pick_return_ext(self):
        game = make_game()
        player = game.players[0]
        barbare = make_card('Barbare', 'Vert')
        barbare.pion_owner = player
        place_in_ext(game, barbare, (8, 0))
        game.pending_action = {
            'type': 'pick_return',
            'effect': 'Archer',
            'zone': 'ext',
            'valid': [(8, 0)],
            'player': player,
            'next': None,
        }
        result = game.resolve_pick_return((8, 0))
        self.assertTrue(result)
        self.assertNotIn((8, 0), game.board.exterieur)
        self.assertIn(barbare, player.hand)

    def test_dragon_chains_ext_then_tile(self):
        game = make_game()
        player = game.players[0]
        barbare = make_card('Barbare', 'Vert')
        soldat = make_card('Soldat', 'Orange')
        place_in_ext(game, barbare, (8, 0))
        tour_pos = [p for p, t in game.board.tiles.items() if t['type'] == 'tour'][0]
        place_on_tile(game, soldat, tour_pos)
        apply(game, 'Dragon', player=player, position=(8, 0))
        # Step 1: ext selection
        pa = game.pending_action
        self.assertIsNotNone(pa)
        self.assertEqual(pa['zone'], 'ext')
        self.assertIsNotNone(pa.get('next'))
        # Resolve step 1
        game.resolve_pick_return((8, 0))
        # Now pending_action should be for tile
        pa2 = game.pending_action
        self.assertIsNotNone(pa2)
        self.assertEqual(pa2['zone'], 'tile')
        # Resolve step 2
        game.resolve_pick_return(tour_pos)
        self.assertIsNone(game.pending_action)
        self.assertNotIn((8, 0), game.board.exterieur)
        self.assertIsNone(game.board.tiles[tour_pos]['card'])


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("CASTEL - Tests unitaires des effets de cartes")
    print("=" * 60)
    unittest.main(verbosity=2)
