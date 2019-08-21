from zsquirrel.utils.meters import Timer, Clock
import zsquirrel.constants as con


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
        self.entity = entity
        self.paused = []
        self.listeners = []

    def __repr__(self):
        return "{} for {}".format(
            self.__class__.__name__,
            self.entity
        )

    def queue_event(self, *events):
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

        name = event[con.NAME]
        duration = event.get(con.DURATION, 1)
        timer = Timer(name, duration)
        event[con.TIMER] = timer

        self.entity.clock.add_timers(
            timer
        )

        lerp = event.get(con.LERP, True)

        def handle_event():
            self.handle_event(event)

        if lerp:
            timer.on_tick = handle_event
        else:
            timer.on_done = handle_event

        link = event.get(con.LINK, False)

        if link:
            if lerp:
                def queue_link():
                    self.queue_event(link)

            else:
                def queue_link():
                    handle_event()
                    self.queue_event(link)

            timer.on_done = queue_link

    def handle_event(self, event):
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
        name = event[con.NAME]

        dead = getattr(self.entity, con.DEAD, False)
        if name not in self.paused and not dead:
            m = getattr(self.entity, con.ON_ + name, False)

            if m and callable(m):
                self.entity.event = event.copy()
                m()

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
            if listener[con.NAME] == event[con.NAME]:
                target = listener[con.TARGET]

                response = listener.get(con.RESPONSE, event.copy())
                response = self.interpret(response)
                response[con.TRIGGER] = event.copy()

                target.queue_event(response)

                if listener.get(con.TEMP, False):
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
            listener[con.TARGET] = listener.get(con.TARGET, self.entity)
            self.listeners.append(listener)

    def remove_listener(self, listener):
        """
        Checks listener dicts in the 'listeners' list against the listener
        argument passed. If the 'name', 'response', and 'target' keys all
        match, the listener is removed from the 'listeners' list

        :param listener: listener dict
        """
        remove = []
        name = listener[con.NAME]

        for check in self.listeners:
            matches = [
                check[con.NAME] == name
            ]

            response = listener[con.RESPONSE]
            if response:
                matches.append(check[con.RESPONSE] == response)

            target = listener.get(con.TARGET, self.entity)
            if target:
                matches.append(check[con.TARGET] == target)

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
            if l[con.NAME] == event_name:
                return True

        return False

    @staticmethod
    def interpret(argument):
        """
        Returns the argument if it is a dict, or else builds a dict
        with default values for either a event or listener.

        Strings with no space are interpreted as an event name and
        returned as a dict with only a 'name' key. Otherwise, the
        string is interpreted as 'listener_name response_name' and
        returned as a listener dict with the 'name' and 'response'
        keys set.

        :param argument: dict or str
        :return: dict
        """
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
        """
        Takes a chain of events and returns them as a single event
        with each subsequent event in the chain recursively stored
        by reference in the event dict's 'link' key

        :param first_event: str or dict
        :param link_events: (str or dict, ...)

        :return: dict
        """
        interp = EventHandler.interpret
        first_event = interp(first_event)

        current_event = first_event
        for link in link_events:
            link = interp(link)
            current_event[con.LINK] = link

            current_event = link

        return first_event


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
        self.event_handler = EventHandler(self)
        self.clock = Clock("Clock for {}".format(self))

        self.event = None
        self.handle_event = self.event_handler.handle_event
        self.queue_event = self.event_handler.queue_event
        self.chain_events = self.event_handler.chain_events
        self.add_listener = self.event_handler.add_listener
        self.remove_listener = self.event_handler.remove_listener
        self.listening_for = self.event_handler.listening_for
