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


# Caching ( Built-in decorator:)
from functools import lru_cache

@lru_cache(maxsize=128)
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)


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
        return func(*args, **kwargs)
    return wrapper


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
