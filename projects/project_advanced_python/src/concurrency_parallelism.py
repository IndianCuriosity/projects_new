

# https://realpython.com/python-concurrency/

##########################################################################################################################################

# Python Module     	CPU	                Multitasking	            Switching Decision
# asyncio	            One	                Cooperative	                The tasks decide when to give up control.
# threading	            One	                Preemptive	                The operating system decides when to switch tasks external to Python.
# multiprocessing	    Many	            Preemptive	                The processes all run at the same time on different processors.

# Both threading and multiprocessing represent fairly low-level building blocks in concurrent programs. 
# In practice, you can often replace them with concurrent.futures, which provides a higher-level interface for both modules. 

# On the other hand, asyncio offers a bit of a different approach to concurrency, which you’ll dive into later.


##########################################################################################################################################



#######################################################
# Synchronous Version:
#---------------------------------------------------------------------------------
# There’s only one train of thought running through it, so you can predict what the next step is and how it’ll behave.
#######################################################

import time

import requests

    # using a session object from requests. It’s possible to call requests.get() directly, but creating a Session object allows the library to retain state 
    # across requests and reuse the connection to speed things up.
def download_all_sites(sites):
    with requests.Session() as session:
        for url in sites:
            download_site(url, session)

def download_site(url, session):
    with session.get(url) as response:
        print(f"Read {len(response.content)} bytes from {url}")

def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.perf_counter()
    download_all_sites(sites)
    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration} seconds")

if __name__ == "__main__":
    main()

# results may vary significantly depending on the speed of your internet connection, network congestion, and other factors
"""
Read 274 bytes from http://olympus.realpython.org/dice
Downloaded 160 sites in 21.570857400016394 seconds
"""



#######################################################
# Multi-Threaded Version:
#---------------------------------------------------------------------------------
# This is a classic example of I/O-bound parallelism.
# Same program looks like when you take advantage of the concurrent.futures and threading modules mentioned earlier:
# This script demonstrates multi-threaded I/O concurrency in Python using ThreadPoolExecutor and thread-local storage to efficiently download many web pages in parallel. 
# Let’s walk through it step by step.

#######################################################

# threading → provides thread-local storage
# time → measures execution duration
# ThreadPoolExecutor → manages worker threads
# requests → performs HTTP requests

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import requests             

# Another strategy to use here is something called thread-local storage. When you call threading.local(), you create an object that resembles a global 
# variable but is specific to each individual thread. It looks a little odd, but you only want to create one of these objects, not one for each thread. The object itself 
# takes care of separating accesses from different threads to its attributes.

# This creates a thread-local object, meaning: Each thread gets its own independent copy of attributes stored inside it.

# Thread 1 → thread_local.session
# Thread 2 → thread_local.session
# Thread 3 → thread_local.session

# All separate objects. This avoids thread conflicts and improves performance.

thread_local = threading.local()

# created an instance of the ThreadPoolExecutor to manage the threads for you. have explicitly requested five workers or threads.
# thread: just the train of thought
# pool: This object is going to create a pool of threads, each of which can run concurrently. 
# executor : the executor is the part that’s going to control how and when each of the threads in the pool will run. It’ll execute the request in the pool.

# The standard library implements ThreadPoolExecutor as a context manager, so you can use the with syntax to manage creating and freeing the pool of threading.Thread instances.

# you let the executor call download_site() on your behalf instead of doing it manually in a loop. The executor.map() method on line 21 takes care of distributing the workload 
# across the available threads, allowing each one to handle a different site concurrently. 
# This method takes two arguments:
    # function to be executed on each data item, like a site address
    # collection of data items to be processed by that function

def download_all_sites(sites):        
    with ThreadPoolExecutor(max_workers=5) as executor: # This launches 5 worker threads. Then distributes jobs:
        # Equivalent to:
            # for site in sites:
            # assign task to available thread
        # Threads execute tasks concurrently.
        executor.map(download_site, sites) # executor’s .map() method must take exactly one argument, you modified download_site() on line 23 to only accept a URL.

def download_site(url):                                                     # Each thread runs:
    session = get_session_for_thread()                                      # Gets its own session:
    with session.get(url) as response:                                      # Downloads webpage:
        print(f"Read {len(response.content)} bytes from {url}")             # Prints content size:


# When get_session_for_thread() is called, the session it looks up is specific to the particular thread on which it’s running. So each thread will create a single 
# session the first time it calls get_session_for_thread() and then will use that session on each subsequent call throughout its lifetime.
# Each thread creates one session only once, then reuses it.

def get_session_for_thread(): # This is the most important optimization in the script.
    if not hasattr(thread_local, "session"): # Checks whether the current thread already has a session. If not, creates one.
        thread_local.session = requests.Session() # isn’t thread-safe, meaning that one thread may interfere with the session while another thread is still using it.
    return thread_local.session

def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.perf_counter()
    download_all_sites(sites)
    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration} seconds")

if __name__ == "__main__":
    main()



"""
Read 274 bytes from http://olympus.realpython.org/dice
Downloaded 160 sites in 4.4108912000083365 seconds

"""


# Threads can interact in ways that are subtle and hard to detect. These interactions can cause race conditions that frequently result in random, intermittent bugs that can 
# be quite difficult to find. If you’re unfamiliar with this concept, then you might want to check out a section on race conditions in another tutorial on thread safety.



# Why Use requests.Session() Instead of requests.get()?
    # Because sessions:

        # ✅ reuse TCP connections
        # ✅ reuse cookies
        # ✅ reduce latency
        # ✅ improve performance significantly

    # Without sessions:
        # Each request opens a new connection → slow
    # With sessions:
        # Connection pooling happens automatically


# Why Thread-Local Instead of Global Session?
    # Because requests.Session() is not thread-safe.

    # If shared globally:
        # Thread A modifies headers
        # Thread B modifies cookies
        # Thread C overwrites connection state

    # This causes unpredictable behavior.
    # Thread-local storage solves this cleanly.

# This is one of the interesting and difficult issues with threading. Because the operating system controls when your task gets interrupted and another task starts, 
# any data shared between the threads needs to be protected or thread-safe to avoid unexpected behavior or potential data corruption. Unfortunately, requests.Session() 
# isn’t thread-safe, meaning that one thread may interfere with the session while another thread is still using it.


# There are several strategies for making data access thread-safe. One of them is to use a thread-safe data structure, such as a queue.Queue, multiprocessing.Queue,
#     or an asyncio.Queue. These objects use low-level primitives like lock objects to ensure that only one thread can access a block of code or a bit of memory at the same time. 
# You’re using this strategy indirectly by way of the ThreadPoolExecutor object.



# Execution Flow Summary
    # Step-by-step:
        # main()
        #   ↓
        # create 160 URLs
        #   ↓
        # start timer
        #   ↓
        # ThreadPoolExecutor(5 threads)
        #   ↓
        # each thread:
        #     gets its own session
        #     downloads URL
        #     prints size
        #   ↓
        # stop timer
        #   ↓
        # print total runtime



# Why Multithreading Helps Here

    # This is an I/O-bound task: Threads spend most time waiting for:
        # network latency
        # server response
        # TCP handshake
    # So Python’s GIL is not a bottleneck here.
    # Result:Multithreading speeds things up dramatically.



# Key Advanced Python Concepts Demonstrated
    # This script uses:

        # ✔ ThreadPoolExecutor
        # ✔ Thread-local storage
        # ✔ Connection pooling
        # ✔ Context managers
        # ✔ Concurrent execution
        # ✔ Performance measurement

    # These are exactly the kinds of techniques used in:

        # trading data pipelines
        # market data ingestion systems
        # web scraping engines
        # API batching frameworks








##############################################################################################
# Asynchronous Version:
#---------------------------------------------------------------------------------
# This script is the async (non-threaded) version of your earlier downloader. Instead of using multiple OS threads, it uses event-loop–based concurrency (asyncio), which is typically 
# more scalable and efficient for high-volume network I/O.
# asynchronous I/O.

# What the Program Does (High-Level)
    # It:
        # Creates 160 download tasks
        # Runs them concurrently using async coroutines
        # Shares a single HTTP connection pool
        # Uses an event loop instead of threads
        # Measures total runtime
    # This is ideal for I/O-bound workloads like:
        # API polling
        # market data ingestion
        # web scraping
        # distributed analytics pipelines

# Asynchronous processing is a concurrency model that’s well-suited for I/O-bound tasks—hence the name, asyncio. It avoids the overhead of context switching between threads by
# employing the event loop, non-blocking operations, and coroutines, among other things. Perhaps somewhat surprisingly, the asynchronous code needs only one thread of execution to run 
# concurrently

# In a nutshell, the event loop controls how and when each asynchronous task gets to execute. As the name suggests, it continuously loops through your tasks while monitoring their state. 
# As soon as the current task starts waiting for an I/O operation to finish, the loop suspends it and immediately switches to another task. Conversely, once the expected event occurs, 
# the loop will eventually resume the suspended task in the next iteration.

# A coroutine is similar to a thread but much more lightweight and cheaper to suspend or resume. That’s what makes it possible to spawn many more coroutines than threads without a 
# significant memory or performance overhead. This capability helps address the C10k problem, which involves handling ten thousand concurrent connections efficiently. But there’s a catch.

# You can’t have blocking function calls in your coroutines if you want to reap the full benefits of asynchronous programming. A blocking call is a synchronous one, meaning that it 
# prevents other code from running while it’s waiting for data to arrive. In contrast, a non-blocking call can voluntarily give up control and wait to be notified when the data is ready.

# In Python, you create a coroutine object by calling an asynchronous function, also known as a coroutine function. Those are defined with the async def statement instead of the usual def. 
# Only within the body of an asynchronous function are you allowed to use the await keyword, which pauses the execution of the coroutine until the awaited task is completed:

    # import asyncio

    # async def main():
    #     await asyncio.sleep(3.5)
# In this case, you defined main() as an asynchronous function that implicitly returns a coroutine object when called. Thanks to the await keyword, your coroutine makes a non-blocking
# call to asyncio.sleep(), simulating a delay of three and a half seconds. While your main() function awaits the wake-up event, other tasks could potentially run concurrently.

# because the Requests library that you’ve been using in this tutorial is blocking, you must now switch to a non-blocking counterpart, such as aiohttp, 
# which was designed for Python’s asyncio:

##############################################################################################

# asyncio → event loop + coroutine scheduling
# time → execution timer
# aiohttp → async HTTP client (non-blocking version of requests)

import asyncio
import time

import aiohttp # This library replaces Requests from earlier examples.

# aysnc redefine your regular functions as asynchronous ones by qualifying their signatures with the async keyword.
# 1. async def
# 2. async with : create asynchronous context managers for the session object and the response, respectively.
# 3. await


# create asynchronous context managers for the session object.
# async with aiohttp.ClientSession() as session:
    # This:
        # ✔ enables connection pooling
        # ✔ avoids repeated TCP handshakes
        # ✔ improves performance dramatically
    # Equivalent to requests.Session() but async.

# creates a list of tasks using a list comprehension, where each task is a coroutine object returned by download_site(). 
    # Notice that you don’t await the individual coroutine objects, as doing so would lead to executing them sequentially.
#  tasks = [download_site(url, session) for url in sites]
    # This builds a list of coroutines, not threads.
        # Example:
            # [
            #  coroutine1,
            #  coroutine2,
            #  coroutine3,
            #  ...
            # ]
# uses asyncio.gather() to run all the tasks concurrently, allowing for efficient downloading of multiple sites at the same time.
    # This schedules all tasks concurrently inside the event loop.
        # Important:
            # NOT sequential
            # NOT threaded
            # NOT multiprocessing
        # Instead:
            # single thread
            # multiple pending I/O operations
            # cooperative scheduling
async def download_all_sites(sites):
    async with aiohttp.ClientSession() as session:                              
        tasks = [download_site(url, session) for url in sites]
        await asyncio.gather(*tasks, return_exceptions=True)



# Reading response (create asynchronous context managers for the response)
# awaits the completion of the session’s HTTP GET request before printing the number of bytes read.
# async with session.get(url) as response:     
    # Sends HTTP request asynchronously
        # This does non-blocking network I/O.
        # Instead of waiting: thread sleeps
        # Python does:switch to another coroutine
async def download_site(url, session):
    async with session.get(url) as response:                                                  
        print(f"Read {len(await response.read())} bytes from {url}")    # await response.read(): again non-blocking. event loop switches tasks while waiting.


# This defines an async coroutine instead of a normal function.

async def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.perf_counter()
        # Runs async downloader:
        # prepends the await keyword to download_all_sites() so that the returned coroutine object can be awaited. 
        # This effectively suspends your main() function until all sites have been downloaded.
    await download_all_sites(sites)  
    
    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration} seconds")

if __name__ == "__main__":
    # Creates and starts the event loop:
        # create loop
        # schedule main()
        # execute tasks
        # shutdown loop
    # Equivalent to:
        # loop = asyncio.get_event_loop()
        # loop.run_until_complete(main())
    # (but modern and cleaner)

    asyncio.run(main())

"""
... 
Downloaded 160 sites in 0.4215377999935299 seconds
"""

# Execution Flow
    # Step-by-step:
        # asyncio.run(main())
        #         ↓
        # create 160 URLs
        #         ↓
        # create ClientSession
        #         ↓
        # create coroutine tasks
        #         ↓
        # asyncio.gather()
        #         ↓
        # event loop schedules tasks
        #         ↓
        # requests executed concurrently
        #         ↓
        # responses processed
        #         ↓
        # timer stops
        #         ↓
        # print runtime


# Why Async Is Faster Than Threads Here
    # Threads:
        # OS scheduling
        # context switching overhead
        # memory overhead
        # GIL interactions
    # Async:
        # single thread
        # no context switching cost
        # no thread creation
        # event-loop scheduling only
    # Result:
        # lower latency
        # higher throughput
        # better scalability
    # Especially when:
        # 100+
        # 1000+
        # 10000+ requests


# asyncio.gather(return_exceptions=True)
    # This is important.
    # Without:
        # one failed request
        # → program crashes
    # With:
        # exceptions captured
        # other tasks continue running
    # Example captured:
        # TimeoutError
        # ConnectionResetError
        # DNS failure


# requests vs aiohttp Comparison
    # Feature	                     requests	        aiohttp
    # --------------------------------------------------------------
    # Blocking	                    Yes	                No
    # Threads required	            Yes	                No
    # Uses event loop	            No	                Yes
    # Scales to 10k+ requests	    No	                Yes
    # Best for	                    Simple scripts	    High-performance pipelines




# Why One Shared ClientSession?
    # Correct pattern:
        # async with ClientSession()
    # Avoid this:
        # create session per request ❌
    # Because:
        # expensive
        # no connection reuse
        # slower performance
    # Best practice:
        # one session per application



# Performance Comparison vs Thread Version

    # Typical behavior:
        # Method	            160 URLs
        # ----------------------------------
        # Sequential	        Slowest
        # ThreadPoolExecutor	Faster
        # asyncio + aiohttp	    Fastest

    # Async wins because:
        # no threads
        # no locks
        # no GIL contention
        # minimal overhead


# Advanced Concepts Demonstrated Here
    # This script uses:

        # ✔ Coroutines
        # ✔ Event loop scheduling
        # ✔ Non-blocking I/O
        # ✔ Connection pooling
        # ✔ Task orchestration
        # ✔ Structured concurrency (gather)

    # These are exactly the primitives used in:

        # trading data collectors
        # streaming pipelines
        # order book ingestion engines
        # async REST gateways
        # microservices




##############################################################################################
# Process-Based Version:
#---------------------------------------------------------------------------------

# Up to this point, all of the examples of concurrency in this tutorial ran only on a single CPU or core in your computer. The reasons for this have to do with the current design of 
# CPython and something called the Global Interpreter Lock, or GIL.

#  the synchronous, multi-threaded, and asynchronous versions of this example all run on a single CPU.
# The multiprocessing module, along with the corresponding wrappers in concurrent.futures, was designed to break down that barrier and run your code across multiple CPUs. 
# At a high level, it does this by creating a new instance of the Python interpreter to run on each CPU and then farming out part of your program to run on it.

# As you can imagine, bringing up a separate Python interpreter is not as fast as starting a new thread in the current Python interpreter. It’s a heavyweight operation 
# and comes with some restrictions and difficulties, but for the correct problem, it can make a huge difference.

# Unlike the previous approaches, using multiprocessing allows you to take full advantage of the all CPUs that your cool, new computer has.


# This script is the multiprocessing version of your downloader. Instead of threads (ThreadPoolExecutor) or async (asyncio), it uses multiple processes via ProcessPoolExecutor. 
# Each process runs independently with its own Python interpreter and memory space.
# This approach is typically best for CPU-bound workloads, but here it demonstrates how multiprocessing works with network tasks.

# What the Program Does (High-Level)
    # It:
        # Creates 160 download jobs
        # Launches multiple worker processes
        # Initializes one HTTP session per process
        # Downloads URLs in parallel
        # Prints which process handled each request
        # Measures total runtime

    # Execution happens across separate OS processes, not threads.

    
##############################################################################################

# atexit → runs cleanup code when process exits
# multiprocessing → identifies worker process names
# ProcessPoolExecutor → manages worker processes
# requests → HTTP client
# time → runtime measurement

import atexit
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor
import requests

# Global Session Declaration
# This declares a global variable placeholder.
    # Important:
        # Each process gets its own independent copy of this variable.
    # Unlike threads:
        # Threads → shared memory
        # Processes → separate memory
    # So every process creates its own session.

#  uses type hints to declare a global variable that will hold the session object. Note that this doesn’t actually define the value of the variable.
session: requests.Session

# define a custom initializer function that each process will call shortly after starting. It ensures that each process initializes its own session.
# registers a cleanup function with atexit, which ensures that the session is properly closed when the process stops. This helps prevent potential memory leaks.

# global session
# session = requests.Session()
    # Creates process-local session:
        # Each worker process gets:

        # its own TCP connection pool
        # its own cookies
        # its own headers
def init_process():
    global session
    session = requests.Session()
    atexit.register(session.close)

# replaces ThreadPoolExecutor with ProcessPoolExecutor from concurrent.futures and passes init_process()
# The line that creates a pool instance is worth your attention. First off, it doesn’t specify how many processes to create in the pool, although that’s an optional parameter. 
# By default, it’ll determine the number of CPUs in your computer and match that. This is frequently the best answer, and it is in your case.
# with ProcessPoolExecutor(initializer=init_process) as executor:
    # Creates process pool:
    # Important part:
        # initializer=init_process
    # This function runs once per worker process when it starts.
    # Then distributes tasks: executor.map(download_site, sites)
    # Equivalent to:
        # send each URL to an available process
    # Processes execute tasks in parallel.

def download_all_sites(sites):
    with ProcessPoolExecutor(initializer=init_process) as executor:
        executor.map(download_site, sites)

# with session.get(url) as response:
    # Uses the session created earlier:
def download_site(url):
    with session.get(url) as response:
        name = multiprocessing.current_process().name               # Gets process name:
        print(f"{name}:Read {len(response.content)} bytes from {url}")

def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    start_time = time.perf_counter()
    download_all_sites(sites)
    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration} seconds")

if __name__ == "__main__":
    main()


# For an I/O-bound problem, increasing the number of processes won’t make things faster. It’ll actually slow things down because the cost of setting up and tearing down all 
# those processes is larger than the benefit of doing the I/O requests in parallel.

# Why Use initializer=init_process?
    # Because sessions cannot be shared across processes.
    # If you tried:
        # session = requests.Session()
    # outside workers:
        # pickle error
        # or duplicated unsafe state
    # Instead:
        # initialize inside each process
    # Correct pattern:
        # ProcessPoolExecutor(initializer=...)





# Execution Flow
    # Step-by-step:
        # main()
        #   ↓
        # create 160 URLs
        #   ↓
        # start ProcessPoolExecutor
        #   ↓
        # spawn worker processes
        #   ↓
        # each process runs init_process()
        #       create session
        #       register cleanup handler
        #   ↓
        # process executes download_site(url)
        #   ↓
        # prints result
        #   ↓
        # shutdown pool
        #   ↓
        # close sessions
        #   ↓
        # print runtime

# Why multiprocessing Works Differently Than Threading
    # Threads:
        # shared memory
        # cheap creation
        # GIL applies
    # Processes:
        # separate memory
        # expensive creation
        # no GIL limitation
        # true parallelism




# Feature	                Threads	            Processes
# -----------------------------------------------------------------
# Memory shared	            Yes	                No
# GIL affected	            Yes	                No
# Startup cost	            Low	                High
# Parallel CPU execution	No	                Yes




# Important Insight: This Is Not Ideal for Network I/O
    # This example works, but multiprocessing is usually not optimal for HTTP downloads.
    # Better choices:
        # ThreadPoolExecutor
        # asyncio + aiohttp
    # Why?
    # Because multiprocessing has:
        # process startup overhead
        # memory duplication
        # IPC cost
    # Multiprocessing shines when:
        # heavy math
        # ML workloads
        # Monte Carlo simulations
        # option pricing grids
        # large dataframe transforms
    # (very relevant in quant workloads)



# Why atexit.register(session.close) Matters
    # Without:
        # session may stay open
        # connections leak
        # file descriptors accumulate
    # With:
        # automatic cleanup at process shutdown
    # Production-safe pattern.


# Default Number of Processes
    # Since not specified: ProcessPoolExecutor() defaults to:
        # number_of_cpu_cores
    # Example:
        # 8 cores → 8 processes

# Comparison with Your Previous Two Versions
# --------------------------------------------------
# Method	            Best For	        Speed
# Sequential	        small tasks	        slow
# ThreadPoolExecutor	I/O-bound	        fast
# asyncio + aiohttp	    massive I/O-bound	fastest
# ProcessPoolExecutor	CPU-bound	        best




# Your three scripts demonstrate the three core concurrency models in Python:
        # threads
        # event loop
        # processes
    # This is exactly the concurrency toolkit used in:
        # market data ingestion engines
        # pricing grids
        # Monte Carlo simulation farms
        # risk scenario engines
        # distributed backtesting systems


import atexit
import multiprocessing
import time

import requests


session = None


def init_process():
    """
    Runs once inside each worker process.
    Each process gets its own requests.Session().
    """
    global session
    session = requests.Session()
    atexit.register(session.close)


def download_site(url):
    """
    Runs inside worker process.
    """
    global session

    with session.get(url) as response:
        process_name = multiprocessing.current_process().name
        print(f"{process_name}: Read {len(response.content)} bytes from {url}")


def download_all_sites(sites):
    cpu_count = multiprocessing.cpu_count()

    with multiprocessing.Pool(
        processes=cpu_count,
        initializer=init_process
    ) as pool:
        pool.map(download_site, sites)


def main():
    sites = [
        "https://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80

    start_time = time.perf_counter()

    download_all_sites(sites)

    duration = time.perf_counter() - start_time
    print(f"Downloaded {len(sites)} sites in {duration:.2f} seconds")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()