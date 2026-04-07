# 🎮 Guide de Démarrage - Castel avec Règles Officielles

## Installation et Démarrage

### Prérequis
- Python 3.8+
- pygame

### Installation
```bash
# Installer les dépendances
pip3 install pygame

# Aller au répertoire du jeu
cd /Users/display/PycharmProjects/Castel
```

### Lancer le jeu
```bash
python3 main.py
```

---

## Règles Implémentées

### 1. Distribution des Cartes
Le jeu suit la distribution officielle selon le nombre de joueurs :
- **2 joueurs**: 9 cartes en main, 13 en pioche, 10 à l'échange
- **3 joueurs**: 7 cartes en main, 8 en pioche, 11 à l'échange
- **4 joueurs**: 5 cartes en main, 6 en pioche, 12 à l'échange
- **5 joueurs**: 5 cartes en main, 4 en pioche, 11 à l'échange

### 2. Système des 3 Actions
Chaque joueur effectue **exactement 2 actions** par tour :

1. **Prendre une carte** de sa pioche
2. **Échanger** une carte (main ↔ échange)
3. **Placer** une carte sur le plateau

Vous pouvez faire 2 fois la même action.

### 3. Zones de Placement
Les cartes ont des zones de placement désignées (bannière de couleur) :
- 🔴 **Cour** (intérieur 4×4)
- 🟠 **Remparts** (murs)
- 🔵 **Tours** (coins)
- 🟢 **Extérieur** (hors les murs)
- 🟣 **Chevaliers** (sur autre carte)

### 4. Victoire
Vous gagnez quand vous avez :
- **0 cartes en main** ET
- **0 cartes en pioche**

(Après application de l'effet de votre dernière carte)

### 5. Effets des Cartes
Les effets s'appliquent une seule fois au placement :
- Certaines cartes renvoient d'autres cartes
- Certaines cartes protègent leurs voisines
- Les soldats et engins ont des règles spéciales

---

## Contrôles du Jeu

### Joueur Humain (Vous)
- **Glisser-déposer**: Prenez une carte de votre main et glissez-la pour la placer
- **ESC**: Quitter le jeu
- **Hover**: Passez la souris sur une carte pour voir ses infos

### Interface
- **Main**: Visible en bas du plateau
- **Pioche**: Affichée à gauche (nombre de cartes)
- **Échange**: Affiché en haut (cartes visibles)
- **Journal**: À droite (historique des actions)
- **Château**: Au centre (cour, remparts, tours)

---

## Mécanique de Jeu

### Votre Tour
1. Vous avez 2 actions à faire
2. Choisissez parmi :
   - Tirer une carte de votre pioche
   - Échanger une carte de votre main contre une de l'échange
   - Placer une carte
3. Après 2 actions, c'est au joueur suivant

### Placement d'une Carte
1. Glissez une carte de votre main
2. Déposez-la sur une case valide
3. Un pion de votre couleur est placé
4. L'effet de la carte s'applique
5. Vérification si vous avez gagné

### Fin du Jeu
Le premier joueur à avoir 0 cartes en main ET 0 cartes en pioche gagne !

---

## Interface Détaillée

### Zone Supérieure
```
[Château] [Échange: 4 cartes]
```
- Affiche le plateau de jeu
- Montre les cartes de l'échange

### Zone Gauche
```
J1 Pioche
7 cartes
5 en main

J2 Pioche
8 cartes
4 en main
```
- État des pioches des joueurs
- Nombre de cartes en main

### Zone Droite
```
Journal des Actions
---
Tour 1: J1 pioche une carte
Tour 1: J1 place Marchand
J1 gagne! (0 cartes)
```
- Historique des actions
- Annonces des victoires

### Zone Inférieure
```
Main: [Carte1] [Carte2] [Carte3] ...
```
- Vos cartes en main
- Cliquez et glissez pour jouer

---

## Exemples de Jeu

### Exemple 1: Placement Simple
1. Vous avez un Marchand (place en cour)
2. Glissez-le sur une case vide de la cour
3. L'effet s'applique
4. C'est au joueur suivant

### Exemple 2: Soldat et Engin
- Si c'est le 4ème soldat sur un rempart
- L'engin de siège en face est renvoyé à l'échange
- Les cartes affectées reviennent à leurs joueurs

### Exemple 3: Victoire
1. Il vous reste 3 cartes en main
2. Vous tirez une de votre pioche (4 cartes)
3. Vous faites 2 actions
4. Action 1: Placer une carte (2 cartes)
5. Action 2: Placer une autre (1 carte)
6. Votre tour s'arrête
7. Au tour suivant, vous jouez votre dernière carte
8. Plus de cartes en main ni en pioche = **VICTOIRE !**

---

## Stratégie de Base

### Pour Gagner
1. **Préparez votre pioche**: Tirez régulièrement des cartes
2. **Videz votre main**: Placez des cartes quand c'est possible
3. **Anticipez la victoire**: Comptez vos cartes restantes
4. **Utilisez les effets**: Les effets peuvent vous aider à avancer

### Pièges à Éviter
1. **Accumuler des cartes**: Trop de cartes = pas de victoire bientôt
2. **Ignorer la pioche**: Vous avez besoin d'une pioche vide pour gagner
3. **Oublier les zones**: Les cartes ont des zones limitées

---

## Dépannage

### Le jeu ne démarre pas
```bash
# Vérifiez pygame
python3 -c "import pygame; print('OK')"

# Relancez
python3 main.py
```

### Je ne peux pas placer de carte
- Vérifiez la zone (bannière de couleur)
- Vérifiez qu'il y a une case libre
- Glissez clairement sur la zone

### La pioche est vide mais je ne gagne pas
- Vérifiez votre main (affichage en bas)
- Vous devez avoir 0 en main ET 0 en pioche
- Placez vos dernières cartes

---

## Fichiers Importants

- `main.py` - Point d'entrée
- `engine/game.py` - Moteur du jeu
- `engine/player.py` - Joueurs
- `engine/board.py` - Plateau
- `engine/card.py` - Cartes
- `engine/effects.py` - Effets
- `ui/renderer.py` - Affichage
- `Inventaire.csv` - Liste des cartes

---

## Documentation Supplémentaire

Voir les fichiers README pour plus d'infos :
- `SUMMARY_IMPLEMENTATION.md` - Résumé complet
- `RULES_IMPLEMENTATION.md` - Vérification des règles
- `CHANGELOG_IMPLEMENTATION.md` - Détails des modifications
- `rules.md` - Règles officielles du jeu

---

## Enjoy! 🎲

Amusez-vous bien en jouant à Castel avec les règles officielles !

