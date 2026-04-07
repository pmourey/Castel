#!/usr/bin/env python3
"""
Test Suite for Castel Game
"""
import sys
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from engine.game import GameState
        from engine.board import Board
        from engine.card import Card, CARDS
        from engine.player import Player
        from engine.ai import AIPlayer
        from engine.effects import CardEffects
        from ui.renderer import CastelWindow
        from tools.scenario_manager import ScenarioManager
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_game_creation():
    """Test game initialization."""
    print("\nTesting game creation...")
    try:
        from engine.game import GameState
        game = GameState(num_players=3)
        assert len(game.players) == 3, "Expected 3 players"
        assert game.players[0].is_human, "First player should be human"
        assert not game.players[1].is_human, "Second player should be AI"
        assert len(game.board.tiles) > 0, "Castle should have tiles"
        print(f"✓ Game created with {len(game.players)} players")
        print(f"✓ Castle has {len(game.board.tiles)} tiles")
        return True
    except Exception as e:
        print(f"✗ Game creation failed: {e}")
        return False

def test_card_loading():
    """Test card loading from CSV."""
    print("\nTesting card loading...")
    try:
        from engine.card import CARDS
        assert len(CARDS) > 0, "No cards loaded"
        assert len(set(c.nom for c in CARDS)) == 37, "Expected 37 card types"
        total = sum(c.nombre for c in CARDS)
        assert total == 56, f"Expected 56 total cards, got {total}"
        print(f"✓ Loaded {len(set(c.nom for c in CARDS))} card types")
        print(f"✓ Total cards: {total}")
        return True
    except Exception as e:
        print(f"✗ Card loading failed: {e}")
        return False

def test_hand_distribution():
    """Test that hands are distributed correctly."""
    print("\nTesting hand distribution...")
    try:
        from engine.game import GameState
        game = GameState(num_players=4)
        for i, player in enumerate(game.players):
            assert len(player.hand) == 5, f"Player {i} should have 5 cards"
        total_in_hands = sum(len(p.hand) for p in game.players)
        assert total_in_hands == 20, f"Total in hands should be 20, got {total_in_hands}"
        print(f"✓ Each player has 5 cards")
        print(f"✓ Total distributed: {total_in_hands} cards")
        return True
    except Exception as e:
        print(f"✗ Hand distribution failed: {e}")
        return False

def test_ai_action():
    """Test that AI can choose an action."""
    print("\nTesting AI action choice...")
    try:
        from engine.game import GameState
        game = GameState(num_players=2)
        ai_player = game.players[1]
        action = ai_player.choose_action(game)
        assert action[0] in ('place', 'draw', 'exchange', 'skip'), f"Unknown action type: {action[0]}"
        if action[0] == 'place':
            _, card, position = action
            assert card is not None, "AI should choose a card"
            assert position is not None, "AI should choose a position"
            assert card in ai_player.hand, "Chosen card should be in AI hand"
            print(f"✓ AI chose card: {card.nom}")
            print(f"✓ AI chose position: {position}")
        else:
            print(f"✓ AI chose action: {action[0]}")
        return True
    except Exception as e:
        print(f"✗ AI action failed: {e}")
        return False

def test_card_placement():
    """Test placing a card on the board."""
    print("\nTesting card placement...")
    try:
        from engine.game import GameState
        game = GameState(num_players=2)
        player = game.players[0]
        # Find a rouge card (cour) to place
        rouge_card = next((c for c in player.hand if 'cour' in c.lieu.lower()), None)
        if rouge_card is None:
            rouge_card = player.hand[0]
        position = (1, 1)
        result = game.place_card(player, rouge_card, position)
        assert result in ('ok', 'win'), f"Expected 'ok' or 'win', got {result!r}"
        assert rouge_card not in player.hand, "Card should be removed from hand"
        print(f"✓ Placed {rouge_card.nom} at {position}")
        return True
    except Exception as e:
        print(f"✗ Card placement failed: {e}")
        return False

def test_scenario_loading():
    """Test loading scenarios."""
    print("\nTesting scenario loading...")
    try:
        from tools.scenario_manager import ScenarioManager
        scenario = ScenarioManager.load_scenario("standard")
        assert scenario is not None, "Scenario not loaded"
        assert "towers" in scenario, "Scenario should have towers"
        assert "walls" in scenario, "Scenario should have walls"
        print(f"✓ Loaded scenario: {scenario['name']}")
        print(f"✓ Towers: {len(scenario['towers'])}, Walls: {len(scenario['walls'])}")
        return True
    except Exception as e:
        print(f"✗ Scenario loading failed: {e}")
        return False

def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("CASTEL GAME TEST SUITE")
    print("=" * 60)

    tests = [
        test_imports,
        test_game_creation,
        test_card_loading,
        test_hand_distribution,
        test_ai_action,
        test_card_placement,
        test_scenario_loading,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("=" * 60)

    return all(results)

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

