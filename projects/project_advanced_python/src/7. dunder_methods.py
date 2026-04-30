
#############################################################################################################################
# Magic (Dunder) Methods: Special methods like __init__, __call__, and __str__ that allow objects to interact with built-in operations like addition 
# or indexing.
# Magic methods (also called dunder methods, short for double underscore) are special methods that let your objects integrate with Python’s 
# built-in syntax and operators.

# They enable things like:
    # + addition ➝ __add__
    # indexing obj[i] ➝ __getitem__
    # printing print(obj) ➝ __str__
    # calling objects like functions ➝ __call__
# Magic methods define how your objects behave like native Python objects.
#############################################################################################################################

# Python automatically invokes them behind the scenes.

# __init__
# __str__
# __repr__
# __len__
# __getitem__
# __add__
# __call__


# 1. __init__ — Object Constructor
#--------------------------------------------
# Runs when object is created.
# create object → initialize attributes

class Person:
    def __init__(self, name):
        self.name = name


p = Person("Alice")
print(p.name)

"""
>>> print(p.name)
Alice
"""

# 2. __str__ — User-Friendly String Representation
#---------------------------------------------------
# Defines what print(obj) displays

class Person:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Person({self.name})"


p = Person("Alice")
print(p)

"""
>>> print(p)
Person(Alice)
"""

# 3. __repr__ — Developer Representation
#---------------------------------------------------
# Used in debugging and interactive shells.

class Person:
    def __repr__(self):
        return "Person('Alice')"

# __repr__ → unambiguous
# __str__ → readable


# 4. __len__ — Length Support
#---------------------------------------------------
# Allows len(obj)

class MyList:
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)


obj = MyList([1, 2, 3])
print(len(obj))

"""
>>> print(len(obj))
3
"""

# 5. __getitem__ — Indexing Support
#---------------------------------------------------
# Enables: obj[i]

class MyList:
    def __init__(self, data):
        self.data = data

    def __getitem__(self, index):
        return self.data[index]


obj = MyList([10, 20, 30])
print(obj[1])



# 6. __setitem__ — Assignment via Index
#---------------------------------------------------
# Supports: obj[i] = value

class MyList:
    def __init__(self, data):
        self.data = data

    def __setitem__(self, index, value):
        self.data[index] = value


obj = MyList([1, 2, 3])
obj[0] = 100
print(obj.data)

"""
>>> print(obj.data)
[100, 2, 3]
"""

# 7. __add__ — Operator Overloading
#---------------------------------------------------
# Controls behavior of +. This is called operator overloading.

class Vector:
    def __init__(self, x):
        self.x = x

    def __add__(self, other):
        return Vector(self.x + other.x)


v1 = Vector(2)
v2 = Vector(3)

v3 = v1 + v2
print(v3.x)

"""
>>> print(v3.x)
5
"""

# 8. __call__ — Make Objects Callable
#---------------------------------------------------
# Lets objects behave like functions.

class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, x):
        return x * self.factor


double = Multiplier(2)

print(double(5))

"""
>>> print(double(5))
10
"""

# Used heavily in:
    # decorators
    # ML pipelines
    # strategy engines


# 9. __contains__ — Membership Testing
#---------------------------------------------------
# Supports: x in obj

class MyContainer:
    def __init__(self, items):
        self.items = items

    def __contains__(self, item):
        return item in self.items


c = MyContainer([1, 2, 3])
print(2 in c)

"""
>>> print(2 in c)
True
"""


# 10. __iter__ — Make Object Iterable
#---------------------------------------------------
# Allows: for x in obj:

class Counter:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        return iter(range(self.n))


for x in Counter(3):
    print(x)

"""
>>> for x in Counter(3):
...     print(x)
... 
0
1
2
"""


# 11. __eq__ — Equality Comparison
#---------------------------------------------------
# Controls: obj1 == obj2


class Point:
    def __init__(self, x):
        self.x = x

    def __eq__(self, other):
        return self.x == other.x


print(Point(2) == Point(2))

"""
>>> print(Point(2) == Point(2))
True

"""

# 12. __enter__ and __exit__ — Context Managers
#---------------------------------------------------
# Used with: with obj:

class Demo:
    def __enter__(self):
        print("Enter")

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exit")


with Demo():
    print("Inside")

"""
>>> with Demo():
...     print("Inside")
... 
Enter
Inside
Exit
"""

# Most Important Dunder Methods (Quick Reference)
#---------------------------------------------------
# Method	            Purpose
#------------------------------------
# __init__	            constructor
# __str__	            readable print output
# __repr__	            developer representation
# __len__	            supports len()
# __getitem__	        indexing
# __setitem__	        index assignment
# __add__	            + operator
# __eq__	            equality comparison
# __call__	            callable objects
# __iter__	            iteration
# __enter__/__exit__	context manager




# Why Magic Methods Matter in Real Systems
    # They enable Pythonic APIs like:
        # portfolio["EURUSD"]      # __getitem__
        # signal()                 # __call__
        # price1 + price2          # __add__
        # len(order_book)          # __len__
        # with db_connection():    # __enter__/__exit__


# These patterns appear everywhere in:

    # trading engines 📈
    # pandas & NumPy internals
    # ORMs (SQLAlchemy)
    # ML pipelines
    # async frameworks