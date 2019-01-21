from game import Screen, Game
import constants as con

PLAYER = "Player"

# Here's a little demo where we'll build a kind of Mock Screen and Environment subclass
# to show exactly how they interact in concert with the Game object. It also gives a bit
# of an example of how the Screen's draw() method expects the Environment's get_graphics()
# method to operate.
#
# For this example our "graphical back end" is essentially going to just be printing to the
# standard out.


class TextScreen(Screen):
    def __init__(self, size):
        self.size = size
        self._screen = ""

    def make_screen(self):
        w, h = self.size
        line = "." * w + "\n"

        return line * h

    def refresh(self):
        self._screen = self.make_screen()

    def render_graphics(self, char, x, y):
        w, h = self.size

        x %= w
        y %= h

        i = (y * (w + 1)) + x

        scr = list(self._screen)
        scr[i] = char
        self._screen = "".join(scr)

    def draw(self, environment):
        super(TextScreen, self).draw(environment)

        print(self._screen)


class TextEnv:
    def __init__(self, name, *entities):
        self.name = name
        self._entities = entities
        self.updated = False

    @property
    def entities(self):
        return self._entities

    @entities.setter
    def entities(self, val):
        self._entities = val

    def get_input(self):
        text = input("> ")

        if "q" in text:
            exit()

        x, y = 0, 0
        up = "u" in text
        down = "d" in text
        left = "l" in text
        right = "r" in text

        if up:
            y -= 1
        if down:
            y += 1
        if left:
            x -= 1
        if right:
            x += 1

        self.move_player(x, y)

    def move_player(self, dx, dy):
        for e in self.entities:
            if e[con.NAME] == PLAYER:
                x, y = e[con.POSITION]
                x += dx
                y += dy
                e[con.POSITION] = x, y

    def get_graphics(self):
        args = []

        for entity in self.entities:
            x, y = entity[con.POSITION]
            char = entity[con.NAME][0]

            args.append((char, x, y))

        return args

    def update(self):
        if self.updated:
            self.get_input()
        self.updated = True


if __name__ == "demos.game_demo":
    ts = TextScreen((50, 12))

    env = TextEnv(
        con.ENVIRONMENT,
        {con.NAME: PLAYER, con.POSITION: (1, 1)}
    )

    Game(ts, env).main()
