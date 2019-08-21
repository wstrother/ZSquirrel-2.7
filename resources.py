from os.path import join
from os import listdir

from defaults.pygame_res import Image
# import json
# import pygame

import zsquirrel.constants as con

FILE_EXT_ERROR = "unrecognized file extension '{}'"

# pygame.init()
# pygame.mixer.quit()
# pygame.mixer.init(buffer=256)


class ResourceLoader:
    """
    This class is instantiated to provide a set of customizable object loader
    methods that can be matched to file extension keys. Each method should return
    a function object instance based on the file type. Different loaders can be
    set at runtime and are used contextually load_resource() method.
    """
    def __init__(self):
        """
        Sets up a dict to match object loader methods to file extension keys
        """
        self.loader_methods = {}

    def get_path(self, directory, file_name):
        """
        Search for a file in a given directory and its subdirectories
        and return it's relative path as a str.

        Resource subdirectory names should not contain any '.' characters
        or begin with a '_' character.

        :param directory: str for the top level resource directory, such as
            "images" or "json"
        :param file_name: str for the file name, including extension

        :return str of the full relative file path
        """
        if con.RESOURCES not in directory:
            directory = join(con.RESOURCES, directory)

        names = [f for f in listdir(directory) if f[0] not in "._"]
        files = [n for n in names if "." in n]
        dirs = [n for n in names if n not in files]

        if file_name in files:
            return join(directory, file_name)

        else:
            for d in dirs:
                try:
                    return self.get_path(join(directory, d), file_name)

                except FileNotFoundError:
                    pass

        raise FileNotFoundError(join(directory, file_name))

    def load_resource(self, file_name):
        """
        loads any file stored in a resource subdirectory and contextually
        instantiates an object by matching the extension to the correct
        loader method by calling get_object()

        :param file_name: str, the name of any file in the appropriate
            resources subdirectory

        :return: object, the output of the appropriate loader method
        """
        ext = file_name.split(".")[-1]

        if ext == con.JSON:
            path = self.get_path(con.JSON, file_name)

        elif ext in con.IMAGE_EXT:
            path = self.get_path(con.IMAGES, file_name)

        elif ext in con.SOUND_EXT:
            path = self.get_path(con.SOUNDS, file_name)

        else:
            raise ValueError(FILE_EXT_ERROR.format(ext))

        return self.get_object(ext, path)

    def get_object(self, ext, path):
        """
        :param ext: str, the file extension, used as key for the
            loader_methods dict
        :param path: str, the full relative file path, passed to the
            method in the loader_methods dict

        :return: object, the output of the appropriate loader method
        """
        if ext in self.loader_methods:
            load = self.loader_methods[ext]
        else:
            return ValueError(FILE_EXT_ERROR.format(ext))

        return load(path)

    # @classmethod
    # def get_default_loader(cls):
    #     """
    #     This method helps generate the appropriate loader_methods to
    #     match typical file_extensions to the default ZSquirrel library
    #     implementation of different resources.
    #
    #     By default, Sound and Image files are loaded and instantiated
    #     through wrapper classes based around the Pygame library.
    #
    #     JSON data is also supported, being loaded as a standard dict object
    #     """
    #     methods = {}
    #
    #     # IMAGES
    #
    #     for ext in con.IMAGE_EXT:
    #         methods[ext] = Image.get_from_file
    #
    #     # AUDIO
    #
    #     for ext in con.SOUND_EXT:
    #         methods[ext] = Sound.get_from_file
    #
    #     # JSON
    #
    #     def load_json(path):
    #         file = open(path, "r")
    #         d = json.load(file)
    #         file.close()
    #
    #         return d
    #
    #     methods[con.JSON] = load_json
    #     resource_loader = cls()
    #     resource_loader.loader_methods.update(methods)
    #
    #     return resource_loader

    @staticmethod
    def clear_default_caches():
        Image.LOADED_IMAGES = {}


