from zs_utils.meters import Timer, Clock

ON = "on_"
NAME = "name"
DURATION = "duration"
RESPONSE = "response"
TIMER = "timer"
LINK = "link"
DONE = "done"
LERP = "lerp"
TARGET = "target"
TEMP = "temp"
TRIGGER = "trigger"


class EventHandler:
    def __init__(self, entity):
        """
        Some Entity subclass such as Sprite or Layer is passed so that
        event timers can be added to its clock.
        A list of 'paused' strings defines names where the event method
        will not be called even when that event is heard.
        A list of 'listener' dicts defines new events that will propagate
        based on a certain event being handled.
        :param entity: Entity subclass object
        """
        self.paused = []
        self.listeners = []

        self.entity = entity
        self.clock = Clock("{} - EventHandler Clock".format(entity))

    def __repr__(self):
        return "{} for {}".format(
            self.__class__.__name__,
            self.entity
        )

    def queue(self, *events):
        """
        Links a chain of events together such that they will be handled in
        sequence, one after the other.
        The initial event, on being queued, is constructed as a Timer object and
        added to the entity's Clock. If the event's 'lerp' key is set, the
        handle_event() method will be called for this event on each frame the timer
        is ticked, otherwise handle_event() is called in the timer's 'on_done'
        method.
        Additional events are recursively stored by reference in each preceding
        event's 'link' key, which will cause this method to define an additional
        'queue_link()' method which calls 'queue_event' with the next event in
        the chain.
        :param events: (event, ...)
        """
        if len(events) > 1:
            event = self.chain_events(*events)
        else:
            event = self.interpret(events[0])

        timer = Timer(
            event[NAME],
            event.get(DURATION, 1),
            temp=event.get(TEMP, True)
        )
        event[TIMER] = timer
        self.clock.add_timers(timer)

        lerp = event.get(LERP, False)
        if lerp:
            timer.on_tick = lambda: self.handle(event)
        else:
            timer.on_done = lambda: self.handle(event)

    def handle(self, event):
        """
        The event argument passed to this method is initially
        passed to the 'interpret' method so that it can either be
        an event dict, or a string event name which will be given
        default key/values.
        It's then passed to 'check_event_methods()' as well as
        'check_listeners()'
        :param event: event dict, or str
        """
        event = self.interpret(event)
        self.check_event_methods(event)
        self.check_listeners(event)

        done = True
        if TIMER in event:
            timer = event[TIMER]
            done = timer.is_off()

        link = event.get(LINK)
        if done and link:
            self.queue(link)

    def pause_event(self, name):
        """
        Adds the event name to the 'paused' list
        :param name: str
        """
        if name not in self.paused:
            self.paused.append(name)

    def unpause_event(self, name):
        """
        Removes the event name from the 'paused' list
        :param name: str
        """
        if name in self.paused:
            self.paused.pop(
                self.paused.index(name)
            )

    def check_event_methods(self, event):
        """
        Checks the event dict's 'name' key against the methods of the
        Entity object. If the Entity has a method by with a name
        following the format of 'on_event_name' it is called and a
        copy of the event dict is assigned to the Entity's 'event'
        attribute.
        If the event's name is in the 'paused' list then the event
        method will not be called.
        :param event: event dict
        """
        name = event[NAME]

        if name not in self.paused:
            m = getattr(self.entity, ON + name, False)

            if m:
                if not callable(m):
                    raise RuntimeError("{} is not a callable method".format(m))
                try:
                    m(event)
                except TypeError:
                    try:
                        m()
                    except TypeError:
                        raise RuntimeError("{} should take either 1 (event) or 0 arguments".format(m))

    def check_listeners(self, event):
        """
        Checks listener dicts in the 'listeners' list for those
        that match the event name.
        If there is a match, the Entity object specified by the
        listener's 'target' key is then made to handle the event
        specified by the 'response' key. Additionally, a copy of
        the event dict is set to the response event's 'trigger' key.
        If the listener's 'temp' key is set to True, the listener is
        removed from the 'listeners' list.
        :param event: event dict
        """
        for listener in self.listeners:
            if listener[NAME] == event[NAME]:
                target = listener[TARGET]

                response = listener.get(RESPONSE, event.copy())
                response = self.interpret(response)
                response[TRIGGER] = event.copy()

                target.event.handle(response)

                if listener.get(TEMP):
                    self.remove_listener(listener)

    def add_listener(self, *listeners):
        """
        Adds listeners to the 'listeners' list. For each argument passed,
        the 'interpret()' method is called, thus the listener can be expressed
        as a listener dict, or a str of the format 'listener_name response_name'
        which will produce a listener dict with only the 'name' and 'response'
        keys defined. The 'target' key will then be set to the EventHandler
        object's Entity by default.
        :param listeners: (listener dict or str, ...)
        """
        for listener in listeners:
            listener = self.interpret(listener)
            if TARGET not in listener:
                listener[TARGET] = self.entity
            self.listeners.append(listener)

    def remove_listener(self, listener):
        """
        Checks listener dicts in the 'listeners' list against the listener
        argument passed. If the 'name', 'response', and 'target' keys all
        match, the listener is removed from the 'listeners' list
        If the listener argument passed does not include values for the
        'target' or 'response' key, those keys and values will not be
        checked and multiple listeners can be removed at once
        :param listener: listener dict or str
        """
        remove = []
        listener = self.interpret(listener)
        name = listener[NAME]

        for check in self.listeners:
            matches = [
                check[NAME] == name
            ]

            response = listener.get(RESPONSE)
            if response:
                matches.append(check[RESPONSE] == response)

            target = listener.get(TARGET)
            if target:
                matches.append(check[TARGET] == target)

            if all(matches):
                remove.append(check)

        self.listeners = [l for l in self.listeners if l not in remove]

    def listening_for(self, event_name):
        """
        Returns True if the event_name is being listened for by any
        listener in 'listeners' list
        :param event_name: str
        :return: bool
        """
        for l in self.listeners:
            if l[NAME] == event_name:
                return True

        return False

    @staticmethod
    def interpret(arg):
        """
        Returns the argument if it is a dict, or else builds a dict
        with default values for either a event or listener.
        Strings with no space are interpreted as an event name and
        returned as a dict with only a 'name' key. Otherwise, the
        string is interpreted as 'listener_name response_name' and
        returned as a listener dict with the 'name' and 'response'
        keys set.
        :param arg: dict or str
        :return: dict
        """
        if type(arg) is dict:
            if NAME not in arg:
                raise ValueError("Event passed needs a '{}' key/value".format(NAME))
            return arg

        elif type(arg) is str:
            if " " in arg:
                name, response = arg.split(" ")

                return {NAME: name, RESPONSE: response}

            else:
                return {NAME: arg}

        else:
            raise ValueError("Object passed as event cannot be interpreted correctly: {}".format(arg))

    @staticmethod
    def chain_events(first, *links):
        """
        Takes a chain of events and returns them as a single event
        with each subsequent event in the chain recursively stored
        by reference in the event dict's 'link' key
        :param first: str or dict
        :param links: (str or dict, ...)
        :return: dict
        """
        interp = EventHandler.interpret
        first = interp(first)

        current = first
        for link in links:
            link = interp(link)
            current[LINK] = link
            current = link

        return first


class EventHandlerObj:
    """
    The EventHandlerObj class is a super class for the Entity class which
    extends the functionality of the EventHandler class. The 'event_handler'
    attribute is defined as a composed EventHandler and it's public facing
    methods are then aliased as attributes of the EventHandlerObj instance.
    The EventHandlerObj instance is also given an 'event' attribute which
    defines the event dict that is currently being handled by the event_handler.
    """
    def __init__(self):
        self.event = EventHandler(self)
