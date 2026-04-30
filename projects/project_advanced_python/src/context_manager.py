

####################################################################################################################################################
# https://realpython.com/python-with-statement/
# https://book.pythontips.com/en/latest/context_managers.html#:~:text=Context%20managers%20allow%20you%20to,Context%20Manager%20as%20a%20Class:


# A context manager in Python is a construct that automatically sets up and cleans up resources around a block of code. It’s most commonly used with the with statement.
    # Typical use cases:
        # file handling 📄
        # database connections 🗄️
        # locks in multithreading 🔒
        # network sessions 🌐
        # temporary settings/environment changes ⚙️

# Python’s with statement automates the process of setting up and tearing down computational resources using context managers.
# Using with reduces code complexity and prevents resource leaks (memory leaks) by ensuring proper resource release, even if exceptions occur.
# A context manager in Python is an object that implements .__enter__() and .__exit__() methods to manage resources safely.
# Python’s with statement and context managers streamline the setup and teardown phases of resource management so you can write safer, more reliable code.

# The Python with statement creates a runtime context that allows you to execute a code block under the control of a context manager
# with statement to make it possible to factor out common use cases of the try … finally construct.

# Compared to the traditional try … finally construct, the with statement makes your code clearer, safer, and more readable. Many classes and objects in the standard 
# library support the with statement by implementing the context manager protocol (special methods).

# This with construct is shorter than its try … finally equivalent construct, but it’s also less generic because you can only use the with statement with objects that 
# support the context management protocol. In contrast, try … finally allows you to perform cleanup actions for any object, even if it doesn’t implement the 
# context management protocol.

# The with statement can make the code that deals with system resources more readable, concise, and safer. It helps avoid resource leaks by making it almost impossible to 
# forget to clean up, close, and release resources after you’re done with them. Using with allows you to abstract away most of the resource handling logic. Instead of 
# using explicit try … finally constructs with setup and teardown logic, you can pack this logic into a context manager and handle it using the with statement to avoid 
# repetition.

# Built-in Context Managers in standard library

# with open(...)
# with threading.Lock()
# with multiprocessing.Pool()
# with requests.Session()
# with tempfile.TemporaryDirectory()
# with pathlib.Path.open()
# with sqlite3.connect()
# with contextlib.suppress()
# with contextlib.redirect_stdout()
# with contextlib.ExitStack()



# What the with Statement Does
    #     The with statement lets Python automatically handle setup and cleanup of resources (files, locks, sockets, connections, etc.). 
    #     It works with objects that implement the context manager protocol (__enter__() and __exit__()).

    # Equivalent idea:

    #     resource = acquire()
    #     try:
    #         use(resource)
    #     finally:
    #         release(resource)

    # Becomes:

    #     with resource:
    #         use(resource)

##################################################################################################################################################

class HelloContextManager:
     def __enter__(self):
         print("Entering the context...")
         return "Hello, World!"
     def __exit__(self, exc_type, exc_value, exc_tb):
         print("Leaving the context...")


with HelloContextManager() as hello:
    print(hello)

"""
Entering the context...
Hello, World!
Leaving the context...
"""

# Why It Exists (Problem It Solves)

    # Programs often forget cleanup steps like:
        # closing files
        # releasing locks
        # closing network connections

    # This causes resource leaks (memory, descriptors, bandwidth).
        # The with statement guarantees cleanup even if exceptions occur.

# Why Context Managers Matter (Especially in Quant/Infra Code)

    # They guarantee:
        # ✔ deterministic cleanup
        # ✔ safer concurrency
        # ✔ no resource leaks
        # ✔ cleaner syntax
        # ✔ exception-safe execution
    # In production trading systems they’re widely used for:
        # DB sessions
        # file streams
        # sockets
        # GPU contexts
        # cache locks
        # market data connections

# Python’s standard library includes many built-in context managers that automatically handle setup/cleanup of resources such as files, locks, 
# processes, temporary objects, warnings filters, and more. Here’s a structured reference you can use in practice (especially useful for production-grade
# data/quant infrastructure code).

# Key Advantages of with

#     According to the article:

#     ✔ safer resource handling
#     ✔ shorter code than try/finally
#     ✔ prevents leaks
#     ✔ improves readability
#     ✔ supports multiple managers in one statement






# ------------------------------------------
# 1. File & I/O Context Managers
# ------------------------------------------


# open()
with open("data.txt", "r") as f:
    data = f.read()

# Used for in-memory streams.
from io import StringIO
with StringIO() as buffer:
    buffer.write("hello")

# ------------------------------------------
# 2. Threading & Synchronization
# ------------------------------------------

# threading.Lock()
import threading
lock = threading.Lock()
with lock:                              # Auto acquire + release.
    print("Critical section")

# threading.RLock()
with threading.RLock():                 # Reentrant lock.
    pass


# threading.Condition()
cond = threading.Condition()            # Used for signaling between threads.
with cond:
    cond.wait()


# threading.Semaphore()
from threading import Semaphore
sem = Semaphore(2)
with sem:                               # Limits concurrency.
    print("Limited access resource")



# ------------------------------------------
# 3. Multiprocessing Context Managers
# ------------------------------------------

# multiprocessing.Pool
from multiprocessing import Pool

with Pool(4) as pool:                   # Automatically terminates workers.
    pool.map(print, [1, 2, 3])

# multiprocessing.Lock
from multiprocessing import Lock

lock = Lock()

with lock:                              # Process-safe locking.
    pass


# ------------------------------------------
# 4. Temporary Files & Directories
# ------------------------------------------

# tempfile.TemporaryFile
import tempfile

with tempfile.TemporaryFile() as f:     # Auto-deleted after use.
    f.write(b"hello")

# tempfile.NamedTemporaryFile

with tempfile.NamedTemporaryFile() as f: # Visible filename + auto cleanup.
    print(f.name)


# tempfile.TemporaryDirectory
with tempfile.TemporaryDirectory() as tmpdir:   # Directory removed automatically.
    print(tmpdir)



# ------------------------------------------
# 5. Database & Network Sessions
# ------------------------------------------

# sqlite3.connect
import sqlite3

with sqlite3.connect("db.sqlite") as conn:  # Commits or rolls back automatically.
    conn.execute("SELECT 1")


# socket.socket
import socket

with socket.socket() as s:                  # Socket closes automatically.
    s.connect(("example.com", 80))

# ------------------------------------------
# 6. Contextlib Utilities (Very Important): 
# The contextlib module provides advanced helpers.
# ------------------------------------------


# contextlib.closing() : Wrap objects that only support .close()
from contextlib import closing
import urllib.request

with closing(urllib.request.urlopen("http://example.com")) as page:
    print(page.read())



# contextlib.suppress() : Ignore specific exceptions
from contextlib import suppress

with suppress(FileNotFoundError):       # Cleaner than try/except.
    open("missing.txt")



# contextlib.redirect_stdout()
from contextlib import redirect_stdout
import io

buffer = io.StringIO()
with redirect_stdout(buffer):           # Useful for logging/testing.
    print("Hello")

print(buffer.getvalue())


# contextlib.ExitStack() ⭐ advanced
from contextlib import ExitStack

with ExitStack() as stack:              # Extremely useful in production pipelines.
    f1 = stack.enter_context(open("a.txt"))
    f2 = stack.enter_context(open("b.txt"))


# ------------------------------------------
# 7. Decimal Precision Control
# ------------------------------------------

# decimal.localcontext()
from decimal import Decimal, localcontext

with localcontext() as ctx:             # Temporary precision override.
    ctx.prec = 4
    print(Decimal("1") / Decimal("7"))


# ------------------------------------------
8. Warnings Control
# ------------------------------------------

warnings.catch_warnings()
import warnings

with warnings.catch_warnings():         # Suppress warnings temporarily.
    warnings.simplefilter("ignore")

# ------------------------------------------
# Creating Function-Based Context Managers

# 9. Environment Variable Override
# ------------------------------------------

# os.environ via contextlib ( (Not built-in directly, but commonly wrapped))
import os
from contextlib import contextmanager

@contextmanager
def temp_env(key, value):
    old = os.environ.get(key)
    os.environ[key] = value
    yield
    if old:
        os.environ[key] = old


# ------------------------------------------
# Creating Class-Based Context Managers
# -------------------------------------
# -----
class DemoContextManager:
    def __enter__(self):
        print("Entering context")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting context")

with DemoContextManager():
    print("Inside block")

# ------------------------------------------
# 10. Async Context Managers (Standard Library) ( Used with async with)
# ------------------------------------------

# asyncio.Lock 
import asyncio

lock = asyncio.Lock()

async with lock:
    pass


# asyncio.Semaphore
sem = asyncio.Semaphore(3)

async with sem:
    pass