class Player:
    def __init__(self, is_human=False, color='black'):
        self.is_human = is_human
        self.hand = []
        self.deck = []  # Pioche face cachée
        self.pions_color = color  # Couleur des pions du joueur
        self.pions_remaining = 13  # Nombre de pions disponibles