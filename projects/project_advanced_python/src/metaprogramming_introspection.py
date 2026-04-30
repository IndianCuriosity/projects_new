###############################################################################################################
# Metaprogramming and introspection are advanced Python techniques that let programs inspect themselves and modify behavior dynamically at runtime. 
# They’re heavily used in frameworks (e.g., ORMs, serializers, dependency injection systems) and are especially valuable in quant infrastructure, 
# analytics engines, and plugin-style architectures.

# What Is Introspection?
    # Introspection means examining objects at runtime:
        # What attributes does this object have?
        # What methods exist?
        # What type is this?
        # What arguments does this function accept?

    # Python makes this very easy. So Python lets you inspect structure dynamically.

# What Is Metaprogramming?
    # Metaprogramming means writing code that writes or modifies other code.
        # Examples:
            # decorators
            # descriptors
            # metaclasses
            # dynamic class creation
            # runtime method injection
###############################################################################################################

# Most Important Introspection Functions
# -------------------------------------------------

# type()
print(type(10))

# Lists attributes/methods:
print(dir(str))

# id()
# Returns memory identity:
print(id(10))

# isinstance() : Checks type safely:
isinstance(5, int)



# hasattr(), getattr(), setattr(): Dynamic attribute access: Used everywhere in dynamic frameworks.
class A:
    x = 10

obj = A()

print(hasattr(obj, "x"))
print(getattr(obj, "x"))

setattr(obj, "y", 20)
print(obj.y)

"""
>>> obj = A()
>>> print(hasattr(obj, "x"))
True
>>> print(getattr(obj, "x"))
10
>>> setattr(obj, "y", 20)
>>> print(obj.y)
20
"""

# Inspecting Function Metadata
def add(a, b):
    return a + b

print(add.__name__) 
print(add.__doc__)
print(add.__code__.co_varnames)

"""
>> print(add.__name__)
add
>>> print(add.__doc__)
None
>>> print(add.__code__.co_varnames)
('a', 'b')
"""



# Using the inspect Module (Advanced Introspection)
#---------------------------------------------------
    # The inspect module gives deeper access.

import inspect

def greet(name):
    return f"Hello {name}"

print(inspect.signature(greet))
print(inspect.getmembers(greet))

# Used heavily in:
    # FastAPI
    # pytest
    # dependency injection systems
    # decorators
    # plugin frameworks





#--------------------------------------------------
# What Is Metaprogramming?
#--------------------------------------------------


# Functions are assignable dynamically.
#---------------------------------------------------
def hello():
    print("Hello")

f = hello
f()





# Example: Dynamic Attribute Creation
#---------------------------------------------------
class Person:
    pass

p = Person()
setattr(p, "name", "Alice") # Attribute created at runtime.
print(p.name)



# Example: Dynamic Method Injection
#---------------------------------------------------
class A:
    pass

def greet(self):
    print("Hello!")

A.greet = greet # Method added dynamically.. This is metaprogramming

obj = A()
obj.greet()



# Example: Dynamic Class Creation : Classes themselves are objects.
#---------------------------------------------------

MyClass = type("MyClass", (), {"x": 10})
obj = MyClass()
print(obj.x)

    #Equivalent to:
class MyClass:
    x = 10

    # But created dynamically.
    #     Used in:
    #         ORMs
    #         serializers
    #         API frameworks





# Decorators = Metaprogramming
    # This modifies another function dynamically.
#---------------------------------------------------
def logger(func):
    def wrapper(*args, **kwargs):
        print("Calling function")
        return func(*args, **kwargs)
    return wrapper





# Using globals() and locals()
    # Access symbol tables dynamically.
#---------------------------------------------------

x = 10
print(globals()["x"])





# Executing Code Dynamically
#---------------------------------------------------
eval("2 + 3") # Evaluates expressions:

exec("x = 10") # Executes statements:
print(x)




# Example: Plugin Architecture Pattern
#---------------------------------------------------
    
    # Common real-world use:

def run_strategy(strategy_name):

    strategy = globals()[strategy_name]

    strategy()

def momentum():
    print("Momentum strategy")

run_strategy("momentum") # Framework-style dynamic execution.



# Metaclasses (Advanced Metaprogramming)
# Metaclasses control class creation itself. 
# Frameworks like Django ORM rely heavily on this.
#---------------------------------------------------
class Meta(type):
    def __new__(cls, name, bases, dct):
        dct["id"] = 100
        return super().__new__(cls, name, bases, dct)


class A(metaclass=Meta):
    pass


print(A.id)


# Real-World Uses in Quant / Data Systems : These appear frequently in production analytics stacks:
# ----------------------------------------------

strategy = getattr(module, strategy_name)       # Dynamic strategy loading

registry[class_name] = cls                      # Auto-registering signals

if hasattr(model, "predict_proba")              # Runtime feature selection

pipeline_step = globals()[step_name]            # Config-driven pipelines

# Introspection vs Metaprogramming
# --------------------------------------------------
# Feature	                    Introspection	            Metaprogramming
# -----------------------------------------------------------------------------------------
# Inspect objects	            ✅	                       ❌
# Modify objects	            ❌	                       ✅
# Runtime behavior changes  	❌	                       ✅
# Example	                    dir(obj)	                decorators
# Example	                    inspect.signature()	        metaclasses





# Mental Model
    # Think:
        # introspection = reading program structure
        # metaprogramming = changing program structure

    # Both enable framework-level Python design and are core tools behind:
        # FastAPI
        # SQLAlchemy
        # Django ORM
        # pytest
        # dataclasses
        # Pydantic
        # plugin engines
        # strategy loaders