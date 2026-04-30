###############################################################################################################

https://realpython.com/python-descriptors/

# Descriptors are one of Python’s most powerful (and least understood) object model features. They control how attribute access works inside classes. 
# In fact, many built-ins like @property, methods, and even staticmethod are implemented using descriptors.
# Think of descriptors as custom attribute access logic.

# A descriptor is any object that defines one or more of these methods:
    # __get__(self, instance, owner)
    # __set__(self, instance, value)
    # __delete__(self, instance)
# If a class attribute implements any of these, Python automatically routes attribute access through them.


# Why Descriptors Exist
    # They allow:
        # ✔ validation
        # ✔ lazy computation
        # ✔ logging
        # ✔ computed attributes
        # ✔ ORM field definitions
        # ✔ access control

    # They power frameworks like:
        # Django ORM
        # SQLAlchemy
        # dataclasses
        # property()
        # methods

###############################################################################################################

# descriptors.py
class Verbose_attribute():
    def __get__(self, obj, type=None) -> object:
        print("accessing the attribute to get the value")
        return 42
    def __set__(self, obj, value) -> None:
        print("accessing the attribute to set the value")
        raise AttributeError("Cannot change the value")

class Foo():
    attribute1 = Verbose_attribute()

my_foo_object = Foo()
x = my_foo_object.attribute1
print(x)

"""
>>> x = my_foo_object.attribute1
accessing the attribute to get the value
>>> print(x)
42
"""


# Another example
# ------------------------------
class Descriptor:
    def __get__(self, instance, owner):
        return "Value from descriptor"

class MyClass:
    attr = Descriptor()


obj = MyClass()
print(obj.attr)

"""
>>> print(obj.attr)
Value from descriptor
"""


# Instead of returning attr directly, Python calls:
#     Descriptor.__get__(obj, MyClass)
# automatically