import constants as con
from inspect import isclass
from entities import Entity, Group
from resources import ResourceLoader


class Context:
    def __init__(self, game, resources, class_dict=None):
        self.resource_loader = resources
        self.game = game

        self._class_dict = class_dict
        self.model = {}
        self.reset_model()

    def reset_model(self):
        self.model = {
            con.CONTEXT: self,
            con.GAME: self.game
        }

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

    def load_resource(self, file_name):
        return self.resource_loader.load_resource(file_name)

    def load_environment(self, data):
        if type(data) is str:
            data = self.load_resource(data)

        self.reset_model()
        self.populate(data)

        self.game.set_environment(self.model[con.ENVIRONMENT])

    @staticmethod
    def get_default_context(game, cd=None):
        res = ResourceLoader.get_default_loader()

        return Context(game, res, class_dict=cd)

    def run_game(self):
        self.game.main(self)


class EnvironmentLoader:
    def __init__(self, context):
        self.context = context
        self.get_value = context.get_value
        self.load_resource = context.load_resource

    @property
    def model(self):
        """
        This alias property ensures that references to the 'model' dict
        always reference the current dict in the Context attribute,
        as a new dict is generated every time Context.reset_model()
        is called.

        :return: the 'model' dict of the Context object
        """
        return self.context.model

    def set_layer_order(self, layer_entries):
        """
        This method sets a hierarchy of Layer.parent_layer attributes
        starting with the top level Environment object, based off of
        a list of dict objects that describe each Layer. Layer entries
        that don't specify the 'parent_layer' attribute automatically
        set their 'parent_layer' to the Environment object.

        :param layer_entries: dict objects that describe Layer objects
        """
        env = self.get_value(con.ENVIRONMENT)

        for l in layer_entries:
            layer = self.model[l[con.NAME]]

            if layer is not env and layer.parent_layer is None:
                layer.set_parent_layer(env)

    def add_entity(self, name, cls_name):
        """
        This method initializes an entity object and adds
        it to the Context object's model dict under a key
        matched to the object's name string.

        :param name: str, name/key for the entity
        :param cls_name: str, key for the Context object's class dict
        :return: and instantiated Entity object created by the class
            specified in cls_name
        """
        cls = self.model[cls_name]

        if isclass(cls) and issubclass(cls, Entity):
            entity = cls(name)
            self.model[name] = entity

        else:
            raise ValueError("'{}' not an Entity class".format(cls_name))

        return entity

    @staticmethod
    def get_init_order(data, order):
        """
        This method compares a preferred 'order' list of keys for
        attribute setters to ensure that data loaded as 'dict'
        objects is initialized in a particular order where that
        is required.

        :param data: dict, the Entity attribute data to be parsed
        :param order: list, the attribute names to be used as the
            primary initialization order
        :return: 'attrs' list, correctly ordered list of attr names
        """
        keys = [k for k in data]

        attrs = [
                    o for o in order if o in keys
                ] + [
                    k for k in keys if k not in order
                ]

        return attrs

    def set_entity_attributes(self, entity, data, init=False):
        """
        This method calls setter methods on an Entity object by
        iterating over keys in the 'data' dict and checking for
        corresponding setter methods to pass the dict key's value to.

        The 'init' flag should be set to True when an Entity is
        first created in case its class defines a default set of
        attributes and values in its 'init_data' attribute.

        Entity objects can optionally contain an 'init_order' list
        with keys for attribute setters that helps define a required
        initialization order. All attributes with names that match keys
        in that list will have their setters called first, in that order
        before all the remaining attribute keys in the entity data
        are set.

        :param entity: Entity object to have attribute setters called
        :param data: a dict of attribute keys that correspond to setter
            methods of the Entity object and values for each key that
            correspond to the value to be passed to that method. If the
            value is a list object the individual list items will be
            passed as individual parameters to the setter method.
        :param init: a Bool flag that checks an option "init_data" attribute
            of the Entity object. Typically defined by the class, this
            data serves as a set of default set of attributes and values
            to be used when initializing a new Entity object
        """
        if init and hasattr(entity, "init_data"):
            data.update(entity.init_data)

        order = getattr(entity, "init_order", [])

        for attr in self.get_init_order(data, order):
            set_attr = con.SET_ + attr

            if hasattr(entity, set_attr):
                value = data[attr]
                if type(value) is list:
                    args = value
                else:
                    args = [value]

                self.set_attribute(entity, set_attr, *args)

    def set_attribute(self, entity, set_attr, *args, sub=None):
        """
        This method calls a setter on the passed Entity object.

        If "set_group" or "set_groups" are the method being called,
        the arguments are contextually changed to a new Group object
        if they are strings, using the string as the Group name which
        is then used as the key for the Group in the Context.model dict.

        Any arguments to be passed to the setter method are also
        passed to the Context.get_value() method, which replaces any
        keys found in the Context.model dict with the object or value
        that they reference.

        :param entity: The Entity object whose setter method is
            being called
        :param set_attr: str, the method name for the setter that
            is being referenced. The standard API defines Entity
            setter method names as beginning with "set_"
        :param args: the arguments to be passed to the setter method
        :param sub: an optional substitutions dict to be passed to the
            Context.get_value() method
        """
        if (con.GROUP in set_attr) or (con.GROUPS in set_attr):
            for g in args:
                if type(g) is str:
                    self.model[g] = Group(g)

        args = self.get_value(args, sub=sub)

        getattr(entity, set_attr)(*args)

    def load_data(self, item):
        """
        This method checks a potential data entry to see whether
        additional data should be loaded from a file resource.
        This file should be loaded by the ResourceLoader such that
        it produces a dict object with Entity object data.

        If 'item' is a str, it will be treated as a file_name to
        be loaded by the Context object's ResourceLoader.

        If 'item' is a dict containing a 'json' key, the value of
        that key is used as a file_name to load data from which
        is then used to update the dict before returning.

        :param item: str or dict, a potential object data entry
            to be checked for additional data that should be loaded
            from a file resource
        :return: 'item' dict, updated with additional data from
            file resources where necessary
        """
        if type(item) is str:
            item = self.load_resource(item)

        if con.JSON in item:
            file_name = item.pop(con.JSON)
            d = self.load_resource(file_name)
            d.update(item)
            item = d

        return item

    def populate(self, data):
        def get_entity_data(d, key):
            if key in d:
                entries = d.pop(key)
                return [self.load_data(i) for i in entries]
            else:
                return []

        # Get list of data entries for Layer objects
        layers = get_entity_data(data, con.LAYERS)

        # Get list of data entries for Sprite objects
        sprites = get_entity_data(data, con.SPRITES)

        # Make an "entities" list of layer and sprite data entries
        entities = layers + sprites

        # add 'empty' entity objects to Context.model
        for e in entities:
            name = e[con.NAME]
            cls_name = e[con.CLASS]
            self.add_entity(name, cls_name)

        # all additional data is used to update Context.model
        for section in data:
            self.context.update_model(section)

        # apply data attributes to entities
        for entry in entities:
            entity = self.model[data[con.NAME]]
            self.set_entity_attributes(entity, entry, init=True)
            # self.apply_interfaces(entity, entry)

        # structure layer hierarchy
        self.set_layer_order(layers)
