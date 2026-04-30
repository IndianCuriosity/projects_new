##########################################################################################################################################

# Python is not a purely functional language (like Haskell), but it supports several functional programming (FP) patterns that help write cleaner, 
# composable, and memory-efficient code—especially useful in data pipelines, analytics workflows, and strategy transformations.
##########################################################################################################################################




# 1. Lambda Functions
#-----------------------------------
# A lambda is a small anonymous function defined in one line.

# lambda arguments: expression
square = lambda x: x * x
print(square(5))

"""
>>> print(square(5))
25
"""
def square(x):                            # Equivalent normal function:
    return x * x

# Common Uses

# ✔ quick transformations
# ✔ sorting keys
# ✔ map/filter operations
# ✔ inline callbacks

nums = [5, 2, 9, 1]
sorted_nums = sorted(nums, key=lambda x: x)
print(sorted_nums)

"""
>> print(sorted_nums)
[1, 2, 5, 9]
"""




# 2. map()
#-----------------------------------
# Applies a function to every element of an iterable.

nums = [1, 2, 3, 4]
result = map(lambda x: x * 2, nums)
print(list(result))

"""
>>> print(list(result))
[2, 4, 6, 8]
"""

[x * 2 for x in nums]                   # Equivalent list comprehension: Usually preferred in modern Python.




# 3. filter()
#-----------------------------------
# Selects elements that satisfy a condition.

nums = [1, 2, 3, 4, 5]
result = filter(lambda x: x % 2 == 0, nums)
print(list(result))


"""
>>> print(list(result))
[2, 4]

"""
[x for x in nums if x % 2 == 0]         # Equivalent comprehension:






# 4. functools.reduce()
#-----------------------------------
# Applies a function cumulatively across elements.

# Example: Sum
from functools import reduce
nums = [1, 2, 3, 4]
result = reduce(lambda a, b: a + b, nums)
print(result)

"""
>>> print(result)
10
"""

# Step-by-step: ((1+2)+3)+4


# Example: Product
from functools import reduce
nums = [1, 2, 3, 4]
result = reduce(lambda a, b: a * b, nums)
print(result)

"""
>> print(result)
24
"""

# Useful for:
    # ✔ aggregations
    # ✔ rolling transformations
    # ✔ combining signals


# 5. functools.partial()
#-----------------------------------
# Creates a new function with some arguments pre-filled. Very powerful for pipelines and configuration-driven workflows.

# Example
from functools import partial
def power(base, exponent):
    return base ** exponent

square = partial(power, exponent=2)
print(square(5))

"""
>>> print(square(5))
25
"""
# Equivalent to: lambda x: power(x, exponent=2)



# Another Example
from functools import partial
def multiply(a, b):
    return a * b

double = partial(multiply, 2)
print(double(10))

"""
>> print(double(10))
20
"""

# Useful when:
    # ✔ fixing parameters in strategy builders
    # ✔ customizing scoring functions
    # ✔ preconfiguring APIs




# 6. sorted() with Functional Style
#-----------------------------------
# sorted() accepts a function as a key.

words = ["apple", "banana", "kiwi"]
result = sorted(words, key=lambda x: len(x))
print(result)

"""
>>> print(result)
['kiwi', 'apple', 'banana']
"""


# Sort by second element:
pairs = [(1, 3), (4, 1), (2, 2)]
print(sorted(pairs, key=lambda x: x[1]))

"""
>>> print(sorted(pairs, key=lambda x: x[1]))
[(4, 1), (2, 2), (1, 3)]
"""

# Why Functional Tools Matter in Real Systems
    # These patterns enable:
        # ✔ transformation pipelines
        # ✔ stateless processing
        # ✔ composability
        # ✔ lazy evaluation
        # ✔ cleaner parallelization


# Example pipeline:
from functools import reduce
nums = [1, 2, 3, 4, 5]
result = reduce(
    lambda acc, x: acc + x,
    filter(lambda x: x % 2 == 0,
           map(lambda x: x * x, nums))
)

print(result)

"""
>>> print(result)
20
"""
# Equivalent logic: square numbers → keep even → sum them


# Functional vs Pythonic Alternative (Best Practice)
# Modern Python prefers:
    # list comprehensions
    # generator expressions
    # built-in functions
# Instead of:
    # map + filter chains

sum(x*x for x in nums if x % 2 == 0)                    # Cleaner and faster.

# Mental Model Summary:

# Tool	                    Purpose
# --------------------------------------------------------
# lambda	                inline anonymous function
# map	                    transform iterable
# filter	                select elements
# reduce	                aggregate values
# partial	                freeze arguments
# sorted(key=...)	        custom ordering logic