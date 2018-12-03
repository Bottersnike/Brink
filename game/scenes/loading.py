import pygame

from game.pyg import BMPFont
from .scene import Scene


class LoadingScene(Scene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.font = BMPFont(self.path('tiles/FONT.png'), 16, 16, 2)
        self.font2 = BMPFont(self.path('tiles/FONT.png'), 16, 16, 1)

        self.message = ''
        self.progress = 0

        # Loading screen should always be a fallback active scene
        self.active = True

    def render(self):
        self.screen.fill((25, 25, 25))

        t = self.font.render('Loading...')
        self.screen.blit(t,
                         ((self.screen.get_width() - t.get_width()) / 2,
                          (self.screen.get_height() - t.get_height()) / 2 - 16))

        t2 = self.font2.render(self.message)
        self.screen.blit(t2,
                         ((self.screen.get_width() - t2.get_width()) / 2,
                          (self.screen.get_height() + t.get_height()) / 2))

        bar = pygame.Rect((self.screen.get_width() / 5 * 2, (self.screen.get_height() + t.get_height()) / 2 + 32,
                           self.screen.get_width() / 5, 10))
        pygame.draw.rect(self.screen, (70, 70, 70), bar)
        if self.progress:
            bar.width = bar.width / 100 * self.progress
            pygame.draw.rect(self.screen, (100, 200, 100), bar)
