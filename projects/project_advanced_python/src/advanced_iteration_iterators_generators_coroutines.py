###############################################################################################################
# https://realpython.com/python-iterators-iterables/#creating-generator-iterators

# Iterators and Iterables in Python: Run Efficient Iterations

    # Python iterators are objects with .__iter__() and .__next__() methods.
    # Iterables are objects that can return an iterator using the .__iter__() method.
    # Generator functions use the yield statement to create generator iterators.
    # Asynchronous iterators use .__aiter__() and .__anext__() for async operations.
    # Iterators are memory-efficient and can handle infinite data streams.

# In Python, an iterator is an object that allows you to iterate over collections of data, such as lists, tuples, dictionaries, and sets.
# Python iterators must implement a well-established internal structure known as the iterator protocol. In the following section, you’ll learn the basics 
# of this protocol.

# Iterators and generators are core Python mechanisms for lazy evaluation, memory efficiency, and streaming computation—widely used in data pipelines, 
# backtesting engines, and async-style workflows.
    
###############################################################################################################


# 1.Iterator
#----------------------------

# An iterator is an object that:
    #     Keeps track of state
    #     Returns the next item when requested
    #     Raises StopIteration when finished


# It implements two methods:

#     __iter__()
#     __next__()

nums = [1, 2, 3]

it = iter(nums)

print(next(it))
print(next(it))
print(next(it))
print(next(it))

"""
>>> print(next(it))
1
>>> print(next(it))
2
>>> print(next(it))
3
>>> print(next(it))
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
StopIteration
"""

# Iterator Protocol (Important Concept)
    # An object is iterable if:
    # __iter__()
    # returns an iterator

    # An object is an iterator if:
    # __iter__()
    # __next__()
    # are both implemented.

class Counter:

    def __init__(self, max_value):
        self.max = max_value
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.max:
            raise StopIteration
        self.current += 1
        return self.current

c = Counter(3)
for num in c:
    print(num)

"""
>>> for num in c:
...     print(num)
... 
1
2
3
"""

# Why Iterators Matter
    #     They enable:

    #     ✔ streaming data
    #     ✔ memory-efficient loops
    #     ✔ infinite sequences
    #     ✔ large dataset processing


# 1.Generators
#----------------------------

    # A generator is a simpler way to create iterators using yield.
    # Cleaner than writing iterator classes
# Instead of __next__()
    # you write :
    #     yield value

def counter(n):
    for i in range(n):
        yield i

for x in counter(3):
    print(x)

"""
>>> for x in counter(3):
...     print(x)
... 
0
1
2
"""

# How yield Works
# ----------------------------------
# Normal function
def f():
    return 10

# Generator:
def g():
    yield 10

# Difference:
# f() → returns value
# g() → returns generator object

gen = g()

print(next(gen))

# Generator State Persistence
# -------------------------------

def example():
    print("Start")
    yield 1
    print("Middle")
    yield 2
    print("End")

g = example()

next(g)
next(g)
next(g)

"""
>> g = example()
>>> next(g)
Start
1
>>> next(g)
Middle
2
>>> next(g)
End
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
StopIteration
"""

# Execution pauses after each yield.

# Generator Expression (Like List Comprehension)
# -----------------------------------------------------

#List comprehension:
[x*x for x in range(5)]

# Generator expression:
(x*x for x in range(5))

# Example:
gen = (x*x for x in range(5))
for val in gen:
    print(val)

# Uses almost zero memory

# Iterator vs Generator
# -----------------------------------------
# Feature	                        Iterator            	Generator
# -----------------------------------------------------------------------------
# Requires class	                Yes	                    No
# Uses yield	                    No	                    Yes
# Easier syntax	                    ❌	                   ✅
# Memory efficient	                ✅	                   ✅
# Stores state automatically    	❌	                   ✅

# Generators are just automatic iterators.

# Infinite Generators
# ---------------------------------

        # Useful for streaming pipelines

def infinite_numbers():
    n = 0
    while True:
        yield n
        n += 1

gen = infinite_numbers()

print(next(gen))
print(next(gen))
print(next(gen))

# Runs forever unless stopped.

# Real Example: File Streaming (Memory Efficient)
# ----------------------------------------------------------

# Bad approach:

lines = open("data.txt").readlines()

#Better: with context manager
with open("data.txt") as f:
    for line in f:
        print(line)

#Best (explicit generator): with context manager & generator
def read_large_file(file):
    with open(file) as f:
        for line in f:
            yield line


# Generator Pipeline Example (Production Pattern)
# ----------------------------------------------------------
def read_data():
    for i in range(5):
        yield i

def square(data):
    for x in data:
        yield x*x

def filter_even(data):
    for x in data:
        if x % 2 == 0:
            yield x

#Pipeline:

result = filter_even(square(read_data()))

for r in result:
    print(r)

# Memory-efficient transformation chain ⚡


# yield from (Advanced Generator Feature)
# ------------------------------------------------------
# Delegates iteration:
def subgen():
    yield 1
    yield 2

def main():
    yield from subgen()
    yield 3

# Usage:

for x in main():
    print(x)

"""
>>> for x in main():
...     print(x)
... 
1
2
3
"""


# Coroutines
# Sending Values Into Generators (Advanced)
# https://book.pythontips.com/en/latest/coroutines.html

# Coroutines are similar to generators with a few differences. The main differences are:

# generators are data producers
# coroutines are data consumers



# -------------------------------------------------------
# Generators can receive input:
def echo():
    while True:
        value = yield
        print("Received:", value)


# Usage:
g = echo()

next(g) # It is required in order to start the coroutine.
g.send(10)
g.send(20)

# Used in coroutine-style workflows.





# When Generators Are Used in Real Systems
    # Very common in:

        # ✔ streaming market data
        # ✔ log processing
        # ✔ backtesting pipelines
        # ✔ Monte Carlo simulations
        # ✔ large CSV readers
        # ✔ API pagination


# Example pattern: Consumes data lazily as it arrives
# --------------------------------------------------------
def market_ticks():
    while True:
        yield get_next_tick()


# Mental Model Summary

    # Iterator:
        # object that produces values one at a time

    # Generator:
        # function that produces values one at a time

    # Both enable:

        # ✔ lazy execution
        # ✔ memory efficiency
        # ✔ composable pipelines
        # ✔ scalable data processing
