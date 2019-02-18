import constants as con
from events import EventHandlerObj
from geometry import add_points
from controller_io import ControllerIO


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

    def add_to_list(self, list_name, *items):
        lis = getattr(self, list_name)

        for item in [i for i in items if i not in lis]:
            lis.append(item)

        setattr(self, list_name, lis)

    def move(self, dx, dy, v=1):
        x, y = self.position
        dx *= v
        dy *= v
        self.set_position(x + dx, y + dy)

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

    def on_spawn(self):
        self.spawned = True

    def on_death(self):
        self.dead = True


class Layer(Entity):
    def __init__(self, name):
        super(Layer, self).__init__(name)
        self.sub_layers = []
        self.groups = []
        self.controllers = []
        self.parent_layer = None

        self.update_methods += [
            self.update_sprites,
            self.update_sub_layers,
            self.update_controllers
        ]

    def set_parent_layer(self, layer):
        layer.add_to_list(con.SUB_LAYERS, self)
        self.parent_layer = layer.name

    def set_groups(self, *groups):
        add = []
        for g in groups:
            if type(g) is str:
                g = Group(g)
            add.append(g)

        self.add_to_list(con.GROUPS, *add)

    def get_graphics(self, position=None):
        if not position:
            position = self.position

        args = []

        if self.visible:
            if self.graphics:
                args += self.graphics.get_graphics(position)

            for l in self.sub_layers:
                args += l.get_graphics(
                    add_points(position, l.position)
                )

            for sprite in self.get_sprites():
                if sprite.graphics and sprite.visible:
                    args += sprite.graphics.get_graphics(position)

        return args

    def get_sprites(self):
        sprites = []

        for g in self.groups:
            sprites += [s for s in g if isinstance(s, Sprite)]

        return sprites

    def update_sprites(self):
        for s in self.get_sprites():
                s.update()

    def update_sub_layers(self):
        for l in self.sub_layers:
            l.update()

    def set_controller(self, arg):
        if type(arg) is str:
            cont = ControllerIO.load_controller(arg)

        else:
            name = list(arg.keys())[0]
            cont = ControllerIO.make_controller(
                name, arg[name]
            )

        self.add_to_list(
            con.CONTROLLERS, cont
        )

    def set_controllers(self, *controllers):
        for c in controllers:
            self.set_controller(c)

    def update_controllers(self):
        for c in self.controllers:
            c.update()

    def on_death(self):
        for s in self.get_sprites():
            s.handle_event(con.DEATH)

        super(Layer, self).on_death()


class Sprite(Entity):
    def __init__(self, name):
        super(Sprite, self).__init__(name)

        self.group = None
        self.controller = None

        self.queue_event(con.SPAWN)

    def set_group(self, group):
        self.group = group
        group.add_member(self)

    def set_controller(self, layer, index):
        self.controller = layer.controllers[index]


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
