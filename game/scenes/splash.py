from game.pyg import BMPFont
from .scene import Scene


class SlidesScene(Scene):
    SHOW = 4
    HIDE = 1
    FADE = 0.5
    SLIDES = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.font = BMPFont(self.path('tiles/font.png'), 16, 16, 3)
        self.font2 = BMPFont(self.path('tiles/font.png'), 16, 16, 1)
        self.font3 = BMPFont(self.path('tiles/font.png'), 16, 16, 6)

        self.fade = 0

        self.message = ''
        self.stage = 0
        self.state = self.SHOW
        self.slide = 0

    def _scene_went_active(self):
        self.slide = 0
        self.state = 0
        self.state = self.SHOW
        self.message = ''

    def next(self):
        pass

    def tick(self, dt):
        self.stage += dt

        if self.state == self.SHOW:
            if self.slide >= len(self.SLIDES):
                self.active = False
                self.next()
                return

            self.message = self.SLIDES[self.slide]
            if self.stage < self.FADE:
                self.fade = min(255, round((self.stage / self.FADE) * 255))
            elif self.stage > self.SHOW - self.FADE:
                self.fade = min(255, round(((self.SHOW - self.stage) / self.FADE) * 255))
            else:
                self.fade = 255

            if self.stage >= self.SHOW:
                self.stage = 0
                self.state = self.HIDE
        else:
            if self.stage >= self.HIDE:
                self.stage = 0
                self.state = self.SHOW
                self.slide += 1

    def render(self):
        self.screen.fill((25, 25, 25))

        if isinstance(self.message, str):
            t = self.font.render(self.message)
        else:
            if len(self.message) == 1:
                t = self.font2.render(self.message[0])
            else:
                t = self.font3.render(self.message[0])
        t.set_alpha(self.fade)
        self.screen.blit(t,
                         ((self.screen.get_width() - t.get_width()) / 2,
                          (self.screen.get_height() - t.get_height()) / 2))


class SplashScene(SlidesScene):
    SLIDES = [
        'A Game by Bottersnike',
        'With art by 8th Kingdom',
        ('BRINK', 2),
        ('Be careful. You bleed out from walking too much and crafting.',),
        ('Stand on top of items when combing them into new things.',),
        ('Hold H to list the full controls.',),
    ]

    def next(self):
        self._game.game_scene.start()


class GameOver(SlidesScene):
    SLIDES = [
        'You died.',
        'That sucks.',
        'Sacrifice too much?',
    ]

    def next(self):
        self._game.game_scene.start()
