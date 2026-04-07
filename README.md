# Castel

Implmentation Pygame du jeu de plateau **Castel** (Serge Laget & Bruno  2 Faidutti 5 joueurs.) 

## Lancement

```bash
pip install -r requirements.txt
python main.py
```

## Structure

```
 Logique de jeu (GameState, Board, Card, Player, AI, Effects)
 Rendu Pygame (renderer.py)
 Utilitaires (chargement de scnarios)
 Ressources graphiques
 Images PNG des cartes et tuiles
 Configurations JSON
 Donnes des 37 types de cartes
```

## Contrôles

| Action | Contrôle |
|--------|----------|
| Sélectionner une carte | Clic gauche sur la carte en main |
| Placer une carte | Clic gauche sur la case du plateau |
| Piocher | Clic sur le bouton Piocher |
| changer | Clic sur une carte de l'échange |
| Quitter | ESC |

## Tests

```bash
python test_suite.py
```

## Documentation

- [`DOCUMENTATION.md`](DOCUMENTATION. Architecture technique) 
- [`GETTING_STARTED.md`](GETTING_STARTED. Guide d'installation) 
- [`rules.md`](rules. RMdgles officielles du jeu) 
- [`CHANGELOG.md`](CHANGELOG. Historique des versions) 
