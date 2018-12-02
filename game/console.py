import pygame

from functools import wraps
import traceback
import sys


def only_active(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.active:
            return False
        return func(self, *args, **kwargs)
    return wrapper


class Console:
    _LOG_TEXT = 0
    _PROMPT_TEXT = 1
    _REPL_TEXT = 2
    _ERROR_TEXT = 3

    COLOURS = {
        _LOG_TEXT: (255, 255, 255),
        _PROMPT_TEXT: (0, 255, 0),
        _REPL_TEXT: (255, 255, 0),
        _ERROR_TEXT: (255, 0, 0),
    }

    PS1 = '>>> '
    PS2 = '... '

    def __init__(self, screen=None, height=400):
        self._stdout = sys.stdout
        sys.stdout = self

        self._screen = screen
        self.height = height
        self._lines = []
        self._l_buff = ''

        self.log('Debug console started')

        self.background = (0, 0, 0, 200)

        pygame.font.init()
        self.font = pygame.font.Font("assets/Monospace.ttf", 14)
        pygame.key.set_repeat(150, 20)

        self._h_cache = ''
        self._current = ''
        self._cursor = 0
        self._inp = ''
        self.active = False
        self._prompt = self.PS1
        self._history = []
        self._history_pos = 0

        self.exposes = {}

        self.expose(help=self.help, hide=self.hide)

    # Make file-like
    def write(self, text):
        self._stdout.write(text)
        for char in text:
            if char == '\n':
                self._lines.append((
                    self._LOG_TEXT,
                    self._l_buff
                ))
                self._l_buff = ''
                continue
            if char == '\r':
                continue
            self._l_buff += char

    def flush(self):
        self._stdout.flush()
        if self._l_buff:
            self.write('\n')

    @staticmethod
    def writable():
        return True

    @staticmethod
    def truncate(pos=None):
        pass

    @staticmethod
    def seekable():
        return False

    @staticmethod
    def tell():
        return 0

    @staticmethod
    def seek(_, __=0):
        return 0

    @staticmethod
    def readable():
        return False

    @staticmethod
    def isatty():
        return True

    def close(self):
        self.hide()

    # Rest 'o stuff
    def clear(self):
        self._lines = []

    def log(self, text):
        self.write(text + '\n')

    @staticmethod
    def help():
        print('Interactive help disabled in debug console!')

    @staticmethod
    def _closed(inp):
        brackets = []
        string = prev = None
        swap = ')(}{]['
        func = False
        for i in inp:
            if (i == '"' or i == "'") and prev != '\\':
                if string is None:
                    string = i
                elif string == i:
                    string = None
            if i in '([{':
                if string is None:
                    brackets.append(i)
            elif i in ')]}':
                if string is None:
                    if swap[swap.index(i) + 1] in brackets:
                        brackets.remove(swap[swap.index(i) + 1])
            if i == '\n' and prev == ':':
                func = True
            prev = i

        if inp.rstrip().endswith(':') or brackets:
            return False
        if func and not inp.strip(' ').endswith('\n'):
            return False

        return True

    def expose(self, **kwargs):
        for i in kwargs:
            self.exposes[i] = kwargs[i]

    def bind(self, screen):
        self._screen = screen

    def show(self):
        self.active = True

    def hide(self):
        self.active = False

    def toggle(self):
        self.active = not self.active

    def _return(self):
        self._lines.append((
            self._PROMPT_TEXT,
            self._prompt + self._current
        ))

        self._inp += self._current

        if self._current.strip():
            self._history.append(self._current)
        self._history_pos = 0
        self._h_cache = ''

        if not self._closed(self._inp):
            self._prompt = self.PS2
            self._inp += '\n'
            self._cursor = 0
            self._current = ' '
            return
        else:
            self._prompt = self.PS1

        if self._inp.strip():
            try:
                scope = globals()
                for i in self.exposes:
                    scope[i] = self.exposes[i]

                eval(compile(self._inp.rstrip(), '<console>', 'single'), scope)
            except:
                for n, i in enumerate(traceback.format_exc().strip().split('\n')):
                    if n in [1, 2]:
                        # Hide that we exists
                        continue
                    self._lines.append((
                        self._ERROR_TEXT,
                        i
                    ))
        self._current = self._inp = ''
        self._cursor = 0

    @only_active
    def tick(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self._cursor > 0:
                    self._current = self._current[:self._cursor - 1] + self._current[self._cursor:]
                    self._cursor -= 1
            elif event.key == pygame.K_DELETE:
                self._current = self._current[:self._cursor] + self._current[self._cursor + 1:]
            elif event.key == pygame.K_RETURN:
                self._return()
            elif event.key == pygame.K_LEFT:
                self._cursor = max(self._cursor - 1, 0)
            elif event.key == pygame.K_RIGHT:
                self._cursor = min(len(self._current), self._cursor + 1)
            elif event.key == pygame.K_TAB:
                self._cursor += 4
                self._current += ' ' * 4
            elif event.key == pygame.K_UP:
                if self._history_pos < len(self._history):
                    if self._history_pos == 0:
                        self._h_cache = self._current
                    self._history_pos += 1
                    self._current = self._history[-self._history_pos]
                    self._cursor = len(self._current)
            elif event.key == pygame.K_DOWN:
                if self._history_pos <= 1:
                    self._history_pos = 0
                    self._current = self._h_cache
                else:
                    self._history_pos -= 1
                    self._current = self._history[-self._history_pos]
                self._cursor = len(self._current)
            elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._current = ''
                self._cursor = 0
            elif event.unicode:
                self._current = self._current[:self._cursor] + event.unicode + self._current[self._cursor:]
                self._cursor += 1

            if event.key == pygame.K_BACKQUOTE:
                return False
            return True

    @only_active
    def render(self, rect=None):
        if not self.active:
            return

        if not isinstance(self._screen, pygame.Surface):
            raise ValueError("Console not bound to surface!")

        if rect is None:
            rect = pygame.Rect(0, 0, self._screen.get_width(), min(self.height, self._screen.get_height()))
        else:
            rect = pygame.Rect(rect)
        surface = pygame.Surface((rect.width, rect.height)).convert_alpha()
        surface.fill(self.background)

        line_height = self.font.get_linesize()
        if len(self._lines) * line_height < rect.height:
            n = -1
            for n, line in enumerate(self._lines):
                line = self.font.render(line[1], 1, self.COLOURS[line[0]])
                surface.blit(line, (rect.x, rect.y + n * line_height))
            y = rect.y + n * line_height
        else:
            for n, line in enumerate(self._lines[::-1]):
                if n * line_height > rect.height - line_height * 2:
                    break
                line = self.font.render(line[1], 1, self.COLOURS[line[0]])
                surface.blit(line, (rect.x, rect.y + rect.height - (n + 2) * line_height))
            y = rect.y + rect.height - line_height * 2

        y += line_height
        pre_c = self.font.render(self._prompt + self._current[:self._cursor], 1, self.COLOURS[self._PROMPT_TEXT])
        post_c = self.font.render(self._current[self._cursor:], 1, self.COLOURS[self._PROMPT_TEXT])
        surface.blit(pre_c, (rect.x, y))
        x = rect.x + pre_c.get_width()
        pygame.draw.line(surface, self.COLOURS[self._PROMPT_TEXT], (x + 1, y + 2), (x + 1, y + line_height - 2))
        surface.blit(post_c, (x, y))

        self._screen.blit(surface, (rect.x, rect.y))
