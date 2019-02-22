import constants as con
from events import EventHandlerObj
from geometry import add_points


class EntityMetaclass(type):
    """
    The EntityMetaclass ensures that the 'initialized' flag is set to True on
    any Entity subclass instance after it's __init__ method has been executed.
    """
    def __call__(cls, *args, **kwargs):
        new = type.__call__(cls, *args, **kwargs)
        new.initialized = True

        return new


class Entity(EventHandlerObj, metaclass=EntityMetaclass):
    def __init__(self, name):
        """
        The __init__ method for the Entity class ensures all entities have
        a 'zs_data' attribute storing a dict that records hashable keys
        and values for each setter method called during the Context class's
        populate() method. These values will only be updated to the dict
        after the __init__ method has executed and the 'initialized' flag
        is set to True by the metaclass.

        All entities take a name value and have a 'size' and 'position' attribute
        defined by default as the tuple (0, 0). A number of flags are also set:
            spawned: defines whether an entity has started
                updating and handling events
            dead: defines whether an entity is marked for
                removal from the environment
            paused: defines whether an entity should not call
                the update() method each frame
            visible: defines whether the containing layer passes
                the entities graphics to its get_graphics() method

        Entities also have an attribute 'graphics' that can define a Graphics
        object with a method for providing graphics arguments to the containing
        layer's get_graphics() method.

        A list of 'update_methods' is iterated during the update() method and
        by default contains the Clock.tick() method on the clock provided by the
        EventHandlerObj parent class.

        By default, the __init__ method also queues the 'spawn' event.

        :param name: str
        """
        self.name = name

        super(Entity, self).__init__()

        self.initialized = False
        self.zs_data = {}

        self.size = 0, 0
        self.position = 0, 0

        self.spawned = False
        self.dead = False
        self.paused = False
        self.visible = True

        self.graphics = None

        self.update_methods = [
            self.clock.tick
        ]

        self.queue_event(con.SPAWN)

    def __repr__(self):
        c = self.__class__.__name__
        n = self.name

        return "<{}: {}>".format(c, n)

    def __setattr__(self, key, value):
        """
        This method ensures that, once the 'initialized' flag has been set to
        True, any attribute (such as 'size' or 'position') with a setter method
        has it's value changes logged in the 'zs_data' dict. I.E. values set
        during the __init__ method will not be recorded, but any changes made
        in the Context.populate() or changes made at runtime by update methods
        and event handling will be stored in the 'zs_data' dict.

        :param key: str
        :param value: hashable obj or Entity or Group
        """
        super(Entity, self).__setattr__(key, value)

        if hasattr(self, "set_" + key) and self.initialized:
            if not (key == con.PARENT_LAYER and value == con.ENVIRONMENT):
                self.log_data(key, value)

    def log_data(self, key, value):
        """
        This method helps ensure that any value passed to each setter
        method is stored in hashable form in the 'zs_data' dict.

        Any Entity subclass instance or Group object will be stored as
        it's 'name' str.

        :param key: str
        :param value: hashable obj or Entity or Group
        :return:
        """
        def get_value(v):
            if type(v) is list:
                return [get_value(item) for item in v]

            else:
                if isinstance(v, (Entity, Group)):
                    return v.name
                else:
                    return v

        value = get_value(value)

        self.zs_data[key] = value

    def add_to_list(self, list_name, *items):
        """
        This method should be used by setter methods that append items
        to a list attribute to ensure that the __setattr_ method is
        called and any changes are logged.

        :param list_name: str
        :param items: (obj, ...)
        """
        lis = getattr(self, list_name)

        for item in [i for i in items if i not in lis]:
            lis.append(item)

        setattr(self, list_name, lis)

    def move(self, dx, dy, v=1):
        """
        Changes the entity's position by a specified amount.

        And optional value 'v' serves as an interpolation factor.
        I.E. a movement event with a duration of n frames will pass
        a 'v' of 1/n each frame.

        :param dx: int or float
        :param dy: int or float
        :param v: int or float
        """
        x, y = self.position
        dx *= v
        dy *= v
        self.set_position(x + dx, y + dy)

    def set_size(self, w, h):
        """
        Default setter for 'size' attribute.

        :param w: int or float
        :param h: int or float
        """
        self.size = w, h

    def set_position(self, x, y):
        """
        Default setter for 'position' attribute.

        :param x: int or float
        :param y: int or float
        """
        self.position = x, y

    def set_visible(self, value):
        """
        Default setter for 'visible' flag

        :param value: bool
        """
        self.visible = value

    def set_paused(self, value):
        """
        Default setter for 'paused' flag

        :param value: bool
        """
        self.paused = value

    def update(self):
        """
        For any entity where the 'paused' flag is not set to True,
        this method iterates over every method listed in 'update_methods'
        and calls them once per frame.
        """
        if not self.paused:
            for m in self.update_methods:
                m()

    def get_graphics(self, position=None):
        """
        This method returns a list of tuples that each represent a set of
        arguments for some back end graphical rendering method. If an Entity
        has a 'graphics' attribute set to None or it's 'visible' flag is
        False, it will return an empty list.

        An optional 'position' argument can be passed representing the
        location where the graphics should be rendered, otherwise the
        Entity's 'position' attribute will be used.

        :param position: None or (int or tuple, int or tuple)

        :return: list, [(arg, ...), ...]
        """
        if not position:
            position = self.position

        if self.graphics and self.visible:
            return self.graphics.get_graphics(position)

        else:
            return []

    def on_spawn(self):
        """
        Event method for 'spawn' event, which is queued by default whenever
        an entity object is initialized
        """
        self.spawned = True

    def on_death(self):
        """
        Event method for 'death' event, which should be queued when an entity
        is set to be removed from the game environment.
        """
        self.dead = True


class Layer(Entity):
    def __init__(self, name):
        """
        Layer entities exist in a hierarchy defined by a 'parent_layer'
        attribute and a list of 'sub_layers'.

        They also have a list of 'groups' containing Group objects which
        define lists of Sprites to be updated, as well as a 'controllers'
        list for Controller objects that can be used to get user input for
        controlling Sprite objects.

        The additional update methods 'update_sprites()', 'update_sub_layers()',
        and 'update_controllers' are added to the 'update_methods' list.

        :param name: str
        """
        super(Layer, self).__init__(name)
        self.parent_layer = None
        self.sub_layers = []

        self.groups = []
        self.controllers = []

        self.update_methods += [
            self.update_sprites,
            self.update_sub_layers,
            self.update_controllers
        ]

    def set_parent_layer(self, layer):
        """
        Sets a parent layer for this layer in the layer hierarchy

        :param layer: Layer object
        """
        layer.add_to_list(con.SUB_LAYERS, self)
        self.parent_layer = layer.name

    def set_groups(self, *groups):
        """
        Adds Group objects to be updated by this layer

        :param groups: (Group object, ...)
        """
        add = []
        for g in groups:
            if type(g) is str:
                g = Group(g)
            add.append(g)

        self.add_to_list(con.GROUPS, *add)

    def get_graphics(self, position=None):
        """
        This method provides a list of tuples of arguments to be used in
        the Screen object's 'draw()' method where each tuple in the list is
        effectively a set of arguments for the 'render_graphics()' method.

        An optional 'position' argument can be passed as a tuple of numbers
        representing a relative offset for any position arguments added to
        the argument tuples list. If no 'position' argument is passed then the
        layer's 'position' attribute is used as the value.

        The Layer's graphics are added to the argument tuple list, then any
        Layer in the 'sub_layers' list is added, with the position passed
        to it's 'get_graphics' method added to the current position value.

        Any sprites returned by the 'get_sprites()' method will also have
        their graphics arguments added to the list.

        :param position: None or (int or float, int or float)

        :return: list
        """
        if not position:
            position = self.position

        args = []

        if self.visible:
            args += super(Layer, self).get_graphics(position=position)

            for l in self.sub_layers:
                args += l.get_graphics(
                    position=add_points(position, l.position)
                )

            for sprite in self.get_sprites():
                args += sprite.get_graphics(position=position)

        return args

    def get_sprites(self):
        """
        Returns a list of all sprites in each Group in 'groups' list

        :return: list
        """
        sprites = []

        for g in self.groups:
            sprites += [s for s in g if isinstance(s, Sprite)]

        return sprites

    @staticmethod
    def remove_sprite(sprite):
        """
        Removes a sprite from its current group and sets the 'group' attribute
        to None

        :param sprite: Sprite object
        """
        g = sprite.group
        sprite.group = None
        g.remove_member(sprite)

    def update_sprites(self):
        """
        Calls the 'update()' method for each Sprite returned by 'get_sprites()' if
        its 'pause' flag is not set to True.

        Calls 'remove_sprite()' on any sprite with the 'dead' flag set to True
        """
        for s in self.get_sprites():
            if s.dead:
                self.remove_sprite(s)

            elif not s.paused:
                s.update()

    def update_sub_layers(self):
        """
        Calls the 'update()' method for each layer in 'sub_layers' list
        """
        for l in self.sub_layers:
            l.update()

    def set_controller(self, controller):
        """
        Adds a Controller object to the 'controllers' list.

        :param controller: Controller object
        """
        self.add_to_list(
            con.CONTROLLERS, controller
        )

    def set_controllers(self, *controllers):
        """
        Passes multiple arguments to 'set_controller()' method

        :param controllers: (Controller, ...)
        """
        for c in controllers:
            self.set_controller(c)

    def update_controllers(self):
        """
        Calls 'update()' on each Controller in 'controllers' list
        """
        for c in self.controllers:
            c.update()

    def on_death(self):
        """
        Passes the 'death' event to each Sprite object returned by
        'get_sprites()' method, before calling the superclass 'on_death'
        event method
        """
        for s in self.get_sprites():
            s.handle_event(con.DEATH)

        super(Layer, self).on_death()


class Sprite(Entity):
    def __init__(self, name):
        """
        each Sprite object has a 'group' attribute referencing the Group
        object whose 'update()' method will handle calling 'update()' for
        this Sprite.

        it also has a 'controller' attribute which references the Controller
        whose input will be used for any relevant update methods of this Sprite.

        :param name: str
        """
        super(Sprite, self).__init__(name)

        self.group = None
        self._controller = None

    @property
    def controller(self):
        if self._controller:
            layer, i = self._controller

            return layer.controllers[i]

    def set_group(self, group):
        """
        Sets the Group object for this Sprite

        :param group: Group object
        """
        self.group = group
        group.add_member(self)

    def set_controller(self, layer, index):
        """
        Sets the Controller object for this Sprite by referencing the 'controllers'
        list of the Layer object passed to this method. The index defines which
        controller in the list to select

        :param layer: Layer object
        :param index: int
        """
        self._controller = layer, index


class Group:
    """
    Groups are a type of collection like object that organize Sprites
    so that they can be acted on collectively.

    Groups have a name and can be added to a Layer object's 'groups'
    list to ensure that its Sprites are updated each frame.
    """
    def __init__(self, name):
        """
        Defines the Group name and creates a 'sprites' list for that group

        :param name: str
        """
        self.name = name
        self.sprites = []

    def __repr__(self):
        n = self.name
        m = len(self.sprites)

        return "Group: {} ({} members)".format(n, m)

    def empty(self):
        self.sprites = []

    def add_member(self, member):
        if member not in self.sprites:
            self.sprites.append(member)

    def remove_member(self, member):
        for s in self.sprites:
            if member is s:
                self.sprites.pop(
                    self.sprites.index(member)
                )

    def __getitem__(self, key):
        return self.sprites.__getitem__(key)

    def __len__(self):
        return len(self.sprites)

    def __setitem__(self, key, value):
        return self.sprites.__setitem__(key, value)

    def __delitem__(self, key):
        return self.sprites.__delitem__(key)

    def __iter__(self):
        return self.sprites.__iter__()

    def __iadd__(self, other):
        return self.sprites.__iadd__(other)

    def __add__(self, other):
        return self.sprites.__add__(other)

    def __contains__(self, item):
        return self.sprites.__contains__(item)
