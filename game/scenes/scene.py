import os


class Scene:
    ASSETS = '../../assets'

    def __init__(self, game, start_active=False):
        self._active = False
        self.active = start_active

        self.screen = game.screen
        self._game = game

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, val):
        if not self._active and val:
            self._scene_went_active()
        self._active = val

    def _scene_went_active(self):
        pass

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
