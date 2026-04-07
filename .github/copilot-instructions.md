# GitHub Copilot Instructions — Castel

## Règles générales

- **Ne jamais générer de fichiers Markdown** pour documenter des changements, corrections, ou itérations. Toute documentation est maintenue dans les fichiers existants (README.md, DOCUMENTATION.md, CHANGELOG.md).
- Ne pas créer de fichiers de notes temporaires, de plans, ou de résumés d'implémentation en Markdown.
- Mettre à jour CHANGELOG.md si un changement majeur est introduit.

## Architecture

Ce projet suit une architecture en couches :

```
engine/   → logique de jeu pure (sans dépendance UI)
ui/       → rendu graphique (Pygame uniquement)
tools/    → utilitaires (chargement de scénarios)
assets/   → ressources graphiques (images PNG par couleur de bannière)
scenarios/→ configurations JSON
```

**Moteur graphique : Pygame** (unique, `ui/renderer.py`). Ne pas utiliser ni ajouter arcade.

## Principes SOLID

- **S** — Chaque classe a une seule responsabilité : `Card` (données), `Board` (plateau), `GameState` (état), `CastelWindow` (rendu).
- **O** — Étendre par héritage/composition plutôt que modifier les classes existantes.
- **L** — Les sous-classes (`AIPlayer` extends `Player`) doivent rester substituables.
- **I** — Préférer de petites interfaces/méthodes ciblées à de grosses méthodes multi-rôles.
- **D** — `GameState` ne dépend pas de l'UI ; l'UI dépend de `GameState` (injection de dépendance).

## Ressources graphiques

Les images sont dans `images/` classées par couleur de bannière :
- `images/rouge/` — cartes de la cour (zone rouge)
- `images/vert/` — cartes hors les murs (zone verte)
- `images/orange/` — remparts (zone orange)
- `images/bleu/` — tours (zone bleue)
- `images/violet/` — chevaliers (bannière violette)
- `images/Rempart.png`, `images/Tour.png` — tuiles du plateau

Toujours utiliser ces assets pour l'affichage des cartes et du plateau.

## Tests

- Exécuter `python test_suite.py` après chaque modification significative du moteur de jeu.
- Ajouter des tests dans `test_suite.py` pour chaque nouvelle fonctionnalité de l'engine.
- `test_rules.py` est réservé aux tests de règles de jeu (effets de cartes).
- Ne pas tester le rendu UI (trop couplé à Pygame).

## Style de code

- Python 3.11+, PEP 8.
- Docstrings sur les classes et méthodes publiques.
- Pas de commentaires superflus ; le code doit être auto-documenté.
- Préférer les dataclasses ou classes simples aux dictionnaires pour les structures de données.
- Fichier de données : `Inventaire.csv` (ne pas modifier la structure CSV).
