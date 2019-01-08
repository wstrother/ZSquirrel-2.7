from zs2.meters import Timer, Clock


class EventHandler:
    # event keys
    NAME = "name"
    DURATION = "duration"
    TIMER = "timer"
    LERP = "lerp"
    LINK = "link"

    # listener keys
    TARGET = "target"
    RESPONSE = "response"
    TEMP = "temp"
    TRIGGER = "trigger"

    def __init__(self, entity):
        self.entity = entity
        self.paused = []
        self.listeners = []

    def __repr__(self):
        e = repr(self.entity)

        return "EventHandler for {}".format(e)

    def queue_event(self, *events):
        if len(events) > 1:
            event = self.chain_events(*events)
        else:
            event = self.interpret(events[0])

        name = event[EventHandler.NAME]
        duration = event.get(EventHandler.DURATION, 1)

        timer = Timer(name, duration)
        event[EventHandler.TIMER] = timer
        self.entity.clock.add_timers(
            timer)

        lerp = event.get(EventHandler.LERP, True)

        def handle_event():
            self.handle_event(event)

        if lerp:
            timer.on_tick = handle_event
        else:
            timer.on_switch_off = handle_event

        link = event.get(EventHandler.LINK, False)

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
        name = event[EventHandler.NAME]

        if name not in self.paused:
            m = getattr(self.entity, "on_" + name, False)
            if m and callable(m):
                self.entity.event = event.copy()
                m()

    def check_listeners(self, event):
        for listener in self.listeners:
            if listener[EventHandler.NAME] == event[EventHandler.NAME]:
                target = listener[EventHandler.TARGET]

                response = listener.get(EventHandler.RESPONSE, event.copy())
                response = self.interpret(response)
                response[EventHandler.TRIGGER] = event.copy()

                target.handle_event(response)

                if listener.get(EventHandler.TEMP, False):
                    self.remove_listener(listener)

    def add_listener(self, *listeners):
        for l in listeners:
            l = self.interpret(l)
            l[EventHandler.TARGET] = l.get(EventHandler.TARGET, self.entity)
            self.listeners.append(l)

    def remove_listener(self, listener):
        remove = []
        name = listener[EventHandler.NAME]

        for l in self.listeners:
            matches = [
                l[EventHandler.NAME] == name
            ]

            response = listener.get(EventHandler.RESPONSE, False)
            if response:
                matches.append(l[EventHandler.RESPONSE] == response)

            target = listener.get(EventHandler.TARGET, False)
            if target:
                matches.append(l[EventHandler.TARGET] == target)

            if all(matches):
                remove.append(l)

        self.listeners = [l for l in self.listeners if l not in remove]

    def listening_for(self, event_name):
        for l in self.listeners:
            if l[EventHandler.NAME] == event_name:
                return True

        return False

    @staticmethod
    def interpret(argument):
        if type(argument) is dict:
            return argument

        if type(argument) is str:
            if " " in argument:
                name, response = argument.split(" ")

                return {EventHandler.NAME: name, EventHandler.RESPONSE: response}

            else:
                return {EventHandler.NAME: argument}

    @staticmethod
    def chain_events(first_event, *link_events):
        interp = EventHandler.interpret
        first_event = interp(first_event)

        current_event = first_event
        for link in link_events:
            link = interp(link)
            current_event[EventHandler.LINK] = link

            current_event = link

        return first_event

    @staticmethod
    def make_event(name, **kwargs):
        event = kwargs.copy()
        event[EventHandler.NAME] = name

        return event


class EventHandlerInterface:
    def __init__(self, name):
        self.name = name

        self.event_handler = EventHandler(self)
        self.event = None
        self.handle_event = self.event_handler.handle_event
        self.queue_event = self.event_handler.queue_event
        self.chain_events = self.event_handler.chain_events
        self.add_listener = self.event_handler.add_listener
        self.remove_listener = self.event_handler.remove_listener
        self.listening_for = self.event_handler.listening_for

        self.clock = Clock("{} event handler clock".format(name))

        if type(self) is EventHandlerInterface:
            err = "{} is an abstract/interface class and should not be instantiated"
            raise RuntimeError(
                err.format(self.__class__.__name__)
            )
