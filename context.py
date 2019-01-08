from zs_constants import ZsData, ApiConstants
from zs2.entities import Layer, Sprite
from zs2.resources import load_resource
from zs2.collections import Group

DEFAULT_CLASSES = {
    ZsData.SPRITE: Sprite,
    ZsData.LAYER: Layer
}


class Context:
    def __init__(self, game, class_dict=None, *interfaces):
        self.game = game
        game.context = self

        self._class_dict = class_dict
        self.model = {}
        self.reset_model()

        self.interfaces = []
        for i in interfaces:
            self.interfaces.append(i(self))

    def reset_model(self):
        if "environment" in self.model:
            env = self.model["environment"]
            env.handle_event("death")

        self.model = {
            ZsData.CONTEXT: self,
            ZsData.GAME: self.game
        }

        self.model.update(DEFAULT_CLASSES)

        cd = self._class_dict
        if cd:
            self.model.update(cd)

    def update_model(self, data):
        for item_name in data:
            item = data[item_name]
            for key in item:
                item[key] = self.get_value(item[key])

            self.model[item_name] = item

    def get_value(self, value, sub=None):
        def get(k):
            if k in self.model:
                return self.model[k]

            elif sub and k in sub:
                return sub[k]

            else:
                return k

        if type(value) is list:
            new = []
            for item in value:
                new.append(
                    self.get_value(item, sub=sub)
                )

            return new

        elif type(value) is dict:
            for key in value:
                if value[key] is True:
                    value[key] = self.get_value(
                        key, sub=sub
                    )

                else:
                    value[key] = self.get_value(
                        value[key], sub=sub
                    )

            return value

        else:
            return get(value)

    @staticmethod
    def get_resource(file_name):
        return load_resource(file_name)

    def get_json(self):
        layers = [l.get_json() for l in self.get_layers()]
        sprites = [s.get_json() for s in self.get_sprites()]

        return {
            ZsData.LAYERS: layers,
            ZsData.SPRITES: sprites
        }

    def get_layers(self):
        return [l for l in self.model.values() if isinstance(l, Layer)]

    def get_sprites(self):
        return [s for s in self.model.values() if isinstance(s, Sprite)]

    def load_environment(self, data):
        if type(data) is str:
            data = load_resource(data)

        self.reset_model()
        self.populate(data)
        self.game.environment = self.model[ZsData.ENVIRONMENT]

    def populate(self, data):
        # separate out data sections
        def get_data(item):
            if type(item) is str:
                item = self.get_resource(item)

            if "json" in item:
                file_name = item.pop("json")
                data = self.get_resource(file_name)
                data.update(item)
                item = data

            return item

        layers = []
        if ZsData.LAYERS in data:
            layers = data.pop(ZsData.LAYERS)
        layers = [get_data(l) for l in layers]

        sprites = []
        if ZsData.SPRITES in data:
            sprites = data.pop(ZsData.SPRITES)
        sprites = [get_data(s) for s in sprites]

        entities = layers + sprites

        # create 'empty' entity objects
        self.add_entities(*entities)

        # update data with live object references
        for section in data:
            self.update_model(section)

        #
        # apply data attributes to entities
        for data in entities:
            entity = self.model[data[ZsData.NAME]]
            self.init_attributes(entity, data, init=True)
            self.apply_interfaces(entity, data)

        #
        # structure layer hierarchy
        self.set_layer_order(layers)

    def set_layer_order(self, layers):
        env = self.get_value(ZsData.ENVIRONMENT)

        for l in layers:
            layer = self.model[l[ZsData.NAME]]

            if layer is not env and layer.parent_layer is None:
                layer.set_parent_layer(env)

    def add_group(self, name):
        g = Group(name)
        self.model[name] = g
        print("created new Group:\n{}".format(g))

    def add_entities(self, *entities):
        output = []

        for e in entities:
            name = e[ZsData.NAME]

            cls = self.model[
                e[ZsData.CLASS]
            ]

            if callable(cls):
                entity = cls(name)
                output.append(entity)

                self.model[name] = entity
                print("\nCreated new Entity:\n{}".format(entity))

        return output

    @staticmethod
    def get_init_order(data, order):
        keys = [k for k in data]

        attrs = [
                    o for o in order if o in keys
                ] + [
                    k for k in keys if k not in order
                ]

        return attrs

    def init_attributes(self, entity, data, init=False):
        if init:
            data.update(entity.init_data)

        for attr in self.get_init_order(data, entity.init_order):
            self.set_entity_attribute(entity, attr, data[attr])

    def set_entity_attribute(self, entity, attr, value):
        set_attr = ApiConstants.SET_ + attr

        if hasattr(entity, set_attr):

            value = self.get_value(value)
            if type(value) is list:
                args = value
            else:
                args = [value]

            if attr in (ZsData.GROUPS, ZsData.GROUP):
                new = []
                for arg in args:
                    if type(arg) is str:
                        self.add_group(arg)
                        new.append(self.model[arg])
                    else:
                        new.append(arg)
                args = new

            getattr(entity, set_attr)(*args)

    def apply_interfaces(self, entity, data):
        def get_data(arg):
            if type(arg) is str:
                if ".json" in arg:
                    return load_resource(arg)

                else:
                    return self.model[arg]

            else:
                return arg

        for i in self.interfaces:
            i_data = {}

            if i.name in entity.interface_data:
                i_data.update(
                    get_data(
                        entity.interface_data[i.name]
                    )
                )

            if i.name in data:
                i_data.update(get_data(
                    data[i.name])
                )

            i.apply_to_entity(entity, i_data)

    #
    # for use by interface methods
    #
    def create_entity(self, data):
        if type(data) is str:
            data = self.get_resource(data)

        entity = self.add_entities(data)[0]
        self.init_attributes(entity, data, init=True)
        self.apply_interfaces(entity, data)


class ApplicationInterface:
    def __init__(self, context):
        self.context = context
        self.name = self.__class__.__name__
        self.get_value = context.get_value
        self.init_order = []

    def log_item(self, entity, method_name, *args):
        print("{} applying {} to {} with args: {}".format(
            self.name, method_name, entity, args
        ))

    def apply_to_entity(self, entity, data):
        for method_name in self.context.get_init_order(data, self.init_order):
            value = self.get_value(data[method_name])

            if type(value) is not list:
                args = [value]
            else:
                args = value

            self.handle_data_item(
                entity, method_name, *args
            )

            self.log_item(entity, method_name, *args)

    def handle_data_item(self, entity, method_name, *args):
        # self.add_update_method(entity, method_name, *args)
        # self.call_method(entity, method_name, *args)
        # self.call_method_on_entity(entity, method_name, *args)
        pass

    def add_update_method(self, entity, method_name, *args):
        m = self.get_interface_method(
            entity, method_name
        )

        if m:
            def interface_update_method():
                # print(args)
                m(*args)

            entity.update_methods.append(interface_update_method)

    def call_method(self, entity, method_name, *args):
        m = self.get_interface_method(
            entity, method_name
        )

        if m:
            m(*args)

    def call_method_on_entity(self, entity, method_name, *args):
        m = self.get_interface_method(
            entity, method_name
        )

        if m:
            m(entity, *args)

    def get_interface_method(self, entity, method_name):
        m = None
        i_method = getattr(self, method_name, None)
        e_method = getattr(entity, method_name, None)

        if i_method and callable(i_method):
            m = i_method
        elif e_method and callable(e_method):
            m = e_method

        return m


class UpdateMethodInterface(ApplicationInterface):
    def handle_data_item(self, entity, method_name, *args):
        self.add_update_method(entity, method_name, *args)


class CallMethodInterface(ApplicationInterface):
    def handle_data_item(self, entity, method_name, *args):
        self.call_method(entity, method_name, *args)


class CallEntityInterface(ApplicationInterface):
    def handle_data_item(self, entity, method_name, *args):
        self.call_method_on_entity(entity, method_name, *args)
