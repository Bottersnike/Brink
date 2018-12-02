import time
import os

import pygame

from .scenes import *
from .console import Console


os.environ['SDL_VIDEO_CENTERED'] = '1'


class Game:
    FLAGS = 0
    WIDTH = 1280
    HEIGHT = 720

    DEVEL = 'LD_DEVEL' in os.environ

    FPS = 0

    def __init__(self, width=None, height=None, fs=False, diff=0):
        if width is not None:
            self.WIDTH = width
        if height is not None:
            self.HEIGHT = height
        if fs:
            self.FLAGS |= pygame.FULLSCREEN

        pygame.init()

        try:
            base = os.path.dirname(__file__)
        except NameError:
            base = os.getcwd()
        icon = pygame.image.load(os.path.join(base, '../assets/icon16.png'))

        pygame.display.set_icon(icon)
        pygame.display.set_caption('Brink', 'Brink')
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), self.FLAGS)
        self.clock = pygame.time.Clock()

        self.console = Console()
        self.console.bind(self.screen)

        self.running = True
        self.game_scene = GameScene(self)
        self.game_scene.difficulty = diff
        self.game_over = GameOver(self)
        self.scenes = [
            SplashScene(self, True),
            self.game_over,
            self.game_scene,
            LoadingScene(self),
        ]

        if self.DEVEL:
            self.scenes[0].active = False
            self.game_scene.start()

        self.console.expose(game=self, scenes=self.scenes, gs=self.game_scene)

    def tick(self, dt):
        for i in self.scenes:
            if i.active:
                if not i.tick(dt):
                    break

        self.clock.tick(self.FPS)

    def render(self):
        for i in self.scenes:
            if i.active:
                if not i.render():
                    break

        self.console.render()
        pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if not (event.type == pygame.KEYDOWN and event.key == pygame.K_BACKQUOTE):
                if self.console.tick(event):
                    # The console grabbed the event, ignore it
                    continue

            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKQUOTE:
                    self.console.toggle()
                elif event.key == pygame.K_F11:
                    self.FLAGS ^= pygame.FULLSCREEN
                    (w, h) = (0, 0) if self.FLAGS & pygame.FULLSCREEN else (self.WIDTH, self.HEIGHT)
                    self.screen = pygame.display.set_mode((w, h), self.FLAGS)
                    for i in self.scenes:
                        i.screen = self.screen

            for i in self.scenes:
                if i.active:
                    if not i.event(event):
                        break

    def mainloop(self):
        dt = 0
        while self.running:
            fs = time.time()
            self.tick(dt)
            self.render()
            self.events()
            dt = time.time() - fs
            dt = min(dt, 1 / 20)

        pygame.quit()
