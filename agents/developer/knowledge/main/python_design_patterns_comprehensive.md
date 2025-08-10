---
source: https://refactoring.guru/design-patterns/python
retrieved: 2025-08-09T14:28:54Z
fetch_method: document_query
agent: agent0
original_filename: python_design_patterns_refactoring_guru.md
content_type: comprehensive_catalog
verification_status: pending
---

# Python Design Patterns - Comprehensive Catalog

*Source: Refactoring.Guru - Authoritative design patterns resource*

## Overview

This comprehensive catalog covers all major design patterns with Python implementations, organized by category: Creational, Structural, and Behavioral patterns. Each pattern includes detailed explanations, use cases, and working Python code examples.

## Creational Patterns

### Abstract Factory
Lets you produce families of related objects without specifying their concrete classes.
- **Purpose**: Create families of related objects
- **Use Case**: When you need to ensure compatibility between created objects
- **Python Implementation**: Available with detailed examples

### Builder
Lets you construct complex objects step by step. The pattern allows you to produce different types and representations of an object using the same construction code.
- **Purpose**: Construct complex objects incrementally
- **Use Case**: When object creation involves many optional parameters
- **Python Implementation**: Particularly useful with method chaining

### Factory Method
Provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.
- **Purpose**: Create objects without specifying exact classes
- **Use Case**: When you need flexibility in object creation
- **Python Implementation**: Leverages Python's dynamic typing

### Prototype
Lets you copy existing objects without making your code dependent on their classes.
- **Purpose**: Clone objects efficiently
- **Use Case**: When object creation is expensive
- **Python Implementation**: Uses copy.deepcopy() and __copy__ methods

### Singleton
Lets you ensure that a class has only one instance, while providing a global access point to this instance.
- **Purpose**: Ensure single instance of a class
- **Use Case**: Database connections, logging, configuration
- **Python Implementations**: 
  - Naïve Singleton
  - Thread-safe Singleton

## Structural Patterns

### Adapter
Allows objects with incompatible interfaces to collaborate.
- **Purpose**: Make incompatible interfaces work together
- **Use Case**: Integrating third-party libraries
- **Python Implementation**: Uses composition and delegation

### Bridge
Lets you split a large class or a set of closely related classes into two separate hierarchies—abstraction and implementation—which can be developed independently.
- **Purpose**: Separate abstraction from implementation
- **Use Case**: When you need to switch implementations at runtime
- **Python Implementation**: Leverages duck typing

### Composite
Lets you compose objects into tree structures and then work with these structures as if they were individual objects.
- **Purpose**: Treat individual and composite objects uniformly
- **Use Case**: File systems, UI components, organizational structures
- **Python Implementation**: Recursive structure handling

### Decorator
Lets you attach new behaviors to objects by placing these objects inside special wrapper objects that contain the behaviors.
- **Purpose**: Add behavior to objects dynamically
- **Use Case**: Adding features without modifying existing code
- **Python Implementation**: Can use Python decorators or wrapper classes

### Facade
Provides a simplified interface to a library, a framework, or any other complex set of classes.
- **Purpose**: Simplify complex subsystem interfaces
- **Use Case**: API wrappers, system integration
- **Python Implementation**: Single class exposing simplified methods

### Flyweight
Lets you fit more objects into the available amount of RAM by sharing common parts of state between multiple objects instead of keeping all of the data in each object.
- **Purpose**: Minimize memory usage through object sharing
- **Use Case**: Large numbers of similar objects
- **Python Implementation**: Uses __new__ method for instance control

### Proxy
Lets you provide a substitute or placeholder for another object. A proxy controls access to the original object, allowing you to perform something either before or after the request gets through to the original object.
- **Purpose**: Control access to another object
- **Use Case**: Lazy loading, access control, caching
- **Python Implementation**: Method delegation and __getattr__

## Behavioral Patterns

### Chain of Responsibility
Lets you pass requests along a chain of handlers. Upon receiving a request, each handler decides either to process the request or to pass it to the next handler in the chain.
- **Purpose**: Avoid coupling sender to receiver
- **Use Case**: Event handling, middleware, request processing
- **Python Implementation**: Linked list of handlers

### Command
Turns a request into a stand-alone object that contains all information about the request. This transformation lets you pass requests as method arguments, delay or queue a request's execution, and support undoable operations.
- **Purpose**: Encapsulate requests as objects
- **Use Case**: Undo/redo, queuing, logging operations
- **Python Implementation**: Callable objects and function objects

### Iterator
Lets you traverse elements of a collection without exposing its underlying representation (list, stack, tree, etc.).
- **Purpose**: Provide sequential access to elements
- **Use Case**: Custom collection traversal
- **Python Implementation**: __iter__ and __next__ methods, generators

### Mediator
Lets you reduce chaotic dependencies between objects. The pattern restricts direct communications between the objects and forces them to collaborate only via a mediator object.
- **Purpose**: Reduce coupling between communicating objects
- **Use Case**: UI components, chat systems, workflow engines
- **Python Implementation**: Central coordinator class

### Memento
Lets you save and restore the previous state of an object without revealing the details of its implementation.
- **Purpose**: Capture and restore object state
- **Use Case**: Undo functionality, checkpoints, snapshots
- **Python Implementation**: State serialization and restoration

### Observer
Lets you define a subscription mechanism to notify multiple objects about any events that happen to the object they're observing.
- **Purpose**: Notify multiple objects about state changes
- **Use Case**: Event systems, MVC architecture, reactive programming
- **Python Implementation**: Subject-observer lists and notifications

### State
Lets an object alter its behavior when its internal state changes. It appears as if the object changed its class.
- **Purpose**: Change behavior based on internal state
- **Use Case**: State machines, game characters, UI controls
- **Python Implementation**: State classes with polymorphic behavior

### Strategy
Lets you define a family of algorithms, put each of them into a separate class, and make their objects interchangeable.
- **Purpose**: Select algorithm at runtime
- **Use Case**: Sorting algorithms, payment processing, compression
- **Python Implementation**: Algorithm classes with common interface

### Template Method
Defines the skeleton of an algorithm in the superclass but lets subclasses override specific steps of the algorithm without changing its structure.
- **Purpose**: Define algorithm structure, customize steps
- **Use Case**: Frameworks, data processing pipelines
- **Python Implementation**: Abstract base classes with hook methods

### Visitor
Lets you separate algorithms from the objects on which they operate.
- **Purpose**: Add operations to object structures without modification
- **Use Case**: Compilers, document processing, tree traversal
- **Python Implementation**: Double dispatch simulation

## Implementation Notes for Python

### Language-Specific Advantages
- **Dynamic Typing**: Simplifies many pattern implementations
- **First-Class Functions**: Enable functional approaches to patterns
- **Decorators**: Natural implementation for Decorator pattern
- **Generators**: Excellent for Iterator pattern
- **Duck Typing**: Reduces need for explicit interfaces
- **Multiple Inheritance**: Supports mixin patterns

### Python-Specific Considerations
- Some patterns are less relevant due to Python's dynamic nature
- Built-in features often provide pattern functionality
- Focus on Pythonic implementations over rigid OOP structures
- Leverage Python's strengths: simplicity, readability, expressiveness

## Best Practices

1. **Choose Appropriate Patterns**: Not every problem needs a design pattern
2. **Favor Composition**: Over inheritance when possible
3. **Keep It Simple**: Don't over-engineer solutions
4. **Python Idioms**: Use Pythonic approaches when they're clearer
5. **Documentation**: Clearly document pattern usage and intent
6. **Testing**: Patterns should enhance, not complicate, testing

## Conclusion

Design patterns provide proven solutions to common programming problems. In Python, many patterns can be implemented more simply than in other languages due to Python's dynamic features. The key is understanding when and how to apply patterns appropriately, always favoring clarity and maintainability over rigid adherence to pattern structures.

This catalog serves as a comprehensive reference for implementing design patterns in Python, with each pattern including practical examples and Python-specific implementation guidance.
