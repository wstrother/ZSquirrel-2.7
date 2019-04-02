import zsquirrel.constants as con
from inspect import isclass
from zsquirrel.entities import Group
from zsquirrel.resources import ResourceLoader


# This module defines a series of objects that are used to synchronize serial
# object data with the into a hierarchy of instantiated Entity objects to be
# updated by the Game object's main() loop. The Context object initializes a
# 'model' dict at run time that preserves object reference through a series of
# hashable keys. It also employs a resource loader from the Resources module
# that helps integrate loading of file data as well as file objects such as
# images and sounds.
#
# Additionally, the EnvironmentLoader object and any
# ApplicationInterface classes passed at runtime create an interface where data
# entry keys can call setter methods on Entity objects as well as various
# auxiliary methods through application interfaces that can help create update
# methods to give arbitrary runtime behavior to generic Entity objects.


class Context:
    """
    A single Context object should be instantiated at runtime to help interface
    serial data and resource files to create a functional hierarchy of 'layers'
    and 'sprites' as Entity objects.

    Other component objects such as the ResourceLoader, EnvironmentLoader and
    various ApplicationInterface classes are passed in at initialization to provide
    customizable methods for creating Entity objects and using data to call setter
    methods for those objects.
    """
    def __init__(self, game, res_loader, populate_class, class_dict, interfaces=None):
        """
        In addition to the Game instance, several component objects must be passed to
        this class at initialization.

        :param game: Game object
        :param res_loader: ResourceLoader object with a method for loading files
            and returning objects from those files
        :param populate_class: EnvironmentLoader or subclass with a 'populate'
            method which is used to create an Environment object and hierarchy
            of Entity class objects based on data passed to the 'load_environment'
            method
        :param class_dict: dict, key/value pairs of Entity class names and the Class
            object itself, will typically be generated programmatically by the
            'get_context' module
        :param interfaces: list of ApplicationInterface subclasses, used to provide
            additional methods to give more complicated behaviors to generic Entity
            objects
        """
        self.game = game
        self.resource_loader = res_loader
        self.env_loader = populate_class(self)

        self.interfaces = []
        if interfaces is None:
            interfaces = []
        for i in interfaces:
            self.interfaces.append(i(self))

        self._class_dict = class_dict
        self.model = {}
        self.reset_model()

    def populate(self, data):
        """
        Calls the EnvironmentLoader object's 'populate' method.

        :param data: dict, entity/setter data
        """
        self.env_loader.populate(data)

    def reset_model(self):
        """
        Creates the basic template of the 'model' dict. Called at initialization
        and whenever a new environment is loaded by calling 'load_environment'
        method.

        Default keys include
            'context': Context object
            'game': Game object
        as well as all the key/values of the 'class_dict' set up at initialization
        """
        self.model = {
            con.CONTEXT: self,
            con.GAME: self.game
        }

        self.model.update(self._class_dict)

    def update_model(self, data):
        """
        Updates the 'model' dict while recursively checking 'data' object's
        dict values for existing object keys. I.E. replaces hashed keys in
        the 'data' dict's values with live reference to object instances.

        :param data: dict, generic data to be added to 'model' dict
        """
        for item_name in data:
            item = self.get_value(data[item_name])
            self.model[item_name] = item

    def set_value(self, key, value):
        self.model[key] = value

    def get_value(self, value, sub=None):
        """
        Recursively checks a given 'value' against keys in the 'model' dict and
        replaces them with live reference to object instances. An additional
        'sub' dict can be passed to provide contextual key/value substitutions.

        :param value: obj, generic 'value' checked against keys in the 'model' dict
        :param sub: dict, optional set of key/value substitutions
        """
        def get(k):
            if k in self.model:
                return self.model[k]

            elif sub and k in sub:
                return sub[k]

            else:
                return k

        if type(value) in (list, tuple):
            new = []
            for item in value:
                new.append(
                    self.get_value(item, sub=sub)
                )

            return new

        elif type(value) is dict:
            for key in value:
                value[key] = self.get_value(
                    value[key], sub=sub
                )

            return value

        else:
            return get(value)

    def load_resource(self, file_name):
        """
        Alias's 'load_resource' method of ResourceLoader object

        :param file_name: str, file_name passed to resource loader
        """
        return self.resource_loader.load_resource(file_name)

    def load_environment(self, data):
        """
        This method should be called anytime a new top level Environment needs to
        be established, creating a hierarchy of Entity objects and using the
        associated data to call setter methods and use ApplicationInterface objects
        for additional Entity behaviors.

        The 'model' dict is reset each time this method is called, so collisions
        between key names for data of each environment can be ignored.

        :param data: dict or str, data to be passed to the
            EnvironmentLoader's 'populate' method. If a 'str' is
            passed, it's treated as a file_name passed to 'load_resource'
            method
        """
        if type(data) is str:
            data = self.load_resource(data)

        self.reset_model()
        self.populate(data)

        self.game.set_environment(self.model[con.ENVIRONMENT])

    @classmethod
    def get_default_context(cls, game, classes, interfaces=None):
        """
        This method helps create a standard Context object with default
        ResourceLoader and EnvironmentLoader components. Typically the
        class_dict and interface class list will be generated and passed
        programmatically by the 'get_context' module.

        :param game: Game object
        :param classes: list, Entity classes to be instantiated by the
            EnvironmentLoader's 'populate' method
        :param interfaces: None or list, interface classes to be instantiated in the
            initialization method of the Context object

        :return: An instance of the Context class with a set of
            default component objects
        """
        cd = {
            c.__name__: c for c in classes
        }

        return cls(
            game,
            ResourceLoader.get_default_loader(),
            EnvironmentLoader,
            class_dict=cd,
            interfaces=interfaces
        )

    def run_game(self):
        """
        Calls the Game object's 'main' method, passing itself as context
        """
        self.game.main(self)


class EnvironmentLoader:
    """
    The EnvironmentLoader class simply provides a 'populate' method
    that takes data for instantiating a hierarchy of Entity objects
    and also calling setter methods, and providing additional behaviors
    for the Entity objects through use of the Context object's
    ApplicationInterface subclass instances.
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
        The main method of the EnvironmentLoader class, it takes a
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
        well as passing them to various ApplicationInterface
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

        The 'entry' dict should have keys for each ApplicationInterface
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


class ApplicationInterface:
    """
    The ApplicationInterface class functions as an abstract base class
    for specific subclasses that will help provide additional functionality
    to generic Entity objects that are loaded by the EnvironmentLoader class.
    """
    def __init__(self, context):
        """
        Single instances of each subclasses should be instantiated by the Context
        object at initialization which passes itself to his method, mainly used
        to alias the 'get_value' method which provides access to the 'model' dict.

        Additionally, the 'init_order' list can contain strings that specify a
        preferred order for interface methods to be called in.

        :param context: Context object
        """
        self.context = context
        self.name = self.__class__.__name__
        self.get_value = context.get_value
        self.set_value = context.set_value
        self.init_order = []

    def apply_to_entity(self, entity, entry):
        """
        This method iterates over the keys in the 'entry' dict and then
        contextually looks up the method using 'get_interface_method' before
        passing the entity and the arguments associated with key's value
        to the method.

        Values contained in 'entry' dict keys are passed through the 'get_value'
        method to replace matching keys in the Context.model dict with live
        object reference.

        NOTE: When the 'entry' dict has a key with a value of 'True' it is
        used as a special case for methods that take no arguments beyond the
        Entity object itself.

        :param entity: Entity object
        :param entry: dict, data entry for list of interface methods that should
            be applied to the Entity
        """
        get_order = self.context.env_loader.get_init_order

        for method_name in get_order(entry, self.init_order):
            value = self.get_value(entry[method_name])

            if value is True:
                value = []

            if type(value) is not list:
                args = [value]
            else:
                args = value

            m = getattr(self, method_name, None)

            if m:
                m(entity, *args)
            else:
                raise ValueError("Interface method {} not found in class {}".format(
                    method_name, self.name
                ))
