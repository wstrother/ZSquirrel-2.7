import constants as con
from events import EventHandlerObj


class EntityMetaclass(type):
    def __call__(cls, *args, **kwargs):
        new = type.__call__(cls, *args, **kwargs)
        new.initialized = True

        return new


class Entity(EventHandlerObj, metaclass=EntityMetaclass):
    def __init__(self, name):
        super(Entity, self).__init__()

        self.initialized = False
        self.zs_data = {}

        self.name = name
        self.size = 0, 0
        self.position = 0, 0

        self.spawned = False
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
        super(Entity, self).__setattr__(key, value)

        if hasattr(self, "set_" + key) and self.initialized:
            if not (key == con.PARENT_LAYER and value == con.ENVIRONMENT):
                self.log_data(key, value)

    def log_data(self, key, value):
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

    def set_size(self, w, h):
        self.size = w, h

    def set_position(self, x, y):
        self.position = x, y

    def set_visible(self, value):
        self.visible = value

    def set_paused(self, value):
        self.paused = value

    def update(self):
        if not self.paused:
            for m in self.update_methods:
                m()


class Group:
    def __init__(self, name):
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
