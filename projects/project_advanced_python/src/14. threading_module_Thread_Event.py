##########################################################################################################
# In Python, an Event (from the threading module) is a synchronization primitive used to coordinate communication between threads. 
# It lets one thread signal one or more other threads that something has happened.

# Think of it as a shared flag:
# Very useful in producer–consumer systems, streaming pipelines, execution engines, and graceful shutdown control.


# What is threading.Event?
    # An Event object manages an internal boolean flag:
        # set() → flag becomes True
        # clear() → flag becomes False
        # wait() → blocks until True
        # is_set() → checks flag status

##########################################################################################################


from threading import Thread, Event
import time

event = Event()

def waiter():
    print("Waiting for event...")
    event.wait()
    print("Event received!")


Thread(target=waiter).start()

time.sleep(2)
event.set()

# Thread pauses until the event is triggered.

"""
Waiting for event...
>>> time.sleep(2)
>>> event.set()
Event received!
"""

# Core Methods
# -----------------------------------

event.set()             # Signals all waiting threads:
event.wait()            # Blocks execution until event becomes True:
event.wait(timeout=3)   # Optional timeout:
event.clear()           # Resets event flag:Threads will block again afterward.
event.is_set()          # Check flag status: True or False


# Example: Thread Coordination
# -----------------------------------
# Used when multiple workers must start together

from threading import Thread, Event
import time

start_event = Event()


def worker():
    print("Worker waiting...")
    start_event.wait()
    print("Worker started!")


Thread(target=worker).start()

time.sleep(2)
print("Triggering start")
start_event.set()

"""
>>> Thread(target=worker).start()
Worker waiting...
>>> time.sleep(2)
>>> print("Triggering start")
Triggering start
>>> start_event.set()
Worker started!
"""


# Example: Graceful Shutdown Signal (Production Pattern)
# -----------------------------------
# Very common in pipelines and streaming systems.

from threading import Thread, Event
import time

stop_event = Event()


def worker():
    while not stop_event.is_set():
        print("Working...")
        time.sleep(1)

    print("Stopping worker")


Thread(target=worker).start()

time.sleep(3)
stop_event.set()

# Clean shutdown without killing threads abruptly.

"""
>>> Thread(target=worker).start()
Working...
>>> time.sleep(3)
Working...
Working...
>>> stop_event.set()
Working...
>>> Stopping worker

"""


# Event vs Lock vs Queue
# -------------------------------------

    # | Tool    | Purpose                 |
    # | ------- | ----------------------- |
    # | `Event` | signal threads          |
    # | `Lock`  | protect shared resource |
    # | `Queue` | transfer data safely    |


# Example mental model:
    # Lock   → exclusive access
    # Queue  → data pipeline
    # Event  → notification trigger


# Event with Multiple Threads
# -----------------------------------------------
# One event can wake many waiting threads:

from threading import Thread, Event
import time

event = Event()

def worker(n):
    print(f"Worker {n} waiting")
    event.wait()
    print(f"Worker {n} started")


for i in range(3):
    Thread(target=worker, args=(i,)).start()

time.sleep(2)
event.set()


"""
>>> for i in range(3):
...     Thread(target=worker, args=(i,)).start()
... 
Worker 0 waiting
Worker 1 waiting
Worker 2 waiting
>>> time.sleep(2)
>>> event.set()
Worker 0 started
Worker 1 started
>>> Worker 2 started

"""

# Broadcast-style signaling


# Event vs Condition Variable
# ---------------------------------------------

# | Feature                 | Event | Condition |
# | ----------------------- | ----- | --------- |
# | Simple signaling        | ✅     | ❌         |
# | Multiple states         | ❌     | ✅         |
# | Producer–consumer logic | ❌     | ✅         |
# | Lightweight             | ✅     | ❌         |

# Event → simple trigger
# Condition → complex coordination


# Async Version: asyncio.Event
# ---------------------------------------------
# For async programs:

import asyncio

event = asyncio.Event()


async def waiter():
    print("Waiting...")
    await event.wait()
    print("Done")


async def main():
    asyncio.create_task(waiter())
    await asyncio.sleep(2)
    event.set()


asyncio.run(main())

"""
>>> asyncio.run(main())
Waiting...
Done
"""
# Same concept, async-compatible





# Real Use Cases in Quant / Data Systems
    # Events commonly control:

        # ✔ market data stream start/stop
        # ✔ strategy activation triggers
        # ✔ risk-limit shutdown switches
        # ✔ execution throttling signals
        # ✔ pipeline stage synchronization
        # ✔ simulation phase transitions

    # Example pattern:
        # market_open_event.wait()
        # start_trading()


# Mental Model Summary
# ------------------------------------
    # Event = shared boolean signal between threads
        # set()     → allow execution
        # wait()    → block execution
        # clear()   → reset signal
        # is_set()  → check signal
