import pygame
from resources import Image

# This module defines a basic Game and Screen object that will regulate
# the main input / update / output loop of your ZSquirrel application.
#
# The methods are mostly very simple and establish an extendable protocol
# for interaction between the Environment and Context modules, which are
# essentially the "ROM" and "RAM" of the "game" itself, as well as the
# Screen object which essentially exposes a backend to whatever graphical
# output platform you wish to use for a project.
#
# By default, a Pygame / SDL based Screen object is supported (as well as
# a Controller input module that uses the same backend).


class Game:
    """
    The Game object is instantiated once per application and
    the Game.main() method is called to implement the main
    input / update / output loop.
    """

    def __init__(self, environment, screen=None, clock=None, frame_rate=1):
        """
        :param screen: a Screen object that implements the graphical backend
        :param clock: an optional Clock object that regulates the "delta time" variable
        :param frame_rate: an optional argument that sets a requested frame rate for the update cycle

        Practically speaking, a clock object and a reasonable frame_rate argument should always
        be provided when not running in a diagnostic / testing capacity. Knowledge of your output
        backend may be required, by default ZSquirrel supports the use of Pygame's Clock object
        """
        self.environment = environment

        self.clock = clock
        self.screen = screen
        self.frame_rate = frame_rate

    # setters

    def set_environment(self, environment):
        self.environment = environment

    # update methods

    def update_game(self):
        self.update_environment()
        self.draw_environment()

    def update_environment(self):
        self.environment.update()

    def draw_environment(self):
        if self.screen:
            self.screen.draw(self.environment)

    # main loop

    def main(self, context=None):
        """
        Called to start the game.

        Note that the clock.tick() method is assumed to return a float
        that represents the number of seconds since the last update.
        """
        while True:
            if self.clock:
                dt = self.clock.tick(self.frame_rate) / 1000
                # print(dt)

                if context:
                    context.update_dt(dt)

            self.update_game()


class Screen:
    """
    The Screen class helps define the interface for interacting
    with a graphical backend. The methods listed here should be
    extended to preserve proper behavior, but the way they are used
    will be dependent upon the specifics of the backend platform.

    See implementation of the "PygameScreen" subclass below for more
    specific examples.
    """
    def refresh(self):
        """
        This method provides a hook to implement general backend
        update routines. See PygameScreen for an example
        """
        pass

    def render_graphics(self, *args):
        """
        This method should define the procedure for generally
        'rendering' graphical arguments as provided by the game's
        Environment object

        :param args: A list of arguments to be used as parameters
            for rendering
        """
        pass

    def draw(self, environment):
        """
        The main 'update' routine for the Screen object. This method
        should implement any general updating requested by the backend
        in the 'refresh method' and then pass the graphical arguments
        provided by the environment to it's 'render_graphics' method,
        one by one.

        NOTE that environment.get_arguments() should return a list of
        tuples of arguments, such that they can be expanded by the
        "*args" indefinite parameters syntax used in this method

        :param environment: the Game.environment attribute
        """
        self.refresh()

        for args in environment.get_graphics():
            self.render_graphics(*args)


class PygameScreen(Screen):
    def __init__(self, size):
        self._screen = pygame.display.set_mode(size)

    def refresh(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        pygame.display.flip()
        self._screen.fill((0, 0, 0))

    def render_graphics(self, obj, *args):
        if type(obj) is Image:
            position = args[0]
            self.render_image(obj.pygame_surface, position)

        else:
            self.render_geometry(self, obj, *args)

    def render_image(self, image, position):
        self._screen.blit(image, position)

    def render_geometry(self, method, *args):
        if method == "rect":
            args = list(args)
            args[1] = args[1].pygame_rect

            pygame.draw.rect(self, *args)

        if method == "line":
            pygame.draw.line(self, *args)

        if method == "circle":
            pygame.draw.circle(self, *args)
