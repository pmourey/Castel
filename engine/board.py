from pathlib import Path
import pygame

class Board:
    def __init__(self):
        self.cour = [[None for _ in range(4)] for _ in range(4)]  # 4x4 grid for interior
        self.exterieur = {}  # Dict for exterior positions, key: (x, y), value: card or tile
        self.tiles = {}  # For castle tiles, key: (x, y), value: {'type': 'tour' or 'rempart', 'rotation': 0-3, 'card': None}

        # Images will be loaded in renderer
        self.tour_img = None
        self.rempart_img = None
        self.card_images = {}  # key: card.nom, value: image

    def load_images(self):
        self.tour_img = pygame.image.load(Path(__file__).parent.parent / "images" / "Tour.png")
        self.rempart_img = pygame.image.load(Path(__file__).parent.parent / "images" / "Rempart.png")
        # Load card images
        images_dir = Path(__file__).parent.parent / "images"
        for color_dir in images_dir.iterdir():
            if color_dir.is_dir():
                for img_file in color_dir.iterdir():
                    if img_file.suffix.lower() == '.png':
                        name = img_file.stem
                        self.card_images[name] = pygame.image.load(img_file)

    def add_tile(self, x, y, tile_type, rotation=0):
        """Add a tile at position (x, y), rotation in degrees (0,90,180,270)"""
        self.tiles[(x, y)] = {'type': tile_type, 'rotation': rotation, 'card': None}

    def place_card(self, card, position):
        """Place a card at position. Position can be (x,y) for cour, exterieur, or tile"""
        if isinstance(position, tuple) and len(position) == 2:
            x, y = position
            if 0 <= x < 4 and 0 <= y < 4:
                # Courtyard
                self.cour[y][x] = card
            elif (x, y) in self.tiles:
                # Tile (tower or wall)
                self.tiles[(x, y)]['card'] = card
            else:
                # Exterior
                self.exterieur[(x, y)] = card

    def draw(self, screen):
        # Draw tiles and cards
        if self.tour_img and self.rempart_img:
            for (x, y), tile in self.tiles.items():
                img = self.tour_img if tile['type'] == 'tour' else self.rempart_img
                rotated = pygame.transform.rotate(img, tile['rotation'] * 90)
                screen.blit(rotated, (x * 50, y * 50))  # Placeholder positions
        # Draw cards in cour
        for y in range(4):
            for x in range(4):
                if self.cour[y][x]:
                    card = self.cour[y][x]
                    img = self.card_images.get(card.nom)
                    if img:
                        screen.blit(img, (x*60 + 200, y*60 + 200))
                    else:
                        pygame.draw.rect(screen, (255, 0, 0), (x*60 + 200, y*60 + 200, 50, 50))
        # Placeholder