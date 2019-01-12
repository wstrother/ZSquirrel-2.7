from game import Screen, Game


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
        if scr[i] == "\n":
            print(x, y)

        scr[i] = char
        self._screen = "".join(scr)

    def draw(self, environment):
        super(TextScreen, self).draw(environment)

        print(self._screen)


class TextEnv:
    def __init__(self, *entities):
        self.entities = entities
        self.updated = False

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
            if e["name"] == "Player":
                x, y = e["position"]
                x += dx
                y += dy
                e["position"] = x, y

    def get_graphics(self):
        args = []

        for entity in self.entities:
            x, y = entity["position"]
            char = entity["name"][0]

            args.append((char, x, y))

        return args

    def update(self):
        if self.updated:
            self.get_input()
        self.updated = True


if __name__ == "__main__":
    ts = TextScreen((50, 12))

    env = TextEnv(
        {"name": "Player", "position": (1, 1)}
    )

    Game(env, ts).main()
