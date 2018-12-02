import os


class Scene:
    ASSETS = '../../assets'

    def __init__(self, game, start_active=False):
        self.active = start_active

        self.screen = game.screen
        self._game = game

    def render(self):
        pass

    def tick(self, dt):
        pass

    def event(self, event):
        pass

    def start(self):
        self.active = True
        return self

    def path(self, path):
        try:
            base = os.path.dirname(__file__)
        except NameError:
            base = os.getcwd()

        return os.path.join(base, self.ASSETS, path)
