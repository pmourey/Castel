import json
from pathlib import Path

class ScenarioManager:
    @staticmethod
    def load_scenario(scenario_name="standard"):
        """Load a scenario configuration from JSON file."""
        scenario_path = Path(__file__).parent.parent / "scenarios" / f"{scenario_name}.json"
        if not scenario_path.exists():
            print(f"Scenario {scenario_name} not found, using defaults")
            return ScenarioManager.get_default_scenario()
        
        with open(scenario_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def get_default_scenario():
        """Get default scenario configuration."""
        return {
            "name": "Standard",
            "description": "Default Castel game",
            "initial_hands": 5,
            "castle_size": 4,
            "exterior_unlimited": True,
            "max_players": 5,
            "min_players": 2,
            "towers": [
                {"x": 0, "y": 0, "rotation": 0},
                {"x": 3, "y": 0, "rotation": 90},
                {"x": 0, "y": 3, "rotation": 270},
                {"x": 3, "y": 3, "rotation": 180}
            ],
            "walls": [
                {"x": 1, "y": 0, "rotation": 0},
                {"x": 2, "y": 0, "rotation": 0},
                {"x": 0, "y": 1, "rotation": 90},
                {"x": 0, "y": 2, "rotation": 90},
                {"x": 1, "y": 3, "rotation": 0},
                {"x": 2, "y": 3, "rotation": 0},
                {"x": 3, "y": 1, "rotation": 90},
                {"x": 3, "y": 2, "rotation": 90}
            ]
        }
