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