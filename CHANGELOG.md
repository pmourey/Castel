# Changelog - Castel Game

## [1.0.0] - 2026-04-04

### ✨ Fonctionnalités Implémentées

#### Core Gameplay
- ✓ Support 2-5 joueurs (1 humain + 1-4 ordinateurs)
- ✓ Génération automatique du château avec tours et remparts
- ✓ Plateau de jeu: cour carrée 4x4 + zones extérieures illimitées
- ✓ Distribution de 5 cartes par joueur au démarrage
- ✓ Tours alternés humain/IA

#### Cartes et Ressources
- ✓ Chargement de 37 types de cartes depuis Inventaire.csv
- ✓ 56 cartes totales dans le jeu
- ✓ Cartes par couleur: Bleu (6), Orange (15), Rouge (22), Vert (7), Violet (4)
- ✓ Chaque carte a nom, nombre, lieu, condition et action

#### Interface Utilisateur
- ✓ Interface Pygame avec résolution 1400x900
- ✓ Affichage de la cour 4x4 avec grille
- ✓ Affichage de la main du joueur avec 5 cartes
- ✓ Système de sélection des cartes (clic)
- ✓ Placement des cartes par clic sur la cour
- ✓ Surlignage visuel des cartes sélectionnées
- ✓ Affichage du joueur actuel et du tour
- ✓ Aide à l'écran avec contrôles

#### Systèmes de Jeu
- ✓ Système de plateau avec grid 4x4
- ✓ Gestion des cartes et deck
- ✓ Distribution des mains
- ✓ Placement des cartes
- ✓ Alternance des joueurs

#### IA
- ✓ Classe AIPlayer héritée de Player
- ✓ Sélection aléatoire de carte
- ✓ Placement intelligent (cour vs extérieur)
- ✓ Délai visuel de 1 seconde pour lisibilité

#### Structure de Projet
- ✓ Dossiers modulaires (engine/, ui/, tools/, assets/, scenarios/)
- ✓ Séparation concerns (Board, Card, Game, Player, AI, Renderer)
- ✓ Configuration par scénario JSON
- ✓ Gestionnaire de scénario

#### Documentation et Tests
- ✓ README.md complet
- ✓ DOCUMENTATION.md détaillée
- ✓ Suite de tests (test_suite.py) - 7/7 tests passants
- ✓ Fichier de configuration pyproject.json
- ✓ Requirements.txt avec dépendances

### 🔄 À Implémenter - Prochaines Phases

#### Phase 2: Effets de Cartes
- [ ] Implémentation des 37 effets spécifiques
- [ ] Système de ciblage pour les effets
- [ ] Résolution des interactions entre cartes
- [ ] Effets qui s'appliquent une seule fois (flag 'used')
- [ ] Chaînes d'effets et résolutions
- [ ] Système de pions joueurs

#### Phase 3: Règles de Jeu Complètes
- [ ] Conditions de placement par zone
- [ ] Règles de remparts et tours
- [ ] Protection des personnages
- [ ] Conditions de victoire/défaite
- [ ] Système de score
- [ ] Gestion des cas spéciaux (Roi/Reine, etc.)

#### Phase 4: Amélioration IA
- [ ] Évaluation du plateau
- [ ] Stratégie défensive/offensive
- [ ] Analyse des coups possibles
- [ ] Prédiction des actions adverses
- [ ] Niveaux de difficulté
- [ ] Fichiers de configuration pour stratégies

#### Phase 5: Interface Avancée
- [ ] Affichage des tuiles du château
- [ ] Animation des placements
- [ ] Effets visuels
- [ ] Son et musique
- [ ] Menu de démarrage
- [ ] Écran de fin de partie
- [ ] Historique des actions

#### Phase 6: Fonctionnalités Avancées
- [ ] Sauvegarde/Chargement de parties
- [ ] Mode rejeu/replay
- [ ] Éditeur de scénario
- [ ] Intégration PDF des règles
- [ ] Mode coaching/tutoriel
- [ ] Statistiques de joueur

### 📝 Architecture

```
Castel/
├── engine/
│   ├── board.py         (212 lignes) - Plateau et placement
│   ├── card.py          (29 lignes)  - Cartes et CSV
│   ├── game.py          (72 lignes)  - Logique de jeu
│   ├── player.py        (7 lignes)   - Classe Player
│   ├── ai.py            (19 lignes)  - Logique IA
│   ├── effects.py       (241 lignes) - Effets de cartes (stubs)
│   └── __init__.py
├── ui/
│   ├── renderer.py      (155 lignes) - Interface Pygame
│   └── __init__.py
├── tools/
│   ├── scenario_manager.py (44 lignes) - Gestion scénarios
│   └── __init__.py
├── assets/
│   └── __init__.py
├── scenarios/
│   └── standard.json
├── images/              - Images des cartes
├── main.py             (18 lignes)  - Point d'entrée
├── test_suite.py       (150+ lignes) - Suite de tests
├── requirements.txt
├── DOCUMENTATION.md    - Documentation détaillée
├── CHANGELOG.md        - Ce fichier
└── pyproject.json
```

### 📊 Statistiques

- **Lignes de code**: ~1000
- **Modules**: 8 (game, board, card, player, ai, effects, renderer, scenario_manager)
- **Cartes**: 37 types, 56 totales
- **Tests**: 7/7 passants
- **Taille du plateau**: 4x4 (16 cases) + extérieur illimité

### 🐛 Bugs Connus et Limitations

1. Affichage des accents dans le terminal (problème d'encodage)
2. Images des cartes non toutes disponibles (chargement gracieux avec fallback)
3. IA ne considère pas les effets des cartes
4. Pas de validation des conditions de placement
5. Pas de système de pions pour les joueurs

### 🎯 Objectifs de Performance

- FPS: 60 constant
- Temps de chargement: <2 secondes
- Mémoire: <100 MB
- Lag IA: <500ms par action

### 📦 Dépendances

- pygame==2.6.1
- Python 3.11+

### 🙏 Ressources Utilisées

- Règles: http://jeuxstrategie.free.fr/Castel_complet.php
- Images: Fichiers PNG fournis
- Inventaire: Fichier CSV détaillé

---

Version initiale développée le 4 avril 2026.
Structure et architecture inspirées du projet Conan Overlord.
