import csv
from pathlib import Path

class Card:
    def __init__(self, couleur, nom, nombre, lieu, condition, action):
        self.couleur = couleur
        self.nom = nom
        self.nombre = nombre
        self.lieu = lieu
        self.condition = condition
        self.action = action
        self.used = False  # Pour effets qui s'appliquent une fois

    @staticmethod
    def load_from_csv(csv_path):
        cards = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=';')
            next(reader)  # Skip header
            for row in reader:
                if len(row) == 6:
                    couleur, nom, nombre, lieu, condition, action = row
                    nombre = int(nombre) if nombre.isdigit() else 1
                    # Create 'nombre' instances of each card
                    for _ in range(nombre):
                        cards.append(Card(couleur, nom, 1, lieu, condition, action))
        return cards

# Charger les cartes
CARDS = Card.load_from_csv(Path(__file__).parent.parent / "Inventaire.csv")
