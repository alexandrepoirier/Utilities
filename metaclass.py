"""
argparser.py by Alexandre Poirier
last modified on 2018-02-22 18:22 ET

This module defines the class MetaClass and provides an example of how the class works.
Documentation on this is in the class's docstring.
"""

class MetaClass(object):
    """
    class MetaClass

    This class provides added functionality for python classes.
    It allows the user to define a set of acceptable arguments for the init line as a list of strings.

    The child class will never have to change the signature of its init line and/or adapt type checking internally as
    it is all handled automatically by the MetaClass class methods.

    Arguments default values are also handled by this class so if an argument is omitted from the init line it will
    be added automatically with its default value.

    :parent: object

    :class attributes:
        _kawargs_ : list (mandatory), contains the names of accepted attributes by the child class as strings.
        _args_defaults_ : dictionary (optional), contains default values for arguments.
                          Arguments must be found in _kwargs_.
        _req_args_ : int (optional), the number of arguments that are required on the init line.
                     Will match the values in _kwargs_[:_req_args_].
        _args_types_ : list of types (optional), used for type checking. If empty, types won't be checked.
                       If not empty, must be of length len(_kwargs_). If many types are acceptable, you can specify
                       a list of types for a given attribute.
                       Note: type checking isn't available for public attributes as it would cause infinite recursion.
        _prvt_args_ : bool or list of bools, defines if an attribute is private or not. When a bool is given, it acts
                      as the default for all instance attributes. If a list is given, attributes privacy will be based
                      on the values in it. If the list is too short, it is automatically filled with the default (not
                      private) until reaching len(_kwargs_).

    :use:
        1- Subclass your class from MetaClass
        2- Define the init method like so: __init__(self, *args, **kwargs)
        3- Override all MetaClass class arguments
        4- Call MetaClass.__init__(self, *args, **kwargs) in the init method of the child class
    """
    _kwargs_ = []
    _args_defaults_ = {}
    _req_args_ = 0
    _args_types_ = []
    _prvt_args_ = False
    def __init__(self, *args, **kwargs):
        MetaClass.__parse__(self, *args, **kwargs)

    def __parse__(self, *args, **kwargs):
        MetaClass.__intergrity__(self, *args, **kwargs)
        index = 0
        if args:
            for val in args:
                MetaClass.__add_attr__(self, index, val)
                index += 1
        if kwargs:
            for key, val in kwargs.items():
                if index > self._kwargs_.index(key):
                    if getattr(self, MetaClass.__get_attr_name__(self, key), False):
                        raise AttributeError("attribute '{}' already passed as positional argument".format(key))
                MetaClass.__add_attr__(self, key, val)
                index += 1
        MetaClass.__set_defaults__(self)

    def __intergrity__(self, *args, **kwargs):
        """
        Validates that the arguments passed to the constructor match what is specified by the class attributes.
        
        :param args: positional arguments as passed to __init__
        :param kwargs: keyword arguments as passed to __init__
        :return: None
        """
        len_args, len_kwargs, total_args = len(args), len(kwargs), len(args)+len(kwargs)

        # make sure required arguments are passed
        if len_args < self._req_args_:
            missing = self._kwargs_[len_args:self._req_args_]
            for arg in kwargs:
                if arg in missing:
                    missing.remove(arg)
            if missing:
                e = "class {} required arguments : {}".format(self.__class__.__name__,
                                                              str(self._kwargs_[:self._req_args_]).strip('[]'))
                raise AttributeError(e)

        # make sure not too many arguments are passed
        if len_args > len(self._kwargs_) or len_kwargs > len(self._kwargs_) or total_args > len(self._kwargs_):
            raise AttributeError("Too many arguments")

        for attr in kwargs:
            if attr not in self._kwargs_:
                raise AttributeError("Unexpected argument '{}' passed to class {}.__init__".format(attr, self.__class__.__name__))

        # convert _prvt_args to a list of length len(_kwargs)
        if isinstance(self._prvt_args_, list):
            if len(self._prvt_args_) < len(self._kwargs_):
                for i in range(len(self._prvt_args_), len(self._kwargs_)):
                    self._prvt_args_.append(False)
        else:
            self.__class__._prvt_args_ = [self._prvt_args_ for i in range(len(self._kwargs_))]

    def __set_defaults__(self):
        """
        Sets the default attributes if any, and if not already set by the user.
        
        :return: None
        """
        for key, val in self._args_defaults_.items():
            if not getattr(self, MetaClass.__get_attr_name__(self, key), False):
                MetaClass.__add_attr__(self, key, val)

    def __make_attr_name__(self, index):
        """
        Creates the final name of the attribute depending on its privacy level.
        
        :param index: int, position index in the _kwargs_ list
        :return: str, internal name of the attribute
        """
        return '__'+self._kwargs_[index] if self._prvt_args_[index] else self._kwargs_[index]

    def __get_attr_name__(self, attr):
        """
        Ges the final name of the attribute depending on its privacy level.
        
        :param attr: str, name of the attribute as seen by the user
        :return: str, internal name of the attribute
        """
        return '__'+attr if self._prvt_args_[self._kwargs_.index(attr)] else attr

    def __get_attr_private__(self, attr):
        """
        Returns true if the given attribute is private.
        
        :param attr: str, name of the attribute as seen by the user
        :return: bool
        """
        return self._prvt_args_[self._kwargs_.index(attr)]

    def __check_type__(self, index, val):
        """
        Raises TypeError when the type isn't valid. Returns True if the type is valid.
        
        :param index: int, position index of the attribute in _args_types_
        :param val: any type, value to test the type on
        :return: bool
        """
        if self._args_types_[index] is callable:
            if not callable(val):
                raise TypeError("'{}' argument must be of type 'callable'".format(self._kwargs_[index]))
        elif isinstance(self._args_types_[index], list):
            for type in self._args_types_[index]:
                if isinstance(val, type):
                    return True
            types_str = [str(elem).strip("<class ''>") for elem in self._args_types_[index]]
            raise TypeError("'{}' argument must be of one of these types {}".format(self._kwargs_[index],
                                                                                    str(types_str).strip("[]")))
        else:
            if not isinstance(val, self._args_types_[index]):
                raise TypeError("'{}' argument must be of type {}".format(self._kwargs_[index],
                                                                          str(self._args_types_[index]).strip(
                                                                              "<class >")))
        return True

    def __add_attr__(self, key, val):
        """
        Adds an attribute to the class and creates the getter and setter methods for it.
        Also checks if the type is valid.
        
        :param key: str, name of the attribute as seen by the user
        :param val: any type, value of the attribute
        :return: None
        """
        if isinstance(key, str):
            key = self._kwargs_.index(key)
        if self._args_types_:
            if MetaClass.__check_type__(self, key, val):
                name = MetaClass.__make_attr_name__(self, key)
                setattr(self, name, val)
                MetaClass.__methods__(self, self._kwargs_[key], name, self._args_types_[key])
        else:
            setattr(self, MetaClass.__make_attr_name__(self, key), val)
            MetaClass.__methods__(self, self._kwargs_[key], name)

    def __methods__(self, attr, name, type=None):
        """
        Creates a getter and a setter for private instance attributes.

        :param attr: str, name of the attribute as seen by the user
        :param name: str, internal name of the attribute, private to the class
        :param type: type, type to check when setting the attribute
        :return: None
        """
        if not MetaClass.__get_attr_private__(self, attr):
            return

        getter_str = "__get_{}__".format(attr)
        getter = "def {0}(self):\n" \
                 "    return self.{1}\n" \
                 "setattr(self.__class__, '{0}', {0})".format(getter_str, name)
        exec(getter)

        setter_str = "__set_{}__".format(attr)
        if type:
            setter = "def {0}(self, value):\n" \
                     "    if MetaClass.__check_type__(self, self._kwargs_.index('{1}'), value):\n" \
                     "        self.{2} = value\n" \
                     "setattr(self.__class__, '{0}', {0})".format(setter_str, attr, name)
        else:
            setter = "def {0}(self, value):\n" \
                     "    self.{1} = value\n" \
                     "setattr(self.__class__, '{0}', {0})".format(setter_str, name)
        exec(setter)
        exec("setattr(self.__class__, '{}', property({}, {}))".format(attr, getter_str, setter_str))



if __name__ == '__main__':
    class Test(MetaClass):
        _kwargs_ = ['a', 'b', 'c', 'func']
        _args_defaults_ = {'c':'lol', 'b':5}
        _req_args_ = 2
        _args_types_ = [[int,float], int, str, callable]
        _prvt_args_ = [True, False, True]
        def __init__(self, *args, **kwargs):
            MetaClass.__init__(self, *args, **kwargs)

    def yo():
        pass

    test_header = "-------------- Test no.{} --------------"
    test_footer = "[end Test no.{}]\n"

    for test in range(9):
        print(test_header.format(test))
        try:
            if test == 0:
                # no errors
                t = Test(1.2, b=3, c='test', func=yo)
                # accessing elements normally
                print("t.a = {}\nt.b = {}".format(t.a, t.b))
            elif test == 1:
                # too many arguments
                t = Test(1, b=3, c='test', func=yo, d=5)
            elif test == 2:
                # wrong type
                t = Test(1, b=3, c='test', func=1)
            elif test == 3:
                # argument passed twice
                t = Test(1, 2, b=3, c='test')
            elif test == 4:
                # missing an argument
                t = Test(1)
            elif test == 5:
                # unexpected argument
                t = Test(1, b=3, c='test', funcs=yo)
            elif test == 6:
                # setting private and public attributes
                t = Test(1, b=3, c='test', func=yo)
                print("{} = {} before modification".format('a', t.a))
                t.a = 5
                print("{} = {} after modification".format('a', t.a))
                # no type checking on public elements
                t.b = None
            elif test == 7:
                # omitting an optional argument that has a default
                t = Test(1, b=3, func=yo)
            elif test == 8:
                # setting wrong type on private attribute
                t = Test(1, b=3, c='test', func=yo)
                t.a = 'this is nuts!'
        except Exception as e:
            print("An error was encountered : {}".format(e))
        else:
            print(t.__dict__)
        print(test_footer.format(test))
