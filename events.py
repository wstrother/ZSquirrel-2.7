from meters import Timer, Clock
import constants as con


class EventHandler:
    def __init__(self, entity):
        self.entity = entity
        self.paused = []
        self.listeners = []

    def __repr__(self):
        return "{} for {}".format(
            self.__class__.__name__,
            self.entity
        )

    def queue_event(self, *events):
        if len(events) > 1:
            event = self.chain_events(*events)
        else:
            event = self.interpret(events[0])

        name = event[con.NAME]
        duration = event.get(con.DURATION, 1)

        timer = Timer(name, duration)
        event[con.TIMER] = timer
        self.entity.clock.add_timers(
            timer)

        lerp = event.get(con.LERP, True)

        def handle_event():
            self.handle_event(event)

        if lerp:
            timer.on_tick = handle_event
        else:
            timer.on_switch_off = handle_event

        link = event.get(con.LINK, False)

        if link:
            if lerp:
                def queue_link():
                    self.queue_event(link)

            else:
                def queue_link():
                    handle_event()
                    self.queue_event(link)

            timer.on_switch_off = queue_link

    def handle_event(self, event):
        event = self.interpret(event)
        self.check_event_methods(event)
        self.check_listeners(event)

    def check_event_methods(self, event):
        name = event[con.NAME]

        if name not in self.paused:
            m = getattr(self.entity, "on_" + name, False)
            if m and callable(m):
                self.entity.event = event.copy()
                m()

    def check_listeners(self, event):
        for listener in self.listeners:
            if listener[con.NAME] == event[con.NAME]:
                target = listener[con.TARGET]

                response = listener.get(con.RESPONSE, event.copy())
                response = self.interpret(response)
                response[con.TRIGGER] = event.copy()

                target.handle_event(response)

                if listener.get(con.TEMP, False):
                    self.remove_listener(listener)

    def add_listener(self, *listeners):
        for listener in listeners:
            listener = self.interpret(listener)
            listener[con.TARGET] = listener.get(con.TARGET, self.entity)
            self.listeners.append(listener)

    def remove_listener(self, listener):
        remove = []
        name = listener[con.NAME]

        for l in self.listeners:
            matches = [
                l[con.NAME] == name
            ]

            response = listener.get(con.RESPONSE, False)
            if response:
                matches.append(l[con.RESPONSE] == response)

            target = listener.get(con.TARGET, False)
            if target:
                matches.append(l[con.TARGET] == target)

            if all(matches):
                remove.append(l)

        self.listeners = [l for l in self.listeners if l not in remove]

    def listening_for(self, event_name):
        for l in self.listeners:
            if l[con.NAME] == event_name:
                return True

        return False

    @staticmethod
    def interpret(argument):
        if type(argument) is dict:
            return argument

        if type(argument) is str:
            if " " in argument:
                name, response = argument.split(" ")

                return {con.NAME: name, con.RESPONSE: response}

            else:
                return {con.NAME: argument}

    @staticmethod
    def chain_events(first_event, *link_events):
        interp = EventHandler.interpret
        first_event = interp(first_event)

        current_event = first_event
        for link in link_events:
            link = interp(link)
            current_event[con.LINK] = link

            current_event = link

        return first_event

    @staticmethod
    def make_event(name, **kwargs):
        event = kwargs.copy()
        event[con.NAME] = name

        return event


class EventHandlerObj:
    def __init__(self):
        self.event_handler = EventHandler(self)
        self.clock = Clock("Clock for {}".format(self))

        self.event = None
        self.handle_event = self.event_handler.handle_event
        self.queue_event = self.event_handler.queue_event
        self.chain_events = self.event_handler.chain_events
        self.add_listener = self.event_handler.add_listener
        self.remove_listener = self.event_handler.remove_listener
        self.listening_for = self.event_handler.listening_for
