import threading
import random
import math
import time

import pygame

from typing import Optional, Tuple, List, Union
from game.pyg import TileSheet, BMPFont
from opensimplex import OpenSimplex
from .scene import Scene


def auto_crop(surface):
    sx = sy = 0
    ex, ey = surface.get_size()
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if surface.get_at((x, y))[3]:
                sx = x
                break
        else:
            continue
        break

    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            if surface.get_at((x, y))[3]:
                sy = y
                break
        else:
            continue
        break

    for x in list(range(surface.get_width()))[::-1]:
        for y in range(surface.get_height()):
            if surface.get_at((x, y))[3]:
                ex = x
                break
        else:
            continue
        break

    for y in list(range(surface.get_height()))[::-1]:
        for x in range(surface.get_width()):
            if surface.get_at((x, y))[3]:
                ey = y
                break
        else:
            continue
        break

    return surface.subsurface((sx, sy, ex - sx, ey - sy))


class GameScene(Scene):
    SHOW_CHAT = 5
    STACK_DIST = 0.25

    CONTROLS = 'WASD to move\n' \
               'C to craft\n' \
               '1-0 to select hotbar\n' \
               'Q to drop, F to pickup\n' \
               'SHIFT to crouch\n' \
               'LEFT CLICK to break\n' \
               'RIGHT CLICK to place\n' \
               'Hold H for help'

    # World gen
    OCTAVES = 2

    DUNGEON = -0.4
    DEEP = -0.1
    MEDIUM = 0.1
    SEA = 0.2
    BEACH = 0.25
    TREE_H = 0.3
    STONE_H = 0.8
    TOP_H = 0.85

    MAX_HUNGER = 10
    MAX_HEALTH = 10

    # World
    X_CHUNKS = 3
    Y_CHUNKS = 3

    CHUNK_W = 32
    CHUNK_H = 32

    WIDTH = X_CHUNKS * CHUNK_W
    HEIGHT = Y_CHUNKS * CHUNK_H

    ALTAR_BONUS = 0.25

    # Tiles
    WATER = 0, 0
    WATER_M = 4, 1
    WATER_D = 4, 0
    PLANK_W = 4, 2
    PLANK_F = 4, 3
    GRASS = 1, 0
    SAND = 2, 0
    TABLE = 0, 1
    FRACTURE = 1, 1
    SAND_DROP = 2, 1
    DIRT_DROP = 2, 2
    TREE = 0, 2
    LOG_DROP = 1, 2
    APPLE = 0, 3
    STICK = 1, 3
    MUD = 2, 3
    ROCK_S = 3, 0
    ROCK_R = 3, 1
    PICKAXE = 3, 3
    PLANK_F_DROP = 3, 2
    PLANK_W_DROP = 0, 4
    FLOWERS_C = 2, 4
    FLOWERS_B = 3, 4
    FLOWERS_W = 4, 4
    WET_ROCK = 5, 4

    Z_PIG = 5, 5
    PIG = 0, 5
    PIG_MEAT = 1, 4
    PIG_HEART = 1, 5

    CANDLE_L = 5, 0
    CANDLE = 5, 1
    ALTAR = 5, 2
    CANDLE_G = 4, 5
    RUBBLE = 5, 3
    ROCK_WALL = 3, 5
    TILE = 2, 5
    HIGH_STONE = 0, 6
    VINES = 1, 6
    BLOOD = 2, 6
    SKY_STONE = 3, 6
    EYE = 4, 6
    ANGEL = 5, 6

    SLIME = 6, 0
    GEM_L = 6, 1
    GEM_M = 6, 2
    GEM_S = 6, 3
    INGOT = 6, 4
    SWORD_S = 6, 5
    SWORD_I = 6, 6
    ARMOUR_S = 7, 0
    ARMOUR_I = 7, 1
    VAMPIRE = 7, 2

    # Assets
    HEART = 0, 0
    ARMOUR = 1, 0
    SHANK = 2, 0
    SATANICITY = 3, 0
    HOTBAR = 0, 1, 2, 2
    HOTBAR_S = 2, 1, 2, 2

    # Movement
    SPEED = {
        PLANK_F: 1.15,
        TILE: 1.2,
        WATER: 0.5,
        WATER_M: 0.25,
        WATER_D: 0.125,
        SAND: 1.05,
        MUD: 0.85,
        HIGH_STONE: 1.1,
        SKY_STONE: 1.1,
    }
    SHIFT_SPEED = 0.3

    BLOOD_COST = 0.05

    DIRECTION = {
        0: (0, -1),
        1: (-1, 0),
        2: (0, 1),
        3: (1, 0),
    }

    ROTATIONS = {
        # Left right up down
        (0, 0, 1, 0): 0,
        (0, 0, 0, 1): 180,
        (1, 0, 0, 0): 270,
        (0, 1, 0, 0): 90,
        (0, 1, 1, 0): 45,
        (0, 1, 0, 1): 135,
        (1, 0, 0, 1): 225,
        (1, 0, 1, 0): 315,
    }
    NO_ROT = (
        EYE,
        ANGEL,
        SLIME,
        VAMPIRE,
    )
    FLOATING = (
        EYE,
        ANGEL,
    )
    HOSTILE = (
        EYE,
        ANGEL,
        SLIME,
        VAMPIRE,
    )

    # Crafting
    RECIPIES = {
        (DIRT_DROP, DIRT_DROP, SAND_DROP): RUBBLE,
        (GEM_M, DIRT_DROP, DIRT_DROP): INGOT,
        (DIRT_DROP, DIRT_DROP): SAND_DROP,
        (STICK, STICK, RUBBLE): PICKAXE,
        (STICK, STICK, PIG_MEAT): CANDLE,
        (CANDLE, CANDLE, CANDLE): CANDLE_G,
        (PIG_HEART, PIG_HEART, PIG_HEART, CANDLE_G, CANDLE_G): ALTAR,
        (STICK, STICK, STICK, STICK): PLANK_F_DROP,
        (PLANK_F_DROP, PLANK_F_DROP): PLANK_W_DROP,
        (LOG_DROP,): STICK,
        (GEM_S, GEM_S, STICK): SWORD_S,
        (INGOT, INGOT, SWORD_S): SWORD_I,
        (GEM_L, PIG_HEART, PIG_MEAT): ARMOUR_S,
        (ARMOUR_S, INGOT, INGOT): ARMOUR_I,
    }
    SACRIFICES = {
        STICK: 0.05,
        SAND_DROP: 0.1,
        RUBBLE: 0.1,
        PICKAXE: 0.5,
        PLANK_F_DROP: 0.1,
        PLANK_W_DROP: 0.1,
        CANDLE: 0.5,
        CANDLE_G: 1,
        ALTAR: 4,
    }

    # Digging stuff
    BREAK_AMOUNT = {
        PICKAXE: 3,
        SWORD_S: 0.5,
        SWORD_I: 0.7,
    }
    SWING_AMOUNT = {
        PICKAXE: 3,
        SWORD_S: 5,
        SWORD_I: 10,
    }

    PROGRESSION = {
        GRASS: MUD,
        SAND: ROCK_S,
        MUD: ROCK_R,
        HIGH_STONE: ROCK_R,
    }
    DROPS = {
        GRASS: DIRT_DROP,
        SAND: SAND_DROP,
        MUD: DIRT_DROP,
        HIGH_STONE: RUBBLE,
    }
    HEALTH = {
        TREE: 3,
        PLANK_W: 10,
        CANDLE: 1,
        CANDLE_G: 3,
        CANDLE_L: 1,
        ALTAR: 25,
        ROCK_WALL: 15,
    }
    DIG_T = {
        GRASS: 0.3,
        SAND: 0.2,
        MUD: 0.3,
        HIGH_STONE: 0.8,
    }
    HUNGER = {
        SAND: 0.05,
        MUD: 0.1,
        ROCK_S: 0.1,
        ROCK_R: 0.1,
        HIGH_STONE: 0.2,

        TREE: 0.15,
        PLANK_W: 0.3,
        ROCK_WALL: 0.3,
        CANDLE: 0.3,
        CANDLE_L: 0.3,
        CANDLE_G: 0.9,
        ALTAR: 4,
    }
    E_DROPS = {
        TREE: LOG_DROP,
        ALTAR: ALTAR,
        CANDLE: CANDLE,
        CANDLE_L: CANDLE,
        PLANK_W: LOG_DROP,
        ROCK_WALL: RUBBLE,
        CANDLE_G: CANDLE_G,
    }
    A_HEALTH = {
        PIG: 10,
        Z_PIG: 30,
        EYE: 11,
        ANGEL: 50,
        SLIME: 2,
        VAMPIRE: 100,
    }

    PLACEABLE = (
        MUD, GRASS, SAND, ROCK_R, ROCK_S, TILE, PLANK_F, WET_ROCK, HIGH_STONE, SKY_STONE
    )
    NO_PICKUP = (
        BLOOD,
    )
    FLOWERS = (
        FLOWERS_B, FLOWERS_C, FLOWERS_W
    )

    # Waves 'n stuff
    WAVE_TIMERS = (
        1, 2, 3, 3, 3, 3, 3, 2, 1, 0.5, 0.25, 0.1
    )  # Minutes

    V_RANGE = {
        EYE: 75,
        ANGEL: 50,
        SLIME: 25,
        VAMPIRE: 25,
    }
    RANGE = {
        EYE: 2,
        ANGEL: 5,
        SLIME: 1,
        VAMPIRE: 5,
    }
    ATTACK = {
        EYE: 3,
        ANGEL: 3,
        SLIME: 1,
        VAMPIRE: 5,
    }
    ARMOUR_RATING = {
        ARMOUR_S: 2,
        ARMOUR_I: 5,
    }

    GEMS = {
        GEM_L: 0.9,
        GEM_M: 0.5,
        GEM_S: 0,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.difficulty = 0

        scale = 2
        ui_scale = scale * 2

        self.ground = TileSheet(self.path('tiles/ground.png'), 32, 32, scale)
        self.player = auto_crop(TileSheet(self.path('tiles/player.png'), 32, 32, scale).get_at(0, 0))
        self.assets = TileSheet(self.path('tiles/ui.png'), 8, 8, ui_scale)
        self.font = BMPFont(self.path('tiles/FONT.png'), 16, 16)

        self.world: List[List[Tuple]] = [
            [self.GRASS for _ in range(self.HEIGHT)]
            for _ in range(self.WIDTH)
        ]
        self.entities: List[List[int, int, Tuple[int, int]]] = [
            [5, 5, self.TABLE]
        ]
        self.g_entities: List[List[Union[int, Tuple[int, int]]]] = []
        self.animals: List[List[int, int, Tuple[int, int], int, int]] = []
        # x, y, [tx, ty], health, direction

        self.chat = []

        self.chunks = []
        self.o_chunks = []
        random.seed()
        self.scroll = [0, 0]
        self.pos = [self.WIDTH // 2 * self.ground.tw, self.HEIGHT // 2 * self.ground.th]
        self.last_tile = None

        self.health = self.MAX_HEALTH
        self.hunger = self.MAX_HUNGER

        self.digging = None
        # (tx, ty, end, after)

        self.flash = True
        self.m_lock = False
        pygame.time.set_timer(pygame.USEREVENT, 1000)
        pygame.time.set_timer(pygame.USEREVENT + 1, 2000)

        self.animal_thread = None

        self.hotbar: List[Optional[List[Union[List[int, int], int]]]] = [None] * 10
        self.altars = 0
        self.hb_p = 0

        self.p_rot = 0

        self.font = BMPFont(self.path('tiles/FONT.png'), 16, 16, 1)
        self.font2 = BMPFont(self.path('tiles/FONT.png'), 16, 16, 2)

        self.wave_timer = 0
        self.wave = 0

    def reset(self):
        self.hotbar = [None] * 10
        self.altars = 0
        self.hb_p = 0
        self.m_lock = False
        self.digging = None
        self.health = self.MAX_HEALTH
        self.hunger = self.MAX_HUNGER
        self.last_tile = None
        self.pos = [self.WIDTH // 2 * self.ground.tw, self.HEIGHT // 2 * self.ground.th]
        self.scroll = [0, 0]
        self.wave = self.wave_timer = 0

    def start(self):
        self.active = False
        self.reset()

        t = threading.Thread(target=self.grow)
        t.daemon = True
        t.start()

        self.animal_thread = threading.Thread(target=self.med_tick)
        self.animal_thread.daemon = True
        self.animal_thread.start()

        return self

    def set_at(self, x, y, tile):
        self.world[x][y] = tile
        cx, cy = int(x // self.CHUNK_W), int(y // self.CHUNK_H)
        rel_x, rel_y = x % self.CHUNK_W, y % self.CHUNK_H
        self.chunks[cx][cy].blit(self.ground.get_at(*tile), (rel_x * self.ground.tw, rel_y * self.ground.th))

    def grow(self, seed=None):
        self._game.scenes[-1].message = 'Generating world seed'
        self._game.scenes[-1].progress = 50
        self.g_entities = []
        self.entities = []
        self.animals = []

        self.chunks = [
            [
                pygame.Surface((self.CHUNK_W * self.ground.tw, self.CHUNK_H * self.ground.th))
                for _ in range(self.Y_CHUNKS)
            ] for _ in range(self.X_CHUNKS)
        ]
        # noinspection PyArgumentList
        self.o_chunks = [
            [
                pygame.Surface((self.CHUNK_W * self.ground.tw, self.CHUNK_H * self.ground.th)).convert_alpha()
                for _ in range(self.Y_CHUNKS)
            ] for _ in range(self.X_CHUNKS)
        ]
        for i in self.o_chunks:
            for j in i:
                j.fill((0, 0, 0, 0))

        px, py = self.pos[0] // self.ground.tw, self.pos[1] // self.ground.th
        if seed is None:
            while True:
                seed = random.random()
                gen = OpenSimplex(seed=round(seed * 100000))

                if self.TREE_H > gen.noise2d(px / self.WIDTH, py / self.HEIGHT) > self.SEA:
                    # Spawn near a beach
                    break
        else:
            gen = OpenSimplex(seed=round(seed * 100000))

        self._game.scenes[-1].message = 'Generating world surfaces'
        for x, row in enumerate(self.world):
            self._game.scenes[-1].progress = (x / len(self.world)) * 100

            for y, p in enumerate(row):
                v = gen.noise2d(x / self.WIDTH, y / self.HEIGHT)

                self.set_at(x, y,
                            self.WET_ROCK if v < self.DUNGEON else
                            self.WATER_D if v < self.DEEP else
                            self.WATER_M if v < self.MEDIUM else
                            self.WATER if v < self.SEA else
                            self.SAND if v < self.BEACH else
                            self.GRASS if v < self.STONE_H else
                            self.HIGH_STONE if v < self.TOP_H else
                            self.SKY_STONE)

                if (x, y) != (px, py):
                    if self.STONE_H > v > self.TREE_H:
                        if random.random() > 1 - v:
                            self.set_g(x, y, self.TREE)
                        elif random.random() > 0.85:
                            self.set_g(x, y, random.choice(self.FLOWERS), True)
                    elif self.STONE_H < v and random.random() * 2 < v:
                        self.set_g(x, y, self.VINES, True)
                    elif self.SEA < v:
                        if random.random() > 0.95:
                            self.animals.append([x * self.ground.tw, y * self.ground.th, self.PIG,
                                                 self.A_HEALTH[self.PIG], random.randint(0, 3), random.randint(32, 64)])

        self.active = True

    def set_g(self, x, y, type_, passive=False):
        health = self.HEALTH.get(type_, -1)
        cx, cy = int(x // self.CHUNK_W), int(y // self.CHUNK_H)
        xo, yo = (x % self.CHUNK_W) * self.ground.tw, (y % self.CHUNK_H) * self.ground.th
        if type_ is None:
            for i in self.g_entities:
                if (i[0], i[1]) == (x, y):
                    self.g_entities.remove(i)
                    pygame.draw.rect(self.o_chunks[cx][cy], (0, 0, 0, 0),
                                     (xo, yo, *self.ground.get_at(*i[2]).get_size()))
                    break
            else:
                pygame.draw.rect(self.o_chunks[cx][cy], (0, 0, 0, 0),
                                 (xo, yo, self.ground.tw, self.ground.th))
        else:
            if not passive:
                self.g_entities.append([x, y, type_, health])
            self.o_chunks[cx][cy].blit(self.ground.get_at(*type_), (xo, yo))

    def event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.hb_p = 0
            elif event.key == pygame.K_2:
                self.hb_p = 1
            elif event.key == pygame.K_3:
                self.hb_p = 2
            elif event.key == pygame.K_4:
                self.hb_p = 3
            elif event.key == pygame.K_5:
                self.hb_p = 4
            elif event.key == pygame.K_6:
                self.hb_p = 5
            elif event.key == pygame.K_7:
                self.hb_p = 6
            elif event.key == pygame.K_8:
                self.hb_p = 7
            elif event.key == pygame.K_9:
                self.hb_p = 8
            elif event.key == pygame.K_0:
                self.hb_p = 9
            elif event.key == pygame.K_q:
                # Drop item
                if self.hotbar[self.hb_p] is not None:
                    self.hotbar[self.hb_p][1] -= 1
                    self.drop_item(self.pos[0] / self.ground.tw, self.pos[1] / self.ground.th, self.hotbar[self.hb_p][0])
                    if self.hotbar[self.hb_p][1] <= 0:
                        self.hotbar[self.hb_p] = None
            elif event.key == pygame.K_c:
                self.do_craft()
        elif event.type == pygame.USEREVENT:
            self.slow_tick()
        elif event.type == pygame.USEREVENT + 1:
            self.super_slow_tick()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.click(event.pos)
            elif event.button == 3:
                self.use(event.pos, self.hotbar[self.hb_p], self.hb_p)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.digging = None
                self.m_lock = False

    def use(self, pos, item: Optional[List[Union[Tuple[int, int], int]]], index: int):
        if item is None:
            return

        xp, yp = pos[0] - self.scroll[0], pos[1] - self.scroll[1]
        tx, ty = int(xp // self.ground.tw), int(yp // self.ground.th)
        used = 0

        if item[0] == self.APPLE:
            if self.hunger < self.MAX_HUNGER:
                self.hunger += 0.5
                self.hunger = min(self.hunger, self.MAX_HUNGER)
                used = 1
        elif item[0] == self.PIG_MEAT:
            for i in self.g_entities:
                if i[2] == self.ALTAR and i[0] == tx and i[1] == ty:
                    i[3] -= 5
                    if i[3] <= 0:
                        self.set_g(i[0], i[1], None)
                        self.altars -= 1
                    self.health -= 1
                    self.hunger = max(self.hunger, self.hunger - 3)
                    self.do_chat('A zombie pig has appeared.')
                    self.animals.append([tx * self.ground.tw, ty * self.ground.th, self.Z_PIG,
                                         self.A_HEALTH[self.Z_PIG], random.randint(0, 3), random.randint(64, 128)])
                    used = 1
                    break
            else:
                if self.hunger < self.MAX_HUNGER:
                    self.hunger += 1
                    self.hunger = min(self.hunger, self.MAX_HUNGER)
                    used = 1
        elif item[0] == self.PIG_HEART:
            if self.health < self.MAX_HEALTH:
                self.health += 1
                self.health = min(self.health, self.MAX_HEALTH)
                used = 1
        elif item[0] == self.SAND_DROP:
            if self.world[tx][ty] in (self.ROCK_S, self.ROCK_R, self.WATER):
                self.set_at(tx, ty, self.SAND)
                used = 1
            elif self.world[tx][ty] == self.WATER_M:
                self.set_at(tx, ty, self.WATER)
                used = 1
            elif self.world[tx][ty] == self.WATER_D:
                self.set_at(tx, ty, self.WATER_M)
                used = 1
        elif item[0] == self.DIRT_DROP:
            if self.world[tx][ty] in (self.ROCK_S, self.ROCK_R, self.WATER):
                self.set_at(tx, ty, self.MUD)
                used = 1
            elif self.world[tx][ty] == self.WATER_M:
                self.set_at(tx, ty, self.WATER)
                used = 1
            elif self.world[tx][ty] == self.WATER_D:
                self.set_at(tx, ty, self.WATER_M)
                used = 1
        elif item[0] == self.RUBBLE:
            if self.world[tx][ty] in (self.ROCK_S, self.ROCK_R):
                self.set_at(tx, ty, self.TILE)
                used = 1
            elif self.world[tx][ty] in (self.MUD, self.GRASS, self.SAND):
                self.set_g(tx, ty, self.ROCK_WALL)
                used = 1
        elif item[0] == self.PLANK_F_DROP:
            if self.world[tx][ty] in (self.ROCK_S, self.ROCK_R):
                self.set_at(tx, ty, self.PLANK_F)
                used = 1
        elif item[0] == self.PLANK_W_DROP:
            if self.world[tx][ty] in (self.MUD, self.GRASS):
                self.set_g(tx, ty, self.PLANK_W)
                used = 1
        # Standard placeable items
        elif item[0] in (self.CANDLE, self.CANDLE_G, self.ALTAR):
            if self.world[tx][ty] in self.PLACEABLE:
                for i in self.g_entities:
                    if tuple(i[0:2]) == (tx, ty):
                        break
                else:
                    self.set_g(tx, ty, item[0])
                    if item[0] == self.ALTAR:
                        self.altars += 1
                    used = 1

        if used:
            item[1] -= used
            if item[1] <= 0:
                self.hotbar[index] = None

    def super_slow_tick(self):
        world_copy = [list(i) for i in self.world]

        for x, row in enumerate(world_copy):
            for y, p in enumerate(row):
                if p == self.MUD:
                    if ((y > 0 and row[y - 1] == self.GRASS) or (y < len(row) - 1 and row[y + 1] == self.GRASS) or
                            (x > 0 and world_copy[x - 1][y] == self.GRASS) or
                            (x < len(world_copy) - 1 and world_copy[x + 1][y] == self.GRASS)):
                        if random.random() > 0.85:
                            self.set_at(x, y, self.GRASS)

        if random.random() > 0.9:
            # Spawn pig
            ge = [(int(x), int(y)) for x, y, _, __ in self.g_entities]
            while True:
                x = random.randint(0, self.WIDTH - 1)
                y = random.randint(0, self.HEIGHT - 1)
                if self.world[x][y] in self.PLACEABLE:
                    if (x, y) not in ge:
                        break
            self.animals.append([x * self.ground.tw, y * self.ground.th, self.PIG,
                                 self.A_HEALTH[self.PIG], random.randint(0, 3), random.randint(32, 64)])

        self.health = min(self.health + self.altars * self.ALTAR_BONUS, self.MAX_HEALTH)

    def slow_tick(self):
        self.flash = not self.flash

        if self.hunger <= 0:
            self.health -= 0.2

        world_copy = [list(i) for i in self.world]

        water = (self.WATER, self.WATER_M, self.WATER_D)
        for x, row in enumerate(world_copy):
            for y, p in enumerate(row):
                if p in (self.ROCK_R, self.ROCK_S):
                    if ((y > 0 and row[y - 1] in water) or (y < len(row) - 1 and row[y + 1] in water) or
                            (x > 0 and world_copy[x - 1][y] in water) or
                            (x < len(world_copy) - 1 and world_copy[x + 1][y] in water)):
                        self.set_at(x, y, self.WATER)

        for i in list(self.animals):
            do_rand = True
            if i[2] in self.HOSTILE:
                dist = math.sqrt((self.pos[0] - i[0]) ** 2 + (self.pos[1] - i[1]) ** 2)
                # noinspection PyTypeChecker
                if dist < self.ground.tw * self.V_RANGE[i[2]]:
                    dx, dy = self.pos[0] - i[0], self.pos[1] - i[1]
                    if abs(dx) > abs(dy):
                        i[4] = 3 if dx > 0 else 1
                    else:
                        i[4] = 2 if dy > 0 else 0
                    do_rand = False

                # noinspection PyTypeChecker
                if dist < self.ground.tw * self.RANGE[i[2]]:
                    self.health -= self.ATTACK[i[2]] / self.armour

            if do_rand and random.random() > 0.8:
                i[4] = (i[4] + random.randint(-1, 1)) % 4

            if i[2] not in self.FLOATING:
                tx, ty = int(i[0] // self.ground.tw), int(i[1] // self.ground.th)
                if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT:
                    if self.world[tx][ty] in (self.WATER, self.WATER_M, self.WATER_D):
                        self.damage_animal(i)

    def med_tick(self):
        while not self.active:
            time.sleep(0.1)

        while self.active:
            ge = [(int(x), int(y)) for x, y, _, __ in self.g_entities]

            # Move animals
            for i in self.animals:
                if i[2] in self.FLOATING:
                    tx, ty = int(i[0] // self.ground.tw), int(i[1] // self.ground.th)
                    if not (0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT):
                        self.animals.remove(i)
                        continue

                    dx, dy = self.DIRECTION[i[4]]
                    i[0] += dx * i[5]
                    i[1] += dy * i[5]
                else:
                    while True:
                        tx, ty = int(i[0] // self.ground.tw), int(i[1] // self.ground.th)

                        if (tx, ty) not in ge:
                            break
                        i[0] += self.DIRECTION[i[4]][0] * self.ground.tw
                        i[1] += self.DIRECTION[i[4]][1] * self.ground.th
                    if 0 <= tx < self.WIDTH and 0 <= ty < self.HEIGHT:
                        speed_mod = self.SPEED.get(self.world[tx][ty], 1)
                    else:
                        self.animals.remove(i)
                        continue

                    dx, dy = self.DIRECTION[i[4]]
                    dx *= speed_mod * i[5] / 16
                    dy *= speed_mod * i[5] / 16

                    ntx, nty = int((i[0] + dx) // self.ground.tw), int((i[1] + dy) // self.ground.th)

                    for dxi in range(0, 2 if (i[0] + dx) % self.ground.tw != 0 else 1):
                        for dyi in range(0, 2 if (i[1] + dy) % self.ground.th != 0 else 1):
                            if (ntx + dxi, nty + dyi) in ge:
                                break
                        else:
                            continue
                        break
                    else:
                        i[0] += dx
                        i[1] += dy
            time.sleep(0.1)

    def damage_animal(self, animal, amount=1):
        animal[3] -= amount

        if animal[3] <= 0:
            self.animals.remove(animal)

            if animal[2] == self.PIG:
                if random.random() > .5:
                    self.drop_item(animal[0] / self.ground.tw, animal[1] / self.ground.th, self.PIG_HEART)
                self.drop_item(animal[0] / self.ground.tw, animal[1] / self.ground.th, self.PIG_MEAT)
            elif animal[2] == self.Z_PIG:
                self.drop_item(animal[0] / self.ground.tw, animal[1] / self.ground.th, self.PIG_HEART)
            elif animal[2] in self.HOSTILE:
                for i in self.GEMS:
                    if random.random() > self.GEMS[i]:
                        self.drop_item(animal[0] / self.ground.tw, animal[1] / self.ground.th, i)

    def click(self, pos):
        if self.hunger <= 0:
            return

        xp, yp = pos[0] - self.scroll[0], pos[1] - self.scroll[1]
        tx, ty = int(xp // self.ground.tw), int(yp // self.ground.th)

        for i in list(self.animals):
            r = pygame.Rect(*i[0:2], self.ground.tw, self.ground.th)
            if r.collidepoint(xp, yp):
                self.damage_animal(i, self.swing_damage())
                self.m_lock = True
                return

        for i in list(self.g_entities):
            x, y, _, __ = i
            r = pygame.Rect(x * self.ground.tw, y * self.ground.th, self.ground.tw, self.ground.th)
            if r.collidepoint(xp, yp):
                if i[2] in self.HEALTH:
                    i[3] -= self.damage()
                    if i[3] <= 0:
                        self.set_g(i[0], i[1], None)
                        if i[2] == self.ALTAR:
                            self.altars -= 1

                        self.drop_item(x + 0.1, y + 0.1, self.E_DROPS[i[2]])
                        if i[2] == self.TREE:
                            if random.random() > 0.3:
                                self.drop_item(x, y, self.APPLE)
                        self.hunger -= self.HUNGER[i[2]]
                    self.m_lock = True
                    return

        if not self.m_lock:
            if self.world[tx][ty] in self.PROGRESSION:
                self.digging = (tx, ty, time.time() + self.DIG_T[self.world[tx][ty]],
                                self.PROGRESSION[self.world[tx][ty]], self.DROPS[self.world[tx][ty]])

    def damage(self):
        if self.hotbar[self.hb_p] is None:
            return 1

        # noinspection PyTypeChecker
        return self.BREAK_AMOUNT.get(self.hotbar[self.hb_p][0], 1)

    def swing_damage(self):
        if self.hotbar[self.hb_p] is None:
            return 1

        # noinspection PyTypeChecker
        return self.SWING_AMOUNT.get(self.hotbar[self.hb_p][0], 1)

    def do_craft(self):
        p_rect = pygame.Rect(*self.pos, *self.player.get_size())
        usable = []

        for i in list(self.entities):
            x, y, _ = i
            if p_rect.colliderect(pygame.Rect(x * self.ground.tw, y * self.ground.th, self.ground.tw, self.ground.th)):
                usable.append(i)

        for i in self.RECIPIES:
            crafted = self.can_craft(i, usable)
            if crafted:
                for j in crafted:
                    self.entities.remove(j)
                self.drop_item(self.pos[0] / self.ground.tw, self.pos[1] / self.ground.th, self.RECIPIES[i])

                self.health -= self.SACRIFICES.get(self.RECIPIES[i], 0)
                break

    @property
    def armour(self):
        base = 1
        for i in self.hotbar:
            if i is not None:
                base += self.ARMOUR_RATING.get(i[0], 0)
        return base

    @staticmethod
    def can_craft(ingredients, usable):
        used = []
        ingredients, usable = list(ingredients), list(usable)
        for i in ingredients:
            for j in usable:
                if j[2] == i:
                    break
            else:
                return False
            usable.remove(j)
            used.append(j)
        return used

    def drop_item(self, x, y, item):
        for ix, iy, ii in self.entities:
            if math.sqrt((ix - x) ** 2 + (iy - y) ** 2) < self.STACK_DIST:
                return self.drop_item(x + self.STACK_DIST, y, item)
        self.entities.append([x, y, item])

    def do_wave(self):
        if self.difficulty == 1:
            return

        self.wave_timer = 0

        if self.wave < len(self.WAVE_TIMERS) - 1:
            self.wave += 1

        for _ in range(self.wave * (self.altars + 1)):
            for j in (self.EYE, self.ANGEL, self.SLIME, self.SLIME, self.Z_PIG, self.Z_PIG, self.VAMPIRE):
                if j == self.ANGEL and self.wave <= 4:
                    continue
                if j == self.VAMPIRE and self.wave <= 7:
                    continue

                while True:
                    x, y = random.randint(0, self.WIDTH - 1), random.randint(0, self.HEIGHT - 1)
                    if self.world[x][y] in self.PLACEABLE:
                        for i in self.g_entities:
                            if i[0] == x and i[1] == y:
                                break
                        else:
                            break

                self.animals.append([
                    x * self.ground.tw, y * self.ground.th,
                    j, self.A_HEALTH[j], 0, 16
                ])

        self.do_chat('Incoming wave. Next wave in {}m'.format(self.WAVE_TIMERS[self.wave] * max(1, self.altars - 2)))

    def tick(self, dt):
        self.wave_timer += dt
        if self.wave_timer > self.WAVE_TIMERS[self.wave] * 60 * max(1, self.altars - 2):
            self.do_wave()
        if self.health < 0:
            self._game.game_over.active = True
            self.active = False

        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()

        right = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        up = keys[pygame.K_w] or keys[pygame.K_UP]
        down = keys[pygame.K_s] or keys[pygame.K_DOWN]

        # Move player
        tx, ty = int(self.pos[0] // self.ground.tw), int(self.pos[1] // self.ground.th)
        speed_mod = self.SPEED.get(self.world[tx][ty], 1)

        if mods & pygame.KMOD_SHIFT:
            speed_mod *= self.SHIFT_SPEED

        speed = dt * 8 * self.ground.tw * speed_mod
        if (right ^ left) and (up ^ down):
            speed = (speed ** 2 / 2) ** 0.5

        dx = dy = 0
        if right and not left:
            dx = speed
        elif left and not right:
            dx = -speed
        if up and not down:
            dy = -speed
        elif down and not up:
            dy = speed

        if up and down:
            up = down = False
        if left and right:
            left = right = False
        if up or down or left or right:
            self.p_rot = self.ROTATIONS[(left, right, up, down)]

        if dx:
            p_rect = pygame.Rect(self.pos[0] + dx, self.pos[1], *self.player.get_size())
            for x, y, _, __ in list(self.g_entities):
                if p_rect.colliderect(
                        pygame.Rect(x * self.ground.tw, y * self.ground.th, self.ground.tw, self.ground.th)):
                    if p_rect.left < x * self.ground.tw:
                        self.pos[0] = x * self.ground.tw - self.player.get_width()
                        break
                    else:
                        self.pos[0] = (x + 1) * self.ground.tw
                        break
            else:
                self.pos[0] += dx
        if dy:
            p_rect = pygame.Rect(self.pos[0], self.pos[1] + dy, *self.player.get_size())
            for x, y, _, __ in list(self.g_entities):
                if p_rect.colliderect(
                        pygame.Rect(x * self.ground.tw, y * self.ground.th, self.ground.tw, self.ground.th)):
                    if p_rect.top < y * self.ground.th:
                        self.pos[1] = y * self.ground.th - self.player.get_height()
                        break
                    else:
                        self.pos[1] = (y + 1) * self.ground.th
                        break
            else:
                self.pos[1] += dy

        if (tx, ty) != self.last_tile:
            for i in self.entities:
                x, y, p = i
                if x == tx and y == ty and p == self.BLOOD:
                    self.entities.remove(i)
                    self.health += self.BLOOD_COST
                    break
            else:
                if not mods & pygame.KMOD_SHIFT:
                    if random.random() > .7:
                        self.health -= self.BLOOD_COST
                        self.entities.insert(0, [tx, ty, self.BLOOD])

        self.last_tile = (tx, ty)

        self.pos[0] = max(0, min(self.pos[0], self.WIDTH * self.ground.th - self.player.get_width()))
        self.pos[1] = max(0, min(self.pos[1], self.HEIGHT * self.ground.tw - self.player.get_height()))

        # Scroll to player
        self.scroll[0] = -self.pos[0] + self.screen.get_width() / 2 - self.player.get_width() / 2
        self.scroll[1] = -self.pos[1] + self.screen.get_height() / 2 - self.player.get_height() / 2

        # Limit scroll
        self.scroll[0] = min(0, max(self.WIDTH * -self.ground.tw + self.screen.get_width(), self.scroll[0]))
        self.scroll[1] = min(0, max(self.HEIGHT * -self.ground.th + self.screen.get_height(), self.scroll[1]))

        # Digging
        if not self.m_lock:
            pos = pygame.mouse.get_pos()
            xp, yp = pos[0] - self.scroll[0], pos[1] - self.scroll[1]
            tx, ty = int(xp // self.ground.tw), int(yp // self.ground.th)
            if self.digging is None or (tx, ty) != self.digging[0:2]:
                if pygame.mouse.get_pressed()[0]:
                    self.click(pos)

            if self.digging is not None:
                if time.time() >= self.digging[2]:
                    self.set_at(tx, ty, self.digging[3])
                    self.drop_item(tx, ty, self.digging[4])
                    self.hunger -= self.HUNGER[self.digging[3]]
                    self.set_g(tx, ty, None)
                    self.digging = None

        # Picking up
        p_rect = pygame.Rect(*self.pos, *self.player.get_size())
        if keys[pygame.K_f]:
            for i in list(self.entities):
                x, y, _ = i
                if p_rect.colliderect(
                        pygame.Rect(x * self.ground.tw, y * self.ground.th, self.ground.tw, self.ground.th)):
                    self.pickup(i)

    def pickup(self, entity):
        if entity[2] in self.NO_PICKUP:
            return

        for i in self.hotbar:
            if i is not None:
                if i[0] == entity[2]:
                    i[1] += 1
                    self.entities.remove(entity)
                    return

        if None in self.hotbar:
            for n, i in enumerate(self.hotbar):
                if i is None:
                    self.hotbar[n] = [entity[2], 1]
                    self.entities.remove(entity)
                    return

    def do_chat(self, msg):
        self.chat.append((msg, time.time()))

    def render(self):
        cx, cy = int(self.pos[0] // (self.CHUNK_W * self.ground.tw)), int(
            self.pos[1] // (self.CHUNK_H * self.ground.th))
        sp = self.scroll[0] + (cx * self.CHUNK_W * self.ground.tw), self.scroll[1] + (
                cy * self.CHUNK_H * self.ground.th)
        for dx in range(-1 if sp[0] > 0 else 0,
                        2 if sp[0] + self.CHUNK_W * self.ground.tw < self.screen.get_width() else 1):
            for dy in range(-1 if sp[1] > 1 else 0,
                            2 if sp[1] + self.CHUNK_H * self.ground.th < self.screen.get_height() else 1):
                self.screen.blit(self.chunks[cx + dx][cy + dy], (
                    sp[0] + (dx * self.CHUNK_W * self.ground.tw), sp[1] + (dy * self.CHUNK_W * self.ground.tw)))
                self.screen.blit(self.o_chunks[cx + dx][cy + dy], (
                    sp[0] + (dx * self.CHUNK_W * self.ground.tw), sp[1] + (dy * self.CHUNK_W * self.ground.tw)))

        if self.digging is not None:
            x = self.digging[0] * self.ground.tw + self.scroll[0]
            y = self.digging[1] * self.ground.th + self.scroll[1]
            self.screen.blit(self.ground.get_at(*self.FRACTURE), (x, y))

        for x, y, p in self.entities:
            x = x * self.ground.tw + self.scroll[0]
            y = y * self.ground.th + self.scroll[1]
            if self.screen.get_width() > x > -self.ground.tw and self.screen.get_height() > y > - self.ground.th:
                self.screen.blit(self.ground.get_at(*p), (x, y))

        for x, y, p, h in self.g_entities:
            if h != self.HEALTH.get(p, h):
                x = x * self.ground.tw + self.scroll[0]
                y = y * self.ground.th + self.scroll[1]
                if self.screen.get_width() > x > -self.ground.tw and self.screen.get_height() > y > - self.ground.th:
                    pygame.draw.rect(self.screen, (50, 50, 50), (x + 8, y + self.ground.th - 5, self.ground.tw - 16, 4))

                    nw = ((self.ground.tw - 16) / self.HEALTH[p]) * h
                    pygame.draw.rect(self.screen, (200, 50, 50), (x + 8, y + self.ground.th - 5, nw, 4))

        for x, y, p, h, d, _ in self.animals:
            x += self.scroll[0]
            y += self.scroll[1]
            if self.screen.get_width() > x > -self.ground.tw and self.screen.get_height() > y > - self.ground.th:
                rot = d * 90 if p not in self.NO_ROT else 0
                self.screen.blit(self.ground.get_at(*p, rot=rot), (x, y))

                if h != self.A_HEALTH.get(p, h):
                    pygame.draw.rect(self.screen, (50, 50, 50), (x + 8, y + self.ground.th - 5, self.ground.tw - 16, 4))

                    nw = ((self.ground.tw - 16) / self.A_HEALTH[p]) * h
                    pygame.draw.rect(self.screen, (200, 50, 50), (x + 8, y + self.ground.th - 5, nw, 4))

        player = pygame.transform.rotate(self.player, 360 - self.p_rot)
        self.screen.blit(player, (self.pos[0] + self.scroll[0], self.pos[1] + self.scroll[1]))

        # HUD
        health = math.ceil(self.health) if self.flash else math.floor(self.health)
        armour = math.ceil(self.armour) if self.flash else math.floor(self.armour)
        hunger = math.ceil(self.hunger) if self.flash else math.floor(self.hunger)

        for n in range(health):
            x = (self.assets.tw + 8) * n + 32
            y = 32
            self.screen.blit(self.assets.get_at(*self.HEART), (x, y))

        for n in range(armour):
            x = (self.assets.tw + 8) * n + 32
            y = 48 + self.assets.th * 2
            self.screen.blit(self.assets.get_at(*self.ARMOUR), (x, y))

        for n in range(hunger):
            x = (self.assets.tw + 8) * n + 32
            y = 40 + self.assets.th
            self.screen.blit(self.assets.get_at(*self.SHANK), (x, y))

        for n in range(self.altars):
            x = (self.assets.tw + 8) * n + 32
            y = 56 + self.assets.th * 3
            self.screen.blit(self.assets.get_at(*self.SATANICITY), (x, y))

        if self._game.DEVEL:
            fps = self.font.render(str(round(self._game.clock.get_fps(), 2)) + ' FPS', True)
            self.screen.blit(fps, (self.screen.get_width() - fps.get_width() - 8,
                                   self.screen.get_height() - fps.get_height() - 8))

            brand = self.font.render('Alpha 0.0.1A', True)
            self.screen.blit(brand, (8, self.screen.get_height() - brand.get_height() - 8))

            dev = self.font.render('RUNNING IN DEVEL ENVIRONMENT')
            self.screen.blit(dev, (self.screen.get_width() - dev.get_width() - 8, 8))

        hbw = self.assets.tw * 2 + 16
        x = (self.screen.get_width() - hbw * len(self.hotbar)) / 2
        y = self.screen.get_height() - hbw - 32
        for n, i in enumerate(self.hotbar):
            if n == self.hb_p:
                self.screen.blit(self.assets.get_at(*self.HOTBAR_S), (x, y))
            else:
                self.screen.blit(self.assets.get_at(*self.HOTBAR), (x, y))
            if i is not None:
                n = self.font.render(str(i[1]), True)
                self.screen.blit(self.ground.get_at(*i[0]), (x, y))
                self.screen.blit(n, (x + 8, y + self.assets.tw * 2 - n.get_height() - 8))
            x += hbw

        # Console
        y = self.screen.get_height() - 156
        now = time.time()
        for line, t in self.chat[::-1]:
            if now - t > self.SHOW_CHAT:
                continue

            alpha = round(min(255, (self.SHOW_CHAT - (now - t)) * 255))
            t = self.font.render(line, True).convert()
            t.set_alpha(alpha)
            self.screen.blit(t, (56, y))
            y -= 20

        # Help menu
        if pygame.key.get_pressed()[pygame.K_h]:
            darken = pygame.Surface(self.screen.get_size())
            darken.set_alpha(200)
            self.screen.blit(darken, (0, 0))

            self.screen.blit(self.font2.render('Controls:'), (16, 16))
            y = 56
            for line in self.CONTROLS.split('\n'):
                self.screen.blit(self.font.render(line), (32, y))
                y += 20

            self.screen.blit(self.font2.render('Recipies:'), (16, y + 16))
            y += 56

            sx = 32
            for ingredients, result in self.RECIPIES.items():
                x = sx
                for i in ingredients:
                    self.screen.blit(self.assets.get_at(*self.HOTBAR), (x, y))
                    self.screen.blit(self.ground.get_at(*i), (x, y))
                    x += self.assets.tw * 2 + 4

                x += 16
                self.screen.blit(self.assets.get_at(*self.HOTBAR_S), (x, y))
                self.screen.blit(self.ground.get_at(*result), (x, y))

                y += self.assets.th * 2 + 8
                if y + self.assets.th * 2 > self.screen.get_height():
                    y = 16
                    sx += 512
            pass
