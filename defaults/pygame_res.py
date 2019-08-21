import pygame
from zsquirrel.utils.geometry import Rect


class Image:
    LOADED_IMAGES = {}

    def __init__(self, pygame_surface):
        if type(pygame_surface) is Image:
            pygame_surface = pygame_surface.pygame_surface
        self.pygame_surface = pygame_surface
        self.get_size = pygame_surface.get_size

        self._x_flip = None
        self._y_flip = None
        self._xy_flip = None

    def flip(self, x, y):
        x_flip = x and not y
        y_flip = y and not x
        xy_flip = x and y

        if x_flip and not self._x_flip:
            self._x_flip = Image(pygame.transform.flip(self.pygame_surface, x, y))

        if y_flip and not self._y_flip:
            self._y_flip = Image(pygame.transform.flip(self.pygame_surface, x, y))

        if xy_flip and not self._xy_flip:
            self._xy_flip = Image(pygame.transform.flip(self.pygame_surface, x, y))

        return {
            (True, False): self._x_flip,
            (False, True): self._y_flip,
            (True, True): self._xy_flip
        }[(x, y)]

    def subsurface(self, rect):
        return Image(self.pygame_surface.subsurface(rect.pygame_rect))

    def get_scaled(self, scale):
        w, h = self.get_size()
        w *= scale
        h *= scale
        size = int(w), int(h)
        image = pygame.transform.scale(self.pygame_surface, size)

        return Image(image)

    def fill(self, *args):
        self.pygame_surface.fill(*args)

    def set_color_key(self, arg=None):
        """
        Defines an alpha color key for the image. The 'arg' can either
        be an iterable defining a pixel on the image to sample or
        a color with R, G, B values between 0-255 (inclusive)

        :param arg: color: (int, int int) or point: (int, int)
        """
        surface = self.pygame_surface

        if len(arg) == 3:
            surface.set_colorkey(arg)
        else:
            surface.set_colorkey(
                surface.get_at(arg)
            )

    def blit(self, other, *args):
        if type(other) is Image:
            other = other.pygame_surface

        args = list(args)
        for arg in args:
            if type(arg) is Rect:
                args[args.index(arg)] = arg.pygame_rect

        self.pygame_surface.blit(other, *args)

    # noinspection PyArgumentList
    @staticmethod
    def get_surface(size, color=None, key=None):
        if not key:
            s = pygame.Surface(size, pygame.SRCALPHA, 32)
        else:
            s = pygame.Surface(size).convert()
            s.set_colorkey(key)

        if color:
            s.fill(color)

        return Image(s)

    @staticmethod
    def get_from_file(path):
        if path in Image.LOADED_IMAGES:
            return Image.LOADED_IMAGES[path]

        else:
            image = pygame.image.load(path)  # PYGAME CHOKE POINT
            image = Image(image)
            Image.LOADED_IMAGES[path] = image

        return image


class Sound:
    def __init__(self, pygame_sound):
        self.pygame_sound = pygame_sound
        self.play = pygame_sound.play
        self.stop = pygame_sound.stop

    @staticmethod
    def get_from_file(path):
        return Sound(pygame.mixer.Sound(path))
