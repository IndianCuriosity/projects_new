# ###############################################################################################################
# The collections module in Python’s standard library provides specialized container datatypes beyond built-in types like list, dict, set, and tuple. These structures are optimized for performance, readability, and expressive code—especially useful in 
# data pipelines, analytics systems, and algorithmic workflows.


# Why Use collections?
    # They provide:
        # ✅ faster operations
        # ✅ cleaner intent
        # ✅ better defaults
        # ✅ specialized behaviors (queues, counters, ordered dicts, etc.)

# Import:
from collections import *           # (or import specific classes individually)

###############################################################################################################

# 1. Counter
# ---------------------------------------
# Counts occurrences of elements automatically.

from collections import Counter
data = ["A", "B", "A", "C", "B", "A"]
c = Counter(data)
print(c)

"""
>>> print(c)
Counter({'A': 3, 'B': 2, 'C': 1})
"""

c.most_common(1)        # Most common values:

"""
>>> c.most_common(1)        # Most common values:
[('A', 3)]
"""

# Useful for:
    # frequency analysis
    # factor exposure counts
    # signal voting systems


# 2. defaultdict
# ---------------------------------------
# Dictionary with automatic default values.

# Example without it:
d = {}

if "a" not in d:
    d["a"] = []

print (d)

"""
>>> print (d)
{'a': []}
"""

# Cleaner version:
from collections import defaultdict

d = defaultdict(list)
d["a"].append(10)
print(d)

"""
>>> print(d)
defaultdict(<class 'list'>, {'a': [10]})

"""

# Other defaults:
defaultdict(int)
defaultdict(set)
defaultdict(float)





# Common use: grouping data:
# Imagine you have a list of students and their grades, and you want to group all grades by student name. With a normal dict, you'd have to check 
# if name not in my_dict: my_dict[name] = [] every single time.

from collections import defaultdict
grades = [
    ('Alice', 90),
    ('Bob', 75),
    ('Alice', 85),
    ('Charlie', 92),
    ('Bob', 80)
]

# We tell it to use 'list' as the default factory
student_grades = defaultdict(list)

for name, score in grades:
    # If 'name' isn't there, it creates an empty list [] automatically
    student_grades[name].append(score)

print(dict(student_grades))

"""
>>> print(dict(student_grades))
{'Alice': [90, 85], 'Bob': [75, 80], 'Charlie': [92]}
"""


# Counting items:
# If you want to count how many times words appear in a list, you can use defaultdict(int). Since the default value of an integer in Python is 0, 
# you can start adding immediately.

words = ["apple", "banana", "apple", "cherry", "banana", "apple"]
word_counts = defaultdict(int)

for word in words:
    # No need to check if the word exists; it starts at 0
    word_counts[word] += 1

print(dict(word_counts))
# Output: {'apple': 3, 'banana': 2, 'cherry': 1}



# Building a "Nested" Dictionary
# You can even use defaultdict to create dictionaries that contain other dictionaries. This is useful for building tree-like structures 
# or complex maps.

# A dictionary where every new key is itself a dictionary
network_map = defaultdict(dict)

network_map['ServerA']['status'] = 'Active'
network_map['ServerA']['ip'] = '192.168.1.1'

print(network_map['ServerA'])
# Output: {'status': 'Active', 'ip': '192.168.1.1'}



# Feature,          Standard dict,                                  collections.defaultdict
# ---------------------------------------------------------------------------------------------------------------
# Missing Keys,     Raises KeyError.,                               Creates key with default value.
# Initialization,   Must manually check/set first value.,           Happens automatically on access.
# Readability,      Can get cluttered with if/else or .get().,      "Clean, concise ""intent-based"" code."

# Quick Tip: Remember that defaultdict only triggers that automatic creation when you access it using square brackets like d[key]. 
# If you use d.get(key), it will still return None (or your specified default) without creating the entry in the dictionary.




# 3. deque (Double-Ended Queue)
# ---------------------------------------
# Fast insert/remove from both ends.

from collections import deque
dq = deque([1, 2, 3])

dq.append(4)
dq.appendleft(0)

print(dq)

"""
>>> print(dq)
deque([0, 1, 2, 3, 4])
"""
# Remove items:
dq.pop()
dq.popleft()
dq

"""
>>> dq
deque([1, 2, 3])
"""

# Very efficient for:
    # rolling windows
    # streaming buffers
    # order book snapshots
    # sliding analytics

# Example rolling window:
dq = deque(maxlen=3)

for i in range(5):
    dq.append(i)
    print(dq)

"""
eque([0], maxlen=3)
deque([0, 1], maxlen=3)
deque([0, 1, 2], maxlen=3)
deque([1, 2, 3], maxlen=3)
deque([2, 3, 4], maxlen=3)

"""


# 4. namedtuple
# ---------------------------------------
# Tuple with named fields.

# Instead of:

point = (10, 20)
print(point[0])

# Use:
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(10, 20)

print(p.x)
print(p.y)

# Advantages:
    # ✔ readable
    # ✔ lightweight
    # ✔ immutable
    # ✔ faster than classes

# Used in:
    # market ticks
    # trade records
    # coordinates
    # configuration objects




# 5. OrderedDict
# ---------------------------------------
# Maintains insertion order (important historically; now built-in dict does too in Python ≥3.7).

from collections import OrderedDict
od = OrderedDict()

od["a"] = 1
od["b"] = 2

print(od)

"""
>>> print(od)
OrderedDict({'a': 1, 'b': 2})
"""

# Special feature: move elements:

od.move_to_end("a")

# Useful for:
    # LRU caches
    # priority tracking
    # execution ordering



# 6. ChainMap
# ---------------------------------------
# Combines multiple dictionaries into one logical view.

from collections import ChainMap
a = {"x": 1}
b = {"y": 2}

c = ChainMap(a, b)

print(c["x"])
print(c["y"])

"""
>>> print(c["x"])
1
>>> print(c["y"])
2
"""

# Common use: configuration layering:
    #  ChainMap(user_config, default_config)


# 7. UserDict, UserList, UserString
# ---------------------------------------
# Wrapper classes for customizing built-in containers safely. Used when subclassing dict/list/string behavior cleanly.

from collections import UserDict

class MyDict(UserDict):
    def __setitem__(self, key, value):
        print("Setting:", key)
        super().__setitem__(key, value)


# Quick Comparison Table

# | Type                   | Purpose                        |
# | ---------------------- | ------------------------------ |
# | `Counter`              | frequency counting             |
# | `defaultdict`          | automatic default values       |
# | `deque`                | fast queue/stack operations    |
# | `namedtuple`           | lightweight structured records |
# | `OrderedDict`          | ordered dictionary control     |
# | `ChainMap`             | merge multiple dicts logically |
# | `UserDict/List/String` | safe container subclassing     |


# Most Useful Ones in Data / Quant Workflows
    # These appear constantly in production code:

# ⭐ Counter → signal frequency / feature stats
# ⭐ defaultdict → grouping pipelines
# ⭐ deque → rolling windows / streaming buffers
# ⭐ namedtuple → tick/trade structures
# ⭐ ChainMap → layered configs


# Example (realistic streaming window pattern): Efficient rolling average without copying data.

from collections import deque
window = deque(maxlen=5)
for price in [10, 11, 12, 13, 14, 15]:
    window.append(price)
    print(sum(window) / len(window))
