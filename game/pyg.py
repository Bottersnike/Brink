import pygame


class TileSheet:
    def __init__(self, path, tw, th, scale=1, pad=0):
        self.pad = pad * scale
        self.image = pygame.image.load(path).convert_alpha()
        self.image = pygame.transform.scale(self.image,
                                            (self.image.get_width() * scale, self.image.get_height() * scale))
        self.tw, self.th = tw * scale, th * scale

        self._cache = {}

    def get_at(self, x, y, w=1, h=1, rot=0):
        if (x, y, w, h, rot) not in self._cache:
            x_pad = (2 * x + 1) * self.pad
            y_pad = (2 * y + 1) * self.pad
            self._cache[(x, y, w, h, rot)] = pygame.transform.rotate(self.image.subsurface(
                (x * self.tw + x_pad, y * self.th + y_pad, self.tw * w, self.th * h)), rot)

        return self._cache[(x, y, w, h, rot)]


class BMPFont:
    KEY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ .0123456789-?'

    def __init__(self, path, tw, th, scale=1, pad=0):
        self.ss = TileSheet(path, tw, th, scale, pad)

    def render(self, text, dark=False):
        text = [i.upper() for i in text if i.upper() in self.KEY]
        surf = pygame.Surface((len(text) * self.ss.tw, self.ss.th))
        surf.set_colorkey((255, 0, 255))
        for n, i in enumerate(text):
            i = self.KEY.index(i)
            surf.blit(self.ss.get_at(i % 16, i // 16 + (8 if dark else 0)), (n * self.ss.tw, 0))

        return surf
