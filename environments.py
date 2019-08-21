from inspect import isclass

import zsquirrel.constants as con
from zsquirrel.entities import Group

# This module defines a class which determines the standard data schema that is used
# to generate game entities (as 'Layer' and 'Sprite' subclass instances) and determine
# values for their setter methods as well as additional AppInterface methods.
#
# Additional hashable data can be passed to the Context object's 'model' dict as well,
# but must not use the reserved keys 'Layers' and 'Sprites'


# Environment data passed to the EnvLoader.populate() method should satisfy the following
# specifications...
#
# {
#   "layers": [
#       ...
#   ],
#
#   "sprites": [
#       ...
#   ],
#
#   "data": { ... } or [ ... ]
# }

#
# The "layers" key should define a list of 'Layer' class or subclass instances and likewise,
# "sprites" should define a list of "Sprite" class or subclass instances. In both cases
# following keys should be specified
#
# {
#   "name": <string>,
#   "class": <string>
# }
#
# Additionally, at least one item in the "layers" list should have the name "environment" which
# specifies that it is the top node of the Layer object hierarchy. A special "parent_layer" key
# can be defined for Layer objects that specifies the direct parent Layer of that object, but
# if it is not specified, its parent layer will be set to "environment" by default.
#
# All "Layer" and "Sprite" objects can also contain keys which define either:
#
#   - Setter methods: where the key name "attr" corresponds to a setter method with the name
#   "set_attr" and the value associated with the key defines the arguments passed to that setter.
#
#   or
#
#   - AppInterface classes: where the key name corresponds to the name of an AppInterface subclass
#   passed to the Context object at instantiation. The value associated with this key should be
#   a dict where the keys correspond to the names of the AppInterface subclass methods and their
#   values are the arguments passed to that method.
#
# For all setter methods and AppInterface methods, the arguments defined by the corresponding value
# can take the form of a single string, integer, float, or any hashable key defined in the Context
# object's 'model' dict, or a list object defining any number of those objects


class EnvLoader:
    """
    The EnvLoader class simply provides a 'populate' method
    that takes data for instantiating a hierarchy of Entity objects
    and also calling setter methods, and providing additional behaviors
    for the Entity objects through use of the Context object's
    AppInterface subclass instances.
    """
    def __init__(self, context):
        """
        On initialization, the Context object is passed to provide
        aliasing of the 'get_value' and 'load_resource' methods, plus
        the 'interfaces' and 'model' attributes

        :param context: Context object
        """
        self.context = context
        self.get_value = context.get_value
        self.load_resource = context.load_resource

    @property
    def interfaces(self):
        """
        Aliases the Context object's 'interfaces' list
        """
        return self.context.interfaces

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

        if isclass(cls):
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
        if init and hasattr(entity, con.INIT_DATA):
            data.update(entity.init_data)

        order = getattr(entity, con.INIT_ORDER, [])

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
                if (type(g) is str) and g not in self.model:
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
        """
        The main method of the EnvLoader class, it takes a
        dict object a particular structure and uses it to instantiate
        the hierarchy of Entity objects that will be updated by the
        Game's 'main' method.

        At the top level, the 'data' dict should contain a list of
        'sprites' and 'layers', each encoded as additional dict objects
        (referred to in method parameters as 'entries').

        Additionally, arbitrary key/values in the 'data' dict can be
        included that will be passed to the Context object's 'model'
        dict using the Context.update_model method, which automatically
        replaces object keys with live object references.

        This method also calls the 'set_layer_order' method to
        contextually assign a 'parent_layer' attribute that creates
        a hierarchy of Layer objects starting at the root level
        Environment object.

        See additional documentation of ZSquirrel "Data API" for a
        more detailed explanation of the structure of data that should
        be passed to this method.

        :param data: dict, provides data for initialization and
            setter / interface methods for Entity objects
        """
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

        self.create_entities(entities, data=data)

        # structure layer hierarchy
        self.set_layer_order(layers)

    def create_entities(self, entries, data=None):
        """
        For each 'entry' in the data dict passed to the 'populate'
        method, the data within that entry is used to call setter
        methods on Entity objects after they're instantiated, as
        well as passing them to various AppInterface
        methods.

        In addition to the list of 'entries' for Entities to be
        loaded, the rest of the incidental 'data' from the 'populate'
        method is passed and used to update the Context object's
        'model' dict. The 'model' must be updated after the Entities
        are substantiated but before their attribute setting methods
        are called in order to properly synchronize object reference
        in the values used to update the 'model' dict.

        :param entries: list, individual 'entry' dicts that specify
            Entity instantiation, attribute setters and interface
            methods
        :param data: dict, optional/additional key/values used to
            update the Context object's 'model' dict with synchronized
            object reference substitution
        """
        if data is None:
            data = {}

        # add 'empty' entity objects to Context.model
        for e in entries:
            name = e[con.NAME]
            cls_name = e[con.CLASS]
            self.add_entity(name, cls_name)

        # all additional data is used to update Context.model
        for section in data:
            self.context.update_model(data[section])

        # apply data attributes to entities
        for e in entries:
            entity = self.model[e[con.NAME]]
            self.set_entity_attributes(entity, e, init=True)
            self.apply_interfaces(entity, e)

    def apply_interfaces(self, entity, entry):
        """
        This method iterates over the interface instances in the
        Context.interfaces list and passes the appropriate data
        to the interface's 'apply_to_entity' method.

        The 'entry' dict should have keys for each AppInterface
        subclass that methods should be applied from. The value of this
        key can be a dict, or a str of a file name for data to be
        loaded from.

        Additionally, Entity objects can specify default interface data
        through an 'interface_data' attribute, (also a dict or str)
        which will be used to update the data passed to the
        'apply_to_entity' method.

        :param entity: Entity object
        :param entry: dict, entity data passed from 'create_entities'
            method
        """
        def get_data(arg):
            if type(arg) is str:
                if con.JSON in arg:
                    return self.load_resource(arg)

                else:
                    return self.model[arg]

            else:
                return arg

        default_i_data = getattr(entity, con.INTERFACE_DATA, {})

        for i in self.interfaces:
            i_data = {}

            if i.name in default_i_data:
                i_data.update(
                    get_data(
                        entity.interface_data[i.name]
                    )
                )

            if i.name in entry:
                i_data.update(get_data(
                    entry[i.name])
                )

            i.apply_to_entity(entity, i_data)
