# Castel - Jeu de Plateau Pygame

Une application Pygame jouable du jeu Castel (Humain vs Ordinateur) avec support jusqu'à 5 joueurs.

## 🎮 Caractéristiques

### Implémentées ✓
- **Joueurs**: 1 Humain + jusqu'à 4 Ordinateurs
- **Plateau**: Cour 4x4 + zones extérieures illimitées
- **Château**: Tours et Remparts avec rotations
- **Cartes**: 37 types de cartes avec 56 cartes totales
- **Distribution**: 5 cartes par joueur au démarrage
- **Interface**: Interface Pygame avec affichage des cartes
- **Sélection**: Clic pour sélectionner/placer les cartes
- **IA**: Joueurs ordinateurs avec tours automatiques
- **Scénarios**: Configuration JSON pour différentes variantes

### À Implémenter 🔄
- Tous les 37 effets de cartes spécifiques
- Conditions de placement (remparts, tours, etc.)
- Règles de victoire/défaite
- Affichage des tuiles du château
- Affichage des cartes dans les zones extérieures
- Amélioration de l'IA (stratégie vs aléatoire)
- Système de pions pour les joueurs
- Animations et transitions
- Intégration des PDFs de règles
- Sauvegarde/Chargement de parties

## 📁 Structure du Projet

```
Castel/
├── engine/                 # Moteur de jeu
│   ├── board.py           # Gestion du plateau
│   ├── card.py            # Gestion des cartes (chargement CSV)
│   ├── game.py            # État et logique du jeu
│   ├── player.py          # Classe Player
│   ├── ai.py              # IA des joueurs ordinateurs
│   ├── effects.py         # Interpréteur des effets de cartes
│   └── __init__.py
├── ui/                    # Interface utilisateur
│   ├── renderer.py        # Rendu Pygame
│   └── __init__.py
├── tools/                 # Utilitaires
│   ├── scenario_manager.py # Gestion des scénarios
│   └── __init__.py
├── assets/                # Ressources
│   └── __init__.py
├── scenarios/             # Configurations de partie
│   └── standard.json
├── images/                # Images des cartes et tuiles
│   ├── Tour.png
│   ├── Rempart.png
│   ├── bleu/
│   ├── orange/
│   ├── rouge/
│   ├── vert/
│   └── violet/
├── Inventaire.csv         # Catalogue des cartes
├── Règles.pdf            # Règles du jeu
├── main.py               # Point d'entrée
├── requirements.txt      # Dépendances
└── README.md            # Cette documentation
```

## 🚀 Installation et Lancement

### Prérequis
- Python 3.11+
- Pygame 2.6.1

### Installation
```bash
pip install -r requirements.txt
```

### Lancement
```bash
python3 main.py
```

L'application demandera le nombre de joueurs (2-5), puis lancera la partie.

## 🎯 Contrôles

| Action | Contrôle |
|--------|----------|
| Sélectionner une carte | Clic gauche sur la carte en main |
| Placer une carte | Clic gauche sur une case de la cour |
| Désélectionner | Clic gauche sur la carte sélectionnée |
| Quitter | Touche ESC |

## 📊 Architecture du Jeu

### GameState (engine/game.py)
- Gère l'état global du jeu
- Alterne entre les joueurs
- Distribution des cartes
- Génération du château
- Gestion des tours

### Board (engine/board.py)
- Représente le plateau 4x4 (cour) + extérieur
- Stocke les cartes placées
- Charge et dessine les images
- Gère les rotations des tuiles

### Card (engine/card.py)
- Charge les cartes depuis Inventaire.csv
- 37 types de cartes, 56 cartes totales
- Attributs: couleur, nom, nombre, lieu, condition, action

### AIPlayer (engine/ai.py)
- Hérité de Player
- Choisit une action aléatoire par défaut
- Place les cartes en fonction du lieu (cour/extérieur)

### CastelWindow (ui/renderer.py)
- Rendu Pygame
- Affichage du plateau et des cartes
- Gestion des entrées souris
- Boucle de jeu

## 📋 Cartes du Jeu

### Bleu (Personnages de tour)
- Fantôme (1)
- Guetteur (1)
- Magicien (1)
- Archer (1)
- Sorcière (1)
- Alchimiste (1)

### Orange (Soldats sur remparts)
- Capitaine (1)
- Traître (1)
- Soldat (13)

### Rouge (Personnages de cour)
- Marchand, Roi, Reine, Princesse, Prince
- Baladin, Courtisane, Intrigant, Espion
- Ambassadeur, Voleur, Bouffon, Fou
- Prêtre, Dame de compagnie, Courtisan
- Assassin, Conseiller du roi, Favorite
- Prince charmant, Chevalier noir

### Vert (Personnages extérieurs)
- Barbare (1)
- Fée (1)
- Enchanteur (1)
- Engin de siège (5)
- Dragon (1)
- Hérault (1)

### Violet (Chevaliers)
- Chevalier (4)

## 🔧 Configuration des Scénarios

Les scénarios sont définis en JSON dans `scenarios/`. Chaque scénario contient:
- Nombre initial de cartes par joueur
- Taille de la cour
- Position et rotation des tours/remparts
- Nombre min/max de joueurs

Exemple: `scenarios/standard.json`

## 🎨 Interface Utilisateur

- **Titre**: Affiche le tour actuel
- **Statut**: Indique le joueur actuel (HUMAIN/IA)
- **Plateau**: Grille 4x4 avec les cartes placées
- **Main**: Les 5 cartes du joueur avec surlignage de sélection
- **Contrôles**: Aide à l'écran

## 🤖 Système d'IA

L'IA actuelle:
- Sélectionne une carte aléatoire de sa main
- Place la carte dans la cour ou extérieur selon le lieu
- Joue avec un délai de 1 seconde pour lisibilité

Améliorations futures:
- Évaluation du plateau
- Stratégie défensive/offensive
- Blocage des cartes adverses
- Combinaisons de cartes

## 📝 Implémentation des Effets

Les effets de cartes sont définis dans `engine/effects.py` avec des placeholders:
- Chaque classe de personnage a sa méthode d'effet
- Les effets sont appelés lors du placement
- Les effets uniques sont marqués avec un flag `used`

Pour implémenter un effet:
1. Localiser la méthode dans `effects.py`
2. Implémenter la logique basée sur `Inventaire.csv`
3. Modifier le jeu/plateau selon l'effet

## 🏆 Règles de Victoire

À implémenter:
- Contrôle de la cour (majorité des pions)
- Élimination des adversaires
- Conditions spéciales (Roi/Reine)

## 🐛 Débogage

```bash
# Afficher l'état du jeu
python3 -c "from engine.game import GameState; game = GameState(3); print(game)"

# Tester le chargement des cartes
python3 -c "from engine.card import CARDS; print(len(CARDS))"

# Vérifier l'IA
python3 -c "from engine.ai import AIPlayer; ai = AIPlayer(); print(ai.hand)"
```

## 📚 Ressources

- **Règles**: [http://jeuxstrategie.free.fr/Castel_complet.php](http://jeuxstrategie.free.fr/Castel_complet.php)
- **Inventaire**: `Inventaire.csv`
- **PDF Complet**: `Règles.pdf`

## 🤝 Contributeurs

Développé en tant qu'adaptation Pygame du jeu Castel original.

## 📄 License

Utilisation libre pour fins éducatives et de divertissement.

---

**Bon jeu! 🎲**
