from os import listdir
from os.path import join

import pygame                           # PYGAME CHOKE POINT

from zs_constants import Resources as Res
from zs2.zson import load_zson, load_json

import pytmx

IMAGES = join(*Res.IMAGES)
SOUNDS = join(*Res.SOUNDS)
STYLES = join(*Res.STYLES)
TILEMAPS = join(*Res.TILEMAPS)


def get_path(directory, file_name):
    """
    Search for a file in a given directory and its subdirectories
    """
    names = [f for f in listdir(directory) if f[0] not in "._"]
    files = [n for n in names if "." in n]
    dirs = [n for n in names if n not in files]

    if file_name in files:
        return join(directory, file_name)

    else:
        for d in dirs:
            try:
                return get_path(
                    join(directory, d), file_name)

            except FileNotFoundError:
                pass

        raise FileNotFoundError(join(directory, file_name))


def load_resource(file_name, section=None):
    """
    Search for and load a resource file as an object by searching
        resource directories using file extension as context
        for file path
    The section argument can be used to return a single section
        from a .cfg file
    File_names with no extension will automatically look for a
        .cfg file
    Passing None, False, or "" as the file_name will automatically
        return the PROJECT_CFG file specified in zs_globals.py
    """

    if section:
        try:
            return load_resource(file_name)[section]

        except KeyError:
            warning = "No '{}' section found in {}".format(
                    section, file_name
                )
            print(warning)
            # raise ValueError(
            #     warning
            # )
            return {}

    else:
        ext = file_name.split(".")[-1]
        # print(file_name, ext)
        if ext == Res.JSON:
            path = get_path(Res.JSON, file_name)

        elif ext == Res.TMX:
            path = get_path(TILEMAPS, file_name)

        elif ext in Res.IMAGE_EXT:
            path = get_path(IMAGES, file_name)

        elif ext in Res.SOUND_EXT:
            path = get_path(SOUNDS, file_name)

        else:
            return ValueError("bad file type")

    return get_object(ext, path)


LOADED_IMAGES = {}


def get_object(ext, path):
    """
    Contextually initializes an object for a given resource based on
      the file extension of the resource being loaded
    """
    if ext == Res.JSON:
        return load_json(path)

    if ext in Res.IMAGE_EXT:
        if path in LOADED_IMAGES:
            return LOADED_IMAGES[path]

        else:
            image = pygame.image.load(path)            # PYGAME CHOKE POINT
            image = Image(image)
            LOADED_IMAGES[path] = image

            return image

    if ext == Res.TMX:
        return pytmx.TiledMap(path)

    # if ext in Res.SOUND_EXT:
    #     return pygame.mixer.Sound(path)             # PYGAME CHOKE POINT

    else:
        file = open(path, "r")
        text = file.read()
        file.close()

        return text


LOADED_FONTS = {}


def get_font(name, size, bold, italic):
    h_key = hash((name, size, bold, italic))
    # PYGAME CHOKE POINT

    if h_key in LOADED_FONTS:
        return LOADED_FONTS[h_key]

    else:
        path = pygame.font.match_font(name, bold, italic)
        font = pygame.font.Font(path, size)
        LOADED_FONTS[h_key] = font

        return font


class Image:
    def __init__(self, pygame_surface):
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

