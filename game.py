import zsquirrel.constants as con

PRINT_DT = False

# This module defines a basic Game and Screen object that will regulate
# the main input / update / output loop of your ZSquirrel application.
#
# The methods are mostly very simple and establish an extendable protocol
# for interaction between the Environment and Context modules, plus the
# Screen object which essentially exposes a backend to whatever graphical
# output platform you wish to use for a project.
#
# By default, a Pygame / SDL based Screen object is supported.


class Game:
    """
    The Game object is instantiated once per application and
    the Game.main() method is called to implement the main
    input / update / output loop.

    Functionally, the game object merely provides the program loop
    that handles updating the Environment object and updating the
    Context object to store a delta-time variable as needed.

    In practice, the Environment object will typically be created by
    the Context object which will also call the Game.main() loop method,
    passing in itself. For diagnostic purposes, the Game object can be
    passed a Mock of the Environment object and run its Game.main()
    method with no Context.
    """

    def __init__(self, screen=None, environment=None, clock=None, frame_rate=1):
        """
        :param screen: a Screen object that implements the graphical backend
        :param environment: an Environment object that extends an update() and get_graphics() method
        :param clock: an optional Clock object that regulates the "delta time" variable
        :param frame_rate: an optional argument that sets a requested frame rate for the update cycle

        Practically speaking, a clock object and a reasonable frame_rate argument should always
        be provided when not running in a diagnostic / testing capacity. Knowledge of your output
        backend may be required, by default ZSquirrel supports the use of Pygame's Clock object
        """
        self.screen = screen
        self.environment = environment
        self.clock = clock
        self.frame_rate = frame_rate

    # setters

    def set_environment(self, environment):
        """
        A setter that is typically called by the Context object to load a new
        update environment for the game.

        :param environment: a new Environment object
        """
        self.environment = environment

    # update methods

    def update_game(self):
        """
        The main update procedure called once per loop of the main() method.
        """
        self.update_environment()
        self.draw_environment()

    def update_environment(self):
        """
        Calls the Environment object's update() method. This method call is
        isolated for the purpose of overwriting in a diagnostic setting.
        """
        self.environment.update()

    def draw_environment(self):
        """
        Calls the Screen object's draw() method while passing the Environment
        object as an argument. The Screen object will not be called if it is
        not None, for diagnostic purposes.
        """
        if self.screen:
            self.screen.draw(self.environment)

    # main loop

    def main(self, context=None):
        """
        Called to start the game.

        Note that the clock.tick() method is assumed to return a float
        that represents the number of seconds since the last update.

        The PRINT_DT variable can be set to True to allow the dt variable
        to be passes to the standard out.
        """
        if not self.environment:
            raise RuntimeError("Game.environment has not been set.")

        while True:
            if self.clock:
                dt = self.clock.tick(self.frame_rate) / 1000

                if PRINT_DT:
                    print(dt)

                if context:
                    context.set_value(con.DT, dt)

            self.update_game()


class Screen:
    """
    The Screen class helps define the interface for interacting
    with a graphical backend. The methods listed here should be
    extended to preserve proper behavior, but the way they are used
    will be dependent upon the specifics of the backend platform.

    See implementation of the "PygameScreen" subclass for more
    specific examples.
    """
    def __init__(self, size):
        """
        The Screen.size attribute defines the size of the display surface in pixels

        :param size: (int, int)
        """
        self.size = size

    def refresh(self):
        """
        This method provides a hook to implement general backend
        update routines. See PygameScreen for an example
        """
        pass

    def render_item(self, *args):
        """
        This method should define the procedure for generally
        'rendering' graphical arguments as provided by the game's
        Environment object

        :param args: A collection of arguments to be used as parameters
            for the backend rendering method
        """
        pass

    def draw(self, environment):
        """
        The main 'update' routine for the Screen object. This object
        should implement any general updating requested by the backend
        in the refresh() method and then pass the graphical arguments
        provided by the environment to its render_graphics() method,
        one by one.

        NOTE that environment.get_graphics() should return a list of
        tuples of arguments, such that they can be expanded by the
        "*args" indefinite parameters syntax used in this method

        :param environment: the Game.environment attribute
        """
        self.refresh()

        for item in environment.get_graphics():
            self.render_item(*item)
