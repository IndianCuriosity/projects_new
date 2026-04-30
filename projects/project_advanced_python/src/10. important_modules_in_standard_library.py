
##########################################################################################################################################################
# Python’s standard library is large, but a core subset appears repeatedly in data engineering, quant research, APIs, automation, and production systems. 
# Below is a structured guide to the most important modules, grouped by purpose, with examples and when to use them.

# 1. System & Runtime Modules
# -------------------------------------------------------
# sys
# os
# platform

# 2. File & Path Handling
# -------------------------------------------------------
# pathlib ⭐ (modern replacement for os.path)
# shutil

# 3. Data Structures
# -------------------------------------------------------
# collections                         # Provides specialized container datatypes like namedtuple, deque, and Counter
# heapq                               # Implements the "min-heap" algorithm. This is perfect for creating priority queues where 
#                                     # you always need quick access to the smallest element.
# array                               # Provides a space-efficient way to store basic values (integers, floats) when you have millions of items and 
#                                     # want to save memory compared to a standard list.
# bisect                              # Keeps a list in sorted order without having to re-sort it every time you insert an item. It uses binary search internally.

# 4. Iteration Utilities
# -------------------------------------------------------
# itertools                           # Functions for creating efficient loops and combinations (very powerful for data processing).

# 5. Functional Programming & Persistence
# -------------------------------------------------------
# functools
#     Includes:

#         lru_cache
#         partial
#         reduce
#         wraps
#         singledispatch
# sqlite3
# copy


# 6. Dates & Time
# -------------------------------------------------------
# datetime
# time

# 7. Math & Statistics
# -------------------------------------------------------
# math
# statistics
# random

# 8. Serialization & Persistence
# -------------------------------------------------------
# json
# pickle
# csv

# 9. Concurrency & Parallelism
# -------------------------------------------------------
# threading
# multiprocessing
# concurrent.futures      # Simplifies threading/multiprocessing.
# asyncio

# 10. Networking & Web
# -------------------------------------------------------
# urllib                  # A package for opening and reading URLs.
# http.server             # A quick way to spin up a local web server for testing (e.g., python -m http.server).
# socket                  # Low-level networking interface for advanced "pipe" communications.

# 11. Debugging & Inspection
# -------------------------------------------------------
# inspect                                 # A powerful "introspection" tool. It can look at live objects and tell you their source code, what arguments
#                                         # a function takes, or what's inside a class.
# logging
# traceback

# 12. Memory & Performance
# -------------------------------------------------------
# gc
# tracemalloc
# sys.getsizeof

# 13. Temporary Resources
# -------------------------------------------------------
# tempfile

# 14. Configuration & CLI, interaction, automation
# -------------------------------------------------------
# argparse
# configparser
# subprocess:                                       # Allows you to run other programs on your computer (like git or ls) and capture thei
#                                                    output directly into your Python script.

# 15. Object-Oriented Utilities
# -------------------------------------------------------
# abc
# dataclasses

# 16. Context Management
# -------------------------------------------------------
# contextlib

# 17. Testing
# -------------------------------------------------------
# unittest

# 18. Compression
# -------------------------------------------------------
# zipfile / tarfile

# 19. Others
# -------------------------------------------------------
# re :                      The engine for Regular Expressions, used for complex string searching and pattern matching.
# locale:                    Handles cultural preferences like currency symbols, decimal points (, vs .), and date formats based on the user's country.
# importlib:                    Allows you to dynamically import modules while the code is running—very useful for plugin-based architectures.


# | Area                    | Modules                                           |
# | ----------------------- | ------------------------------------------------- |
# | Regex / text            | `re`, `string`, `textwrap`, `difflib`             |
# | Compression / archives  | `gzip`, `zipfile`, `tarfile`, `bz2`, `lzma`       |
# | Hashing / security      | `hashlib`, `hmac`, `secrets`, `ssl`               |
# | Subprocess / automation | `subprocess`, `sched`, `signal`                   |
# | Import / plugins        | `importlib`, `pkgutil`                            |
# | Types / typing          | `typing`, `types`, `enum`                         |
# | Data formats            | `xml`, `html`, `email`, `base64`                  |
# | Queues / IPC            | `queue`, `socket`, `selectors`                    |
# | Testing / mocking       | `doctest`, `unittest.mock`                        |
# | Profiling               | `cProfile`, `pstats`, `timeit`                    |
# | Weak references         | `weakref`                                         |
# | Copying                 | `copy`                                            |
# | Binary data             | `struct`, `array`, `mmap`                         |
# | Fractions / precision   | `decimal`, `fractions`                            |
# | UUIDs                   | `uuid`                                            |
# | Time zones              | `zoneinfo`                                        |
# | Distribution metadata   | `venv`, `site`, `sysconfig`, `importlib.metadata` |

# Most useful additions for your Quant Tech preparation:
# re
# subprocess
# typing
# enum
# timeit
# cProfile
# copy
# weakref
# queue
# socket
# struct
# mmap
# decimal
# zoneinfo
# importlib
# unittest.mock


# Especially important for production systems:

# typing → type-safe large codebases
# logging → already covered, but very important
# subprocess → batch scripts / external tools
# timeit, cProfile → performance tuning
# queue, socket, selectors → streaming / networking
# struct, mmap → binary/high-performance data handling
# importlib → plugin/strategy loading
# unittest.mock → testing external APIs without hitting real services













############################################################################################################################################################
