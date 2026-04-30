##############################################################################################

# Python’s OOP features such as classes, inheritance, encapsulation and polymorphism help create reusable, modular and maintainable code for complex applications.

    # Class and Object in Python
    # Inheritance 
    # Encapsulation
    # Polymorphism
    # Data Abstraction

# Python’s Object-Oriented Programming (OOP) features help structure large systems into reusable, modular components—especially useful
#  in analytics platforms, trading engines, APIs, and simulation frameworks. The five core pillars you listed are the foundation:

##############################################################################################


# 1. Class and Object in Python
# ------------------------------------------
# A class is a blueprint; an object is an instance of that blueprint.

class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def greet(self):
        return f"Hello, my name is {self.name}"


p1 = Person("Alice", 30)

print(p1.name)
print(p1.greet())

"""
>>> print(p1.name)
Alice
>>> print(p1.greet())
Hello, my name is Alice
"""

# Used for modeling:
    #     trades
    #     portfolios
    #     pricing engines
    #     signals
    #     datasets


# 2. Inheritance
# ------------------------------------------
# Inheritance allows one class to reuse functionality from another.

class Animal:
    def speak(self):
        return "Some sound"

class Dog(Animal):
    def speak(self):
        return "Bark"

d = Dog()
print(d.speak())

# Dog inherits from Animal but overrides behavior.

# Types of inheritance in Python
# ------------------------------------------
# Type	            Example
# Single	        A → B
# Multiple	        A + B → C
# Multilevel	    A → B → C
# Hierarchical	    A → B, A → C

# Example (multiple inheritance):
class Engine:
    def start(self):
        print("Engine started")


class GPS:
    def locate(self):
        print("Location found")


class Car(Engine, GPS):
    pass

a = Car()
print (a.locate())

"""
>>> print (a.locate())
Location found
None
"""

# 2a. Inheritance ( uses super)
# ------------------------------------------
# super() is a core tool in object-oriented programming, especially when working with inheritance and multiple inheritance.
# is used to access methods from a parent (base) class inside inheritance hierarchies.
# super() lets you call a method from the parent class without explicitly naming that parent.

class Animal:
    def speak(self):
        print("Animal makes a sound")


class Dog(Animal):
    def speak(self):
        super().speak()         # calls the parent version of speak().
        print("Dog barks")


d = Dog()
d.speak()

"""
>>> d.speak()
Animal makes a sound
Dog barks

"""
# Bad practice:
    # Animal.speak(self)\
# Better practice:
    # super().speak()
# Why?
    # Because super():

    # ✅ works with multiple inheritance
    # ✅ respects method resolution order (MRO)
    # ✅ avoids hard-coding class names
    # ✅ makes code maintainable


# Using super() in Constructors (__init__)

class Animal:
    def __init__(self, name):
        self.name = name


class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)                  # calls the parent constructor.
        self.breed = breed


d = Dog("Buddy", "Labrador")

print(d.name)
print(d.breed)

"""
>>> print(d.name)
Buddy
>>> print(d.breed)
Labrador

"""
How super() Works Internally

# Python determines which parent method to call using:MRO (Method Resolution Order)

class A:
    pass

class B(A):
    pass

class C(B):
    pass

print(C.__mro__)

# This defines how super() navigates inheritance.
"""
>>> print(C.__mro__)
(<class '__main__.C'>, <class '__main__.B'>, <class '__main__.A'>, <class 'object'>)

"""

# super() with Multiple Inheritance (Important)

class A:
    def show(self):
        print("A")


class B(A):
    def show(self):
        print("B")
        super().show()


class C(A):
    def show(self):
        print("C")
        super().show()


class D(B, C):
    def show(self):
        print("D")
        super().show()


d = D()
d.show()

"""
>>> d.show()
D
B
C
A

"""
# This happens because Python follows MRO order, not simple parent order.




# When You Should Use super()
    # Use it whenever:
        # ✔ extending parent behavior
        # ✔ calling parent constructor
        # ✔ working with mixins
        # ✔ designing frameworks
        # ✔ supporting multiple inheritance

    # Especially important in large systems like:
        # pricing engines
        # portfolio hierarchies
        # strategy inheritance trees
        # plugin architectures


# Example (Quant-Style Class Hierarchy)
    # class Instrument:
        #     def price(self):
        #         print("Generic pricing")


    # class Option(Instrument):
        #     def price(self):
        #         super().price()
        #         print("Option pricing logic")

        # Output:

    # Generic pricing
    # Option pricing logic

    # This pattern is common in financial libraries.




# 3. Encapsulation
# ------------------------------------------
# Encapsulation restricts direct access to internal data and protects object integrity

# Python uses naming conventions:
    # | Access    | Example |
    # | --------- | ------- |
    # | Public    | `x`     |
    # | Protected | `_x`    |
    # | Private   | `__x`   |


class Account:
    def __init__(self, balance):
        self.__balance = balance   # private variable

    def deposit(self, amount):
        self.__balance += amount

    def get_balance(self):
        return self.__balance


acc = Account(1000)
acc.deposit(500)

print(acc.get_balance())

print (acc.__balance)
"""
>>> print(acc.get_balance())
1500

>>> print (acc.__balance)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'Account' object has no attribute '__balance'. Did you mean: 'get_balance'?

"""

# Encapsulation ensures safe updates via methods.


# 4. Polymorphism
# ------------------------------------------
# Polymorphism means same interface, different behavior

class Dog:
    def speak(self):
        return "Bark"


class Cat:
    def speak(self):
        return "Meow"


animals = [Dog(), Cat()]

for animal in animals:              # Same method name → different implementation.
    print(animal.speak())

"""
>> for animal in animals:
...     print(animal.speak())
... 
Bark
Meow
"""

# Another example: operator polymorphism
print(3 + 4)
print("Hello " + "World")

# Same operator +, different behavior.


# 5. Data Abstraction
# ------------------------------------------
# Abstraction hides implementation details and exposes only essential functionality.


from abc import ABC, abstractmethod
class Shape(ABC):

    @abstractmethod
    def area(self):
        pass


class Circle(Shape):

    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius ** 2


c = Circle(5)
print(c.area())

"""
>> print(c.area())
78.5
"""


# Encapsulation vs Abstraction (Common Confusion)
# ----------------------------------------------------

    # Feature	      Purpose
    #----------------------------------
    # Encapsulation	  Protect data
    # Abstraction	  Hide complexity

    # Example:

        # Encapsulation → private variables
        # Abstraction → abstract base classes





# Real Example (Quant-Style OOP Design)
# -----------------------------------------------
# Polymorphism + abstraction together.

    # Example: financial instrument hierarchy

from abc import ABC, abstractmethod

class Instrument(ABC):

    @abstractmethod
    def price(self):
        pass


class Bond(Instrument):

    def price(self):
        return "Bond pricing logic"


class Option(Instrument):

    def price(self):
        return "Option pricing logic"


portfolio = [Bond(), Option()]

for inst in portfolio:
    print(inst.price())


"""
>> for inst in portfolio:
...     print(inst.price())
... 
Bond pricing logic
Option pricing logic
"""


# Why OOP Matters in Large Python Systems

# OOP enables:
    # ✅ modular strategy engines
    # ✅ reusable pricing components
    # ✅ extensible analytics pipelines
    # ✅ cleaner API layers
    # ✅ scalable backtesting frameworks

# Typical structure:
    # Instrument
    #  ├── FXOption
    #  ├── Swap
    #  └── EquityOption

# This mirrors production quant architectures.