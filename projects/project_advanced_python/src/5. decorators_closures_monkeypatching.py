##########################################################################################################################################

# https://realpython.com/primer-on-python-decorators/ : Very good one ( with lots of examples)
# https://realpython.com/python-closure/

# Closures and decorators are two closely related advanced Python concepts. Closures explain how functions remember state, and decorators 
# use closures to modify behavior of other functions. Together, they’re foundational for writing clean, reusable, production-grade Python (especially in APIs, analytics pipelines, logging layers, and trading infra).

# Decorators are a powerful feature in Python. You can use decorators to modify a function’s behavior dynamically. 
# In Python, you have two types of decorators:

    # Function-based decorators
    # Class-based decorators

##########################################################################################################################################

# ----------------------------------------------------------------------------------
# 2. Closures
# A decorator is a function that wraps another function to extend its behavior.
# ----------------------------------------------------------------------------------
def multiplier(n):
    def multiply(x):
        return x * n
    return multiply


double = multiplier(2)
triple = multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15

"""
>>> print(double(5))   # 10
10
>>> print(triple(5))   # 15
15
>>> 
"""


# Why Closures Are Useful
    # Closures enable:

    # ✔ function factories
    # ✔ encapsulated state without classes
    # ✔ lightweight configuration
    # ✔ decorators

# Closures vs Decorators (Difference)

# | Feature                   | Closure | Decorator |
# | ------------------------- | ------- | --------- |
# | Stores outer variables    | ✅       | ✅         |
# | Returns function          | ✅       | ✅         |
# | Modifies another function | ❌       | ✅         |
# | Uses closure internally   | —         | ✅         |

# decorators are built using closures



# ----------------------------------------------------------------------------------
# 2. Closures
# A closure is a function that remembers variables from its enclosing scope even after the outer function has finished executing.
# ----------------------------------------------------------------------------------


# Where These Appear in Production Systems

    # Closures:
        # ✔ parameterized strategy builders
        # ✔ signal pipelines
        # ✔ callback factories
        # ✔ lazy evaluation
    # Decorators:
        # ✔ retry logic
        # ✔ caching layers
        # ✔ logging
        # ✔ timing
        # ✔ authentication
        # ✔ rate limiting
        # ✔ database session management


# ----------------------------------------------------------------------------------
# 1. Decorators
# A decorator is a function that wraps another function to extend its behavior.
# ----------------------------------------------------------------------------------

#Syntax:

@decorator
def function():

#Equivalent to:
function = decorator(function)

# Basic Decorator Example
#-----------------------------------------------------

# wrapper() is a closure capturing func
def my_decorator(func):
    def wrapper():
        print("Before execution")
        func()
        print("After execution")
    return wrapper

# Usage:
@my_decorator
def say_hello():
    print("Hello")

say_hello()


"""
>> say_hello()
Before execution
Hello
After execution
"""


# Decorators With Arguments
#-----------------------------------------------------

def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before execution")
        result = func(*args, **kwargs)
        print("After execution")
        return result
    return wrapper

@my_decorator
def add(a, b):
    return a + b

print(add(2, 3))

"""
>>> print(add(2, 3))
Before execution
After e
"""

# Why *args, **kwargs Matters
#     Without them:
#         TypeError
#     when decorating functions with parameters. This makes decorators generic and reusable.



# Decorators That Return Values
#-----------------------------------------------------

def timing(func):
    import time

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        print("Execution time:", end - start)
        return result

    return wrapper

@timing
def compute():
    sum(range(10_000_000))

compute()

# Decorators With Arguments (Decorator Factory)
#-----------------------------------------------------

# Sometimes decorators themselves take parameters.

def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                func(*args, **kwargs)
        return wrapper
    return decorator

@repeat(3)
def greet():
    print("Hello")

greet()

# decorator(arg)
#     → returns decorator
#         → returns wrapper

"""
>>> greet()
Hello
Hello
Hello
"""

###############################
# Real-World Decorator Examples
###############################

# Logging
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


# Authentication (Web APIs)
def require_auth(func):
    def wrapper(user):
        if not user.is_authenticated:
            raise PermissionError("Unauthorized")
        return func(user)
    return wrapper

## Built in decorators 
#----------------------------------------------


# 1. @property
# -------------------------------------------------------------
# Turns a method into a read-only attribute.

class Person:
    def __init__(self, age):
        self._age = age

    @property
    def age(self):
        return self._age


p = Person(25)
print(p.age)               # instead of p.age() # Useful for encapsulation

"""
>>> print(p.age)
25
"""


# 2. @<property>.setter
# -------------------------------------------------------------
# Allows controlled attribute updates.

class Person:
    def __init__(self, age):
        self._age = age

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, value):
        if value < 0:
            raise ValueError("Invalid age")
        self._age = value

p = Person(40)
p.age = 30


# 3. @staticmethod
# -------------------------------------------------------------
# Defines a method that does not depend on instance or class.

class MathUtils:

    @staticmethod
    def add(a, b):
        return a + b

print(MathUtils.add(2, 3))


"""
# >>> print(MathUtils.add(2, 3))
5
"""

# No self, no cls.
# Used for utility helpers




# 4. @classmethod
# -------------------------------------------------------------
# Receives the class instead of instance.
class Person:

    count = 0

    def __init__(self):
        Person.count += 1

    @classmethod
    def total(cls):
        return cls.count

print(Person.total())


# Common use cases:
    # ✔ factory methods
    # ✔ class-level counters
    # ✔ alternative constructors





# 5. @dataclass (from dataclasses)
# -------------------------------------------------------------
# Auto-generates:

# __init__
# __repr__
# __eq__
# others

from dataclasses import dataclass
@dataclass
class Point:
    x: int
    y: int


p = Point(1, 2)
print(p)

"""
>>> print(p)
Point(x=1, y=2)

"""
# Equivalent to writing lots of boilerplate manually



# 6. @abstractmethod (from abc)
# -------------------------------------------------------------
# For defining abstract base classes.

from abc import ABC, abstractmethod
class Shape(ABC):

    @abstractmethod
    def area(self):
        pass

# Subclass must implement:
    # area()

# Otherwise error raised. Used in interface-style design



# 7. @lru_cache() (from functools)
# -------------------------------------------------------------
# Caches function results automatically.

from functools import lru_cache

@lru_cache(maxsize=128)
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

print(fib(30))


# Huge performance boost ⚡
    # Great for:
        # recursion
        # pricing grids
        # repeated analytics calls



# 8. @wraps (from functools)
# -------------------------------------------------------------
# Preserves metadata inside decorators.

# Preserving Function Metadata
    # Decorators overwrite:
        # function name
        # docstring
        # signature
    # Fix using:

from functools import wraps

def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print("Calling function")
        return func(*args, **kwargs)
    return wrapper

# Keeps:
    # function name
    # docstring
    # signature
# Best practice



# 9. @total_ordering (from functools)
# -------------------------------------------------------------
# Auto-generates comparison operators.

from functools import total_ordering

@total_ordering
class Number:

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

# Now supports: >, <=, >= automatically




# 10. @singledispatch (from functools)
# -------------------------------------------------------------
# Function overloading based on argument type.

from functools import singledispatch

@singledispatch
def process(x):
    print("Default:", x)


@process.register(int)
def _(x):
    print("Integer:", x)

process(10)
process("hello")

"""
>>> process(10)
Integer: 10
>>> process("hello")
Default: hello

"""
# Useful for extensible APIs


# 11. @contextmanager (from contextlib)
# -------------------------------------------------------------
# Creates context managers easily.

from contextlib import contextmanager

@contextmanager
def timer():
    import time
    start = time.time()
    yield
    print("Elapsed:", time.time() - start)

with timer():
    sum(range(10_000_000))

# Cleaner than writing __enter__ / __exit__.


# 12. @cached_property (from functools, Python ≥3.8)
# -------------------------------------------------------------
# Computes value once and caches it.

from functools import cached_property

class Data:

    @cached_property
    def expensive(self):
        print("Computing...")
        return 42


d = Data()

print(d.expensive)
print(d.expensive)

# Runs only once


# Most Important Built-In Decorators (Quick Reference)
# ---------------------------------------------------------------------
# Decorator	                Purpose
# @property	                computed attribute
# @staticmethod	            utility method
# @classmethod	            class-level method
# @dataclass	            auto-generate class methods
# @abstractmethod	        enforce subclass implementation
# @lru_cache	            memoization
# @wraps	                preserve metadata
# @total_ordering	        auto comparisons
# @singledispatch	        function overloading
# @contextmanager	        create context managers
# @cached_property	        lazy cached attribute
