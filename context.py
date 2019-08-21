import zsquirrel.constants as con


# This module defines a series of objects that are used to synchronize serial
# object data with the into a hierarchy of instantiated Entity objects to be
# updated by the Game object's main() loop. The Context object initializes a
# 'model' dict at run time that preserves object reference through a series of
# hashable keys. It also employs a resource loader from the Resources module
# that helps integrate loading of file data as well as file objects such as
# images and sounds.
#
# Additionally, the EnvLoader object and any
# AppInterface classes passed at runtime create an interface where data
# entry keys can call setter methods on Entity objects as well as various
# auxiliary methods through application interfaces that can help create update
# methods to give arbitrary runtime behavior to generic Entity objects.


class Context:
    """
    A single Context object should be instantiated at runtime to help interface
    serial data and resource files to create a functional hierarchy of 'layers'
    and 'sprites' as Entity objects.

    Other component objects such as the ResourceLoader, EnvLoader and
    various AppInterface classes are passed in at initialization to provide
    customizable methods for creating Entity objects and using data to call setter
    methods for those objects.
    """
    def __init__(self, game, res_loader, env_loader, class_dict, interfaces=None):
        """
        In addition to the Game instance, several component objects must be passed to
        this class at initialization.

        :param game: Game object
        :param res_loader: ResourceLoader object with a method for loading files
            and returning objects from those files
        :param env_loader: EnvLoader or subclass with a 'populate'
            method which is used to create an Environment object and hierarchy
            of Entity class objects based on data passed to the 'load_environment'
            method
        :param class_dict: dict, key/value pairs of Entity class names and the Class
            object itself, will typically be generated programmatically by the
            'get_context' module
        :param interfaces: list of AppInterface subclasses, used to provide
            additional methods to give more complicated behaviors to generic Entity
            objects
        """
        self.game = game
        self.resource_loader = res_loader
        self.env_loader = env_loader(self)

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
        Calls the EnvLoader object's 'populate' method.

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
        associated data to call setter methods and use AppInterface objects
        for additional Entity behaviors.

        The 'model' dict is reset each time this method is called, so collisions
        between key names for data of each environment can be ignored.

        :param data: dict or str, data to be passed to the
            EnvLoader's 'populate' method. If a 'str' is
            passed, it's treated as a file_name passed to 'load_resource'
            method
        """
        if type(data) is str:
            data = self.load_resource(data)

        self.reset_model()
        self.populate(data)

        self.game.set_environment(self.model[con.ENVIRONMENT])

    def run_game(self):
        """
        Calls the Game object's 'main' method, passing itself as context
        """
        self.game.main(self)


class AppInterface:
    """
    The AppInterface class functions as an abstract base class
    for specific subclasses that will help provide additional functionality
    to generic Entity objects that are loaded by the EnvLoader class.
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
