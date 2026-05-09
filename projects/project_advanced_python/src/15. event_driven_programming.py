#########################################################################################
# https://realpython.com/intro-to-python-threading/

# I’ll put this together as a small but realistic event-driven market-data pipeline: one producer thread simulates ticks, one dispatcher consumes a queue, 
# and strategy/risk handlers react to events using Event, Queue, deque, and threads.


# Below is a compact event-driven market-data simulation using:

    # threading.Event
    # thr
    # queue.Queue
    # collections.deque
    # random simulated prices
    # event dispatcher pattern
    # rolling window analytics

# deque and Queue are both FIFO-style containers in Python, but they serve different purposes. The key distinction is:

# deque is a fast general-purpose data structure
# Queue is a thread-safe communication tool


#########################################################################################


# MarketDataProducer
#     ↓
# creates MARKET_TICK events
#     ↓
# Queue
#     ↓
# EventDispatcher
#     ↓
# MovingAverageStrategy
#     ↓
# creates SIGNAL events
#     ↓                                                                                                                                                                                     
# ExecutionHandler

# Key advanced Python concepts used:
    # queue module: 
        # Queue          → thread-safe event bus
    # threading module:
        # Event          → graceful shutdown signal
        # Thread         → concurrent market data producer
    # collections module:
        # deque          → rolling price window
    # dataclasses module:
        # dataclass      → clean event/message objects
    # enum module:
        # Enum           → strongly defined event types
    # dispatcher     → event-driven architecture


import random
import time
import threading
from queue import Queue, Empty
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
# The line from enum import Enum, auto is used in Python to import the essential tools for creating enumerations 
# (sets of symbolic names bound to unique, constant values
# Enum: The base class for creating enumeration constants. Subclassing Enum helps make your code more readable and prevents the use of "magic numbers".
# auto(): A helper function that automatically assigns values to your enum members when the exact value doesn't matter. By default, it 
# starts at 1 and increments by 1 for each subsequent member

# =========================
# Event Types
# =========================

# Event Type Block
# This defines the types of events that can flow through the system.
# This prevents using messy strings like:
    # "market_tick"
    # "signal"
    # "shutdown"
# Instead, you use a clean enum.

class EventType(Enum): # 
    MARKET_TICK = auto()                    # A new simulated market price has arrived.
    SIGNAL = auto()                         # The strategy has generated a trading signal.
    SHUTDOWN = auto()                       # The system should stop.

# Market Tick Data Block : This defines the structure of a market tick.(light weight container holding the raw price data)
# The @dataclass automatically creates __init__, __repr__, and comparison methods.
# Example object : MarketTick(symbol="EURUSD", price=1.10123, timestamp=1710000000.0)
@dataclass
class MarketTick:
    symbol: str                     # The instrument name.
    price: float                    # latest price.
    timestamp: float                # When the tick was generated.


# Signal Data Block : This defines a trading signal.(light weight container holding the decision BUY/SELL of the strategy)
# Example object : Signal(symbol="EURUSD",action="BUY",price=1.10200,moving_average=1.10150)
@dataclass
class Signal:
    symbol: str
    action: str
    price: float
    moving_average: float

# Generic Event Block : This is the common wrapper for every message.
# Instead of putting raw ticks or signals into the queue, we wrap them as events.
# This lets the dispatcher know what kind of object it is receiving.
# Example:
    # Event(EventType.MARKET_TICK, tick)
                # or
    # Event(EventType.SIGNAL, signal)
# If the type is MARKET_TICK, the data will be a MarketTick object.
# If the type is SIGNAL, the data will be a Signal object.
@dataclass
class Event:                        # In the context of this trading system, the Event class acts as a standardized envelope or package.
    type: EventType                 # This uses the Enum we discussed earlier. It serves as the label on the outside of the envelope (e.g., 
                                    # "This is a Market Tick" or "This is a Signal").
    data: object                    # This is the content inside the envelope.
                                    # If the type is MARKET_TICK, the data will be a MarketTick object.
                                    # If the type is SIGNAL, the data will be a Signal object.

# =========================
# Market Data Producer (The "Input")
# =========================

class MarketDataProducer(threading.Thread):                                 # This creates a custom thread. Its job is to simulate live market data.
    # This block initializes the producer. Constructor
    def __init__(self, event_queue: Queue, stop_event: threading.Event):
        super().__init__(daemon=True)  # Initializes the parent Thread class.  daemon=True means this background thread will not prevent Python from exiting.
        self.event_queue = event_queue  # The shared queue where market ticks will be sent.
        self.stop_event = stop_event    # A signal telling the thread when to stop.
        self.price = 1.1000             # Initial EURUSD price.

    # Producer Run Loop
    def run(self):
        while not self.stop_event.is_set():     # The loop continues until stop_event is switched on.
            self.price += random.uniform(-0.0010, 0.0010) # This creates a random price movement.

            tick = MarketTick(                  # This creates a market tick object.
                symbol="EURUSD",
                price=round(self.price, 5),
                timestamp=time.time()
            )

            event = Event(EventType.MARKET_TICK, tick)          # This wraps the tick inside a market-tick event.
            self.event_queue.put(event)                         # This sends the market tick event into the queue. Now the dispatcher can consume it.

            time.sleep(0.25)                                    # Waits 0.25 seconds before creating the next tick. So it creates around 4 ticks per second.

        self.event_queue.put(Event(EventType.SHUTDOWN, None))   # When the producer stops, it sends a shutdown event. This tells the dispatcher to stop too.


# =========================
# Strategy Engine (The "Brain")
# This block defines the strategy. It listens to market ticks, stores recent prices, calculates moving average, and generates BUY/SELL signals.
# =========================


class MovingAverageStrategy:
    # This initializes the strategy. Constructor
    def __init__(self, event_queue: Queue, window_size: int = 10):
        self.event_queue = event_queue                              # The strategy needs the queue because it will publish signal events.
        self.prices = deque(maxlen=window_size)                     # This stores the latest 10 prices. When the 11th price arrives, the oldest one is automatically removed.
                                                                    # This is very useful for rolling windows.
    
    # Strategy Logic
    def on_market_tick(self, tick: MarketTick):                     # This method is called whenever a new market tick arrives.
        self.prices.append(tick.price)                              # Add latest price to rolling window.

        if len(self.prices) < self.prices.maxlen:                   # If we do not yet have 10 prices, do nothing. Because moving average over 10 prices needs 10 observations.
            return

        moving_average = sum(self.prices) / len(self.prices)        # Calculate simple moving average.

        # Simple trading rule:
        if tick.price > moving_average:
            action = "BUY"
        elif tick.price < moving_average:
            action = "SELL"
        else:
            action = "HOLD"

        # Create signal object.
        signal = Signal(
            symbol=tick.symbol,
            action=action,
            price=tick.price,
            moving_average=round(moving_average, 5)
        )
        # If a decision is made, it creates a Signal and puts it back into the event_queue.
        self.event_queue.put(Event(EventType.SIGNAL, signal))

        # This is the key event-driven pattern:
        # Market Tick Event → Strategy → Signal Event


# =========================
# Risk / Execution Handler
# =========================

# Execution Handler Block
# This block handles trading signals. In this example, it only prints them.
# In a real trading system, this is where you would send orders.
class ExecutionHandler:
    # This method receives a signal.
    def on_signal(self, signal: Signal):
        print(
            f"[SIGNAL] {signal.symbol} | "
            f"{signal.action} | "
            f"Price={signal.price} | "
            f"MA={signal.moving_average}"
        )

    # Prints the signal. Example output : [SIGNAL] EURUSD | BUY | Price=1.10125 | MA=1.10092
    # In production, this could become: 
        # order_manager.send_order(signal)


# =========================
# Event Dispatcher ( (The "Traffic Cop"))
# the Event Dispatcher acts as that sorter. It performs a simple check on every Event object:
# =========================

# This is the central router # It reads events from the queue and decides where to send them # It is like the traffic controller of the system.

class EventDispatcher:
    # Constructor. This creates:
    def __init__(self, event_queue: Queue, stop_event: threading.Event):
        self.event_queue = event_queue              # The queue to consume from.
        self.stop_event = stop_event                # The shutdown signal.

        self.strategy = MovingAverageStrategy(event_queue)  # The moving-average strategy.
        self.execution_handler = ExecutionHandler()         # The object that handles generated signals.
    
    # Dispatcher Loop
    def run(self):
        while not self.stop_event.is_set():                 # This keeps the dispatcher running until the stop signal is set.
            try:
                event = self.event_queue.get(timeout=1)     # The dispatcher waits up to 1 second for an event. If there is an event, it processes it.
                                                            # If no event arrives, it raises Empty.

                # If the event is a market tick event
                    # 1. Extract tick
                    # 2. Print tick
                    # 3. Send tick to strategy

                if event.type == EventType.MARKET_TICK:
                    tick = event.data
                    print(f"[TICK] {tick.symbol} price={tick.price}")
                    self.strategy.on_market_tick(tick)
                
                # If the event is a trading signal event:
                    # 1. Extract signal
                    # 2. Send signal to execution handler
                elif event.type == EventType.SIGNAL:
                    signal = event.data
                    self.execution_handler.on_signal(signal)

                # If the event is shutdown event
                    # 1. Print shutdown message
                    # 2. Exit dispatcher loop
                elif event.type == EventType.SHUTDOWN:
                    print("[SYSTEM] Shutdown event received.")
                    break

                self.event_queue.task_done()        # Marks the event as fully processed. 
                                                    # This is useful when you use: event_queue.join()

            except Empty:                           # If the queue has no event, just continue waiting. This prevents the dispatcher from crashing.
                continue


# =========================
# Main Application ((The "Manager"))
# The main() function wires everything together:
# =========================

def main():
    # event_queue is a single "pipe" that handles many different types of information, you need a way to wrap that information so the system k
    # nows what it is looking at when it pulls it out of the pipe.
    
    # Creates the shared Queue and Stop Event.
    event_queue = Queue()                       # Creates the shared event queue.  This is the central communication channel.            
    stop_event = threading.Event()              # Creates the shutdown signal. Initially it is false.
                                                # When we call: stop_event.set() all loops checking it will stop.

    # Initializes the Producer and Dispatcher.
    producer = MarketDataProducer(event_queue, stop_event)  # Creates the market-data producer.
    dispatcher = EventDispatcher(event_queue, stop_event)   # Creates the dispatcher.

    producer.start()                                        # Starts the producer thread. Now simulated ticks begin flowing into the queue.

    dispatcher_thread = threading.Thread(                   # Creates another thread to run the dispatcher. Why another thread? Because the dispatcher waits continuously for events.
        target=dispatcher.run,
        daemon=True
    )

    dispatcher_thread.start()                               # Starts the dispatcher thread. 
                                                            # Now two threads are active:
                                                                # Thread 1: MarketDataProducer
                                                                # Thread 2: EventDispatcher

    # Cleanup: Once the time is up (or you hit Ctrl+C), it signals all threads to stop and waits for them to finish (join()) to ensure no data 
    # is lost and the program exits cleanly.

    # Runtime and Shutdown Block
    try:
        time.sleep(10)                                      # Let the system run for 10 seconds.
    except KeyboardInterrupt:
        print("[SYSTEM] Keyboard interrupt received.")      # If you press Ctrl+C, it handles the interrupt cleanly.
    finally:
        stop_event.set()                                    # This triggers shutdown.
        producer.join()                                     # Waits for producer thread to finish.
        dispatcher_thread.join()                            # Waits for dispatcher thread to finish.

        print("[SYSTEM] Application stopped cleanly.")      # Final message.

# Entry Point Block
if __name__ == "__main__":
    main()                                                  # This ensures main() runs only when the file is executed directly.
                                                            # This is especially important when using threading or multiprocessing.




# main()
#   ↓
# creates Queue and stop_event
#   ↓
# starts MarketDataProducer thread
#   ↓
# starts EventDispatcher thread
#   ↓
# producer generates random EURUSD ticks
#   ↓
# ticks go into Queue
#   ↓
# dispatcher reads Queue
#   ↓
# strategy receives ticks
#   ↓
# strategy updates deque rolling window
#   ↓
# strategy emits BUY/SELL signal
#   ↓
# signal goes into Queue
#   ↓
# dispatcher sends signal to ExecutionHandler
#   ↓
# after 10 seconds stop_event is set
#   ↓
# threads stop cleanly




# The architecture is:
    # Producer → Queue → Dispatcher → Strategy → Queue → Dispatcher → ExecutionHandler
# This is a simple version of the architecture used in real trading systems:
    # Market Data Feed → Event Bus → Strategy Engine → Signal/Event Bus → Execution/Risk Engine