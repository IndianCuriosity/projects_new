# ###############################################################################################################

# The queue module in Python’s standard library provides thread-safe queues for exchanging data between threads safely and efficiently. 
# It’s widely used in producer–consumer pipelines, task schedulers, streaming systems, and multi-threaded data ingestion workflows.


# Why Use queue?
    # Unlike a normal list:
        # shared_list.append(x)
        # shared_list.pop(0)
    # a queue.Queue:

        # ✅ is thread-safe
        # ✅ prevents race conditions
        # ✅ supports blocking reads/writes
        # ✅ supports task coordination


###############################################################################################################

# Types of Queues in queue Module

# | Class           | Behavior           | Use Case                  |
# | --------------- | ------------------ | ------------------------- |
# | `Queue`         | FIFO               | standard pipelines        |
# | `LifoQueue`     | stack (LIFO)       | DFS-style processing      |
# | `PriorityQueue` | sorted by priority | schedulers                |
# | `SimpleQueue`   | lightweight FIFO   | high-throughput streaming |



# 1. FIFO Queue (Queue)
# --------------------------------
# Standard queue: Order preserved (First-In-First-Out).

from queue import Queue
q = Queue()

q.put(1)
q.put(2)

print(q.get())
print(q.get())

"""
>> print(q.get())
1
>>> print(q.get())
2
"""


# 2. Queue in Multithreading (Producer–Consumer Pattern)
# --------------------------------
# Classic real-world example


from queue import Queue
from threading import Thread
import time


def producer(q):
    for i in range(5):
        print("Producing", i)
        q.put(i)
        time.sleep(1)


def consumer(q):
    while True:
        item = q.get()
        print("Consuming", item)
        q.task_done()


q = Queue()

Thread(target=consumer, args=(q,), daemon=True).start()
producer(q)

q.join()

# Used in:
    # data ingestion pipelines 📊
    # log processors
    # background workers
    # task schedulers



# 3. LIFO Queue (LifoQueue)
# --------------------------------
# Acts like a stack:

from queue import LifoQueue
q = LifoQueue()

q.put(1)
q.put(2)

print(q.get())
print(q.get())

"""
>>> print(q.get())
2
>>> print(q.get())
1
"""

# 4. Priority Queue (PriorityQueue)
# --------------------------------
# Processes lowest-priority value first:

from queue import PriorityQueue

q = PriorityQueue()

q.put((2, "task2"))
q.put((1, "task1"))

print(q.get())

"""
>>> print(q.get())
(1, 'task1')
"""

# Useful for:
    # execution engines
    # scheduling systems
    # event simulators
    # order routing priority



# 5. SimpleQueue (Fast Lightweight Version)
# --------------------------------
# No size tracking, faster than Queue:

from queue import SimpleQueue

q = SimpleQueue()

q.put(10)
print(q.get())              # Best for: high-throughput producer/consumer streaming

"""
>> print(q.get())
10
"""


# Blocking Behavior (Key Feature)
# --------------------------------
# Queues can block threads automatically.

# Example: Waits until data arrives.
q.get()


# Example: Non-blocking version:
q.get(block=False)

# Timeout example:
q.get(timeout=2)



# Limiting Queue Size (Backpressure Control)
# --------------------------------
# Now producer pauses if queue is full.

q = Queue(maxsize=3)

# Useful for:

    # streaming pipelines
    # market data buffers
    # rate control systems


# Task Completion Tracking
# --------------------------------
# Example

q.task_done()
q.join()

# Pattern:

# producer → q.put()                    # Ensures all tasks finish before program exits.
# consumer → q.get()
# consumer → q.task_done()
# main thread → q.join()


# Queue vs collections.deque
# --------------------------------
# | Feature                  | Queue | deque |
# | ------------------------ | ----- | ----- |
# | Thread-safe              | ✅     | ❌     |
# | Blocking support         | ✅     | ❌     |
# | Faster single-thread ops | ❌     | ✅     |
# | Multithreading pipelines | ✅     | ❌     |


# Rule of thumb:
    # deque → single-thread streaming
    # Queue → multi-thread pipelines



# Example: Streaming Rolling Processor
# --------------------------------
# Typical analytics-style workflow:

from queue import Queue
from threading import Thread


def worker(q):
    while True:
        price = q.get()
        print("Processing price:", price)
        q.task_done()


q = Queue()

Thread(target=worker, args=(q,), daemon=True).start()

for price in [100, 101, 102]:
    q.put(price)

q.join()

"""
Processing price: 100
Processing price: 101
>>> q.join()
Processing price: 102

"""

# Used in:
    # tick processing engines 📈
    # signal pipelines
    # event-driven backtesting
    # execution handlers



# queue vs multiprocessing.Queue
# --------------------------------
# Important distinction:

# | Module                  | Use Case              |
# | ----------------------- | --------------------- |
# | `queue.Queue`           | thread communication  |
# | `multiprocessing.Queue` | process communication |

# thread ↔ thread → queue.Queue
# process ↔ process → multiprocessing.Queue


# Mental Model Summary
# --------------------------------
# Queue → thread-safe pipeline buffer
# LifoQueue → stack-style processing
# PriorityQueue → scheduler ordering
# SimpleQueue → fast streaming FIFO
