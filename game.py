from sys import exit


class Game:
    def __init__(self, screen=None, clock=None, frame_rate=1):
        self.environment = None
        self.context = None
        self.clock = clock
        self.screen = screen
        self.frame_rate = frame_rate

    def update_game(self):
        self.update_environment()
        self.draw_environment()

    def update_environment(self):
        self.environment.update()

    def draw_environment(self):
        if self.screen:
            self.screen.draw(self.environment)

    def main(self):
        while True:
            if self.clock:
                dt = self.clock.tick(self.frame_rate) / 1000
                self.context.model["dt"] = dt
                # print(dt)

            self.update_game()

    @staticmethod
    def quit():
        exit()


class Screen:
    def refresh(self):
        pass

    def render_graphics(self, *args):
        pass

    def draw(self, environment):
        self.refresh()

        for args in environment.get_graphics():
            self.render_graphics(*args)
