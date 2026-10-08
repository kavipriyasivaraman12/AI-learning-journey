"""
Learning Journey & Roadmap Service.

Encapsulates business logic for generating, persisting, and reusing learning maps,
integrating with the AI Service Layer and initializing topic progression states.
"""

from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func
from fastapi import HTTPException, status

from app.models.user import User
from app.models.profile import Profile
from app.models.learning_map import LearningMap
from app.models.topic import Topic
from app.models.progress import TopicProgress
from app.schemas.map_schema import LearningMapResponse, TopicSummaryResponse, TopicProgressSummary
from app.services.ai_service import ai_service


# Curated baseline curriculum templates for deterministic flow (25 topics per level)
CURRICULUM_TEMPLATES: Dict[str, Dict[str, List[Dict]]] = {
    "java": {
        "beginner": [
            {"title": "1. Java Evolution & JDK Setup", "description": "JVM, JRE, JDK architecture, environment variables, and compiling your first program.", "difficulty": "Beginner", "minutes": 45},
            {"title": "2. Java Syntax & Primitive Data Types", "description": "Integral, floating-point, boolean, char types, and memory allocation fundamentals.", "difficulty": "Beginner", "minutes": 45},
            {"title": "3. Variables, Literals & Type Casting", "description": "Widening and narrowing casting, variable scope, constants, and final keyword.", "difficulty": "Beginner", "minutes": 45},
            {"title": "4. Arithmetic, Relational & Logical Operators", "description": "Operator precedence, bitwise operations, short-circuit evaluation, and expressions.", "difficulty": "Beginner", "minutes": 45},
            {"title": "5. Decision Control Structures", "description": "if-else branching, nested conditions, ternary operator, and enhanced switch expressions.", "difficulty": "Beginner", "minutes": 50},
            {"title": "6. Loop Constructs & Flow Control", "description": "for, while, do-while loops, nested loops, break, and continue statements.", "difficulty": "Beginner", "minutes": 50},
            {"title": "7. Method Declarations & Parameters", "description": "Signatures, pass-by-value semantics, return types, and method decomposition.", "difficulty": "Beginner", "minutes": 50},
            {"title": "8. Method Overloading & Varargs", "description": "Compile-time polymorphism, variable-length argument lists, and ambiguity resolution.", "difficulty": "Beginner", "minutes": 50},
            {"title": "9. One-Dimensional Arrays", "description": "Array instantiation, memory layout, indexing, traversal, and bounds checking.", "difficulty": "Beginner", "minutes": 50},
            {"title": "10. Multi-Dimensional & Jagged Arrays", "description": "Matrices, nested iteration, jagged array structures, and array utility algorithms.", "difficulty": "Beginner", "minutes": 55},
            {"title": "11. String Fundamentals & Immutability", "description": "String constant pool, reference comparison vs value equality (.equals).", "difficulty": "Beginner", "minutes": 55},
            {"title": "12. StringBuilder & StringBuffer", "description": "Mutable string operations, capacity expansion, and performance optimization.", "difficulty": "Beginner", "minutes": 50},
            {"title": "13. Intro to Classes & Objects", "description": "Class anatomy, object instantiation, state vs behavior, and heap allocation.", "difficulty": "Beginner", "minutes": 60},
            {"title": "14. Constructors & this Keyword", "description": "Default, parameterized, copy constructors, constructor chaining, and shadowing.", "difficulty": "Beginner", "minutes": 55},
            {"title": "15. Encapsulation & Access Modifiers", "description": "public, private, protected, default access, and getter/setter validation patterns.", "difficulty": "Beginner", "minutes": 55},
            {"title": "16. Class Inheritance & Super Keyword", "description": "IS-A hierarchy, single inheritance, super constructor calls, and Object class methods.", "difficulty": "Beginner", "minutes": 60},
            {"title": "17. Method Overriding & Dynamic Dispatch", "description": "Runtime polymorphism, @Override annotation rules, and covariant return types.", "difficulty": "Beginner", "minutes": 60},
            {"title": "18. Abstract Classes vs Concrete Classes", "description": "Abstract methods, partial implementation, and polymorphic base classes.", "difficulty": "Beginner", "minutes": 60},
            {"title": "19. Interfaces & Default Methods", "description": "Multiple contract implementation, default and static interface methods.", "difficulty": "Beginner", "minutes": 60},
            {"title": "20. Java Packages & Classpath", "description": "Package naming conventions, static imports, access levels, and jar packaging.", "difficulty": "Beginner", "minutes": 45},
            {"title": "21. Exception Hierarchy & Try-Catch", "description": "Throwable, Error, Exception, checked vs unchecked exceptions, and multiple catch.", "difficulty": "Beginner", "minutes": 60},
            {"title": "22. Finally Block & Try-with-Resources", "description": "AutoCloseable interface, guaranteed cleanup, and suppressed exceptions.", "difficulty": "Beginner", "minutes": 55},
            {"title": "23. Custom Exceptions & Best Practices", "description": "Defining domain exceptions, exception chaining, and rethrowing idioms.", "difficulty": "Beginner", "minutes": 55},
            {"title": "24. Basic File I/O with Scanner & Files", "description": "Reading and writing text files, Paths, Files API, and IOException handling.", "difficulty": "Beginner", "minutes": 60},
            {"title": "25. Intro to ArrayList & Wrapper Classes", "description": "Autoboxing/unboxing, dynamic resizing, and foundation for Collections.", "difficulty": "Beginner", "minutes": 60},
        ],
        "intermediate": [
            {"title": "1. Java Generics & Type Erasure", "description": "Generic classes, methods, bounded wildcards (? extends, ? super), and bridge methods.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "2. Java Collections: Lists Deep-Dive", "description": "ArrayList vs LinkedList internals, Vector, CopyOnWriteArrayList, and complexity.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "3. Java Collections: Sets & Hashing", "description": "HashSet, LinkedHashSet, TreeSet, hashCode() and equals() contract invariants.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "4. Java Collections: Maps & Tree Structures", "description": "HashMap bucket collisions, Red-Black tree rebalancing, TreeMap, and LinkedHashMap.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "5. Queues, Deques & PriorityQueues", "description": "FIFO queues, double-ended queues, PriorityQueue heap ordering, and custom Comparators.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "6. Comparable vs Comparator Interfaces", "description": "Natural ordering vs custom multi-field sorting pipelines with Comparator chaining.", "difficulty": "Intermediate", "minutes": 55},
            {"title": "7. Lambda Expressions & Method References", "description": "Syntax, functional interface targets, constructor references, and closure scope.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "8. Standard Functional Interfaces", "description": "Predicate, Function, Consumer, Supplier, BiFunction, and primitive specializations.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "9. Stream API: Creation & Intermediate Ops", "description": "filter, map, flatMap, distinct, sorted, peek, and pipeline laziness.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "10. Stream API: Collectors & Reductions", "description": "collect(toList), groupingBy, partitioningBy, reducing, summarizing, and downstream collectors.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "11. Optional Class & Null Safety", "description": "orElse, orElseGet, orElseThrow, map, flatMap, and eliminating NullPointerExceptions.", "difficulty": "Intermediate", "minutes": 50},
            {"title": "12. Java Multi-Threading & Thread Lifecycle", "description": "Thread class, Runnable interface, thread states, join, and daemon threads.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "13. Synchronization & Intrinsic Locks", "description": "synchronized methods, synchronized blocks, wait/notify, and race condition prevention.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "14. Volatile Keyword & Java Memory Model", "description": "Visibility guarantees, happens-before relationship, instruction reordering, and atomicity.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "15. Atomic Variables & CAS Operations", "description": "AtomicInteger, AtomicReference, Compare-And-Swap non-blocking synchronization.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "16. Concurrent Collections", "description": "ConcurrentHashMap lock striping, BlockingQueue producer-consumer patterns.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "17. ExecutorService & Thread Pools", "description": "FixedThreadPool, CachedThreadPool, ScheduledExecutor, Callable, and Future.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "18. CompletableFuture & Async Pipelines", "description": "thenApply, thenCompose, thenCombine, exceptionally, and non-blocking asynchronous flows.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "19. Java NIO.2 Buffers, Channels & Selectors", "description": "Non-blocking I/O, Path, Files modern utility methods, and FileChannel memory mapping.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "20. Reflection API & Dynamic Class Loading", "description": "Inspecting metadata, dynamic instantiation, invoking private fields/methods, and costs.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "21. Custom Annotations & Runtime Processing", "description": "Retention policies, Target elements, reflection processors, and meta-annotations.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "22. Serialization & JSON Processing with Jackson", "description": "Serializable interface, transient fields, ObjectMapper serialization and deserialization.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "23. Relational Databases & JDBC Architecture", "description": "DriverManager, Connection, PreparedStatement, ResultSet, and SQL injection defense.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "24. JDBC Transactions & Connection Pooling", "description": "ACID properties, commit/rollback, savepoints, HikariCP configuration, and performance.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "25. JUnit 5 Testing & Mockito Framework", "description": "Unit test lifecycle, assertions, parameterized tests, test doubles, and mocking services.", "difficulty": "Intermediate", "minutes": 75},
        ],
        "advanced": [
            {"title": "1. Spring Core: Inversion of Control & DI", "description": "BeanFactory, ApplicationContext, Bean lifecycle, scopes, and component scanning.", "difficulty": "Advanced", "minutes": 80},
            {"title": "2. Spring Boot Architecture & Autoconfiguration", "description": "@SpringBootApplication, conditional annotations, starters, and application properties.", "difficulty": "Advanced", "minutes": 80},
            {"title": "3. RESTful API Architecture with Spring Web", "description": "Controllers, RequestMapping, ResponseEntity, validation, and content negotiation.", "difficulty": "Advanced", "minutes": 85},
            {"title": "4. Global Exception Handling in REST APIs", "description": "@ControllerAdvice, @ExceptionHandler, ProblemDetails RFC 7807, and error payloads.", "difficulty": "Advanced", "minutes": 75},
            {"title": "5. Spring Data JPA & Hibernate ORM", "description": "Entity mappings, primary keys, relationships (@OneToMany, @ManyToMany), and JPA Repositories.", "difficulty": "Advanced", "minutes": 90},
            {"title": "6. JPA Query Optimization & N+1 Problem", "description": "JPQL, criteria queries, entity graphs, fetch joins, and Hibernate batch fetching.", "difficulty": "Advanced", "minutes": 90},
            {"title": "7. Hibernate Caching Strategies (L1 & L2)", "description": "Persistence context caching, second-level cache with Ehcache/Redis, and query caching.", "difficulty": "Advanced", "minutes": 80},
            {"title": "8. Spring Security Architecture & Filter Chain", "description": "SecurityFilterChain, AuthenticationManager, UserDetailsService, and PasswordEncoder.", "difficulty": "Advanced", "minutes": 90},
            {"title": "9. Stateless JWT Authentication & RBAC", "description": "JWT token generation, claims verification, Bearer authorization filters, and role guards.", "difficulty": "Advanced", "minutes": 90},
            {"title": "10. Database Migrations with Flyway / Liquibase", "description": "Versioned migration scripts, baseline schemas, rollback strategies, and CI/CD validation.", "difficulty": "Advanced", "minutes": 70},
            {"title": "11. Distributed Caching with Redis in Spring", "description": "Spring Cache abstraction, RedisTemplate, eviction policies, and cache-aside patterns.", "difficulty": "Advanced", "minutes": 85},
            {"title": "12. Microservices Architecture Fundamentals", "description": "Decomposition patterns, domain boundaries, database-per-service, and service discovery.", "difficulty": "Advanced", "minutes": 90},
            {"title": "13. Spring Cloud Gateway & Routing", "description": "Route predicates, gateway filters, rate limiting, and reverse proxy setup.", "difficulty": "Advanced", "minutes": 80},
            {"title": "14. Inter-Service Communication: OpenFeign & RestClient", "description": "Declarative HTTP clients, error decoders, timeout configuration, and load balancing.", "difficulty": "Advanced", "minutes": 80},
            {"title": "15. Asynchronous Messaging with Apache Kafka", "description": "Topics, partitions, consumer groups, KafkaTemplate, @KafkaListener, and message offset commit.", "difficulty": "Advanced", "minutes": 95},
            {"title": "16. Event-Driven Architecture & Transactional Outbox", "description": "Event sourcing, idempotent consumers, Debezium CDC, and transactional outbox pattern.", "difficulty": "Advanced", "minutes": 90},
            {"title": "17. Circuit Breaker & Resilience4j", "description": "Fault tolerance, circuit breaker states, retries, rate limiters, and bulkhead isolation.", "difficulty": "Advanced", "minutes": 85},
            {"title": "18. Distributed Transactions & Saga Pattern", "description": "Two-Phase Commit limits, Orchestration vs Choreography Saga, and compensation logic.", "difficulty": "Advanced", "minutes": 90},
            {"title": "19. Dockerizing Java & Spring Boot Applications", "description": "Multi-stage Docker builds, layered JARs, distroless images, and container best practices.", "difficulty": "Advanced", "minutes": 75},
            {"title": "20. Kubernetes Deployment & Service Orchestration", "description": "Deployments, Services, ConfigMaps, Secrets, liveness/readiness probes, and scaling.", "difficulty": "Advanced", "minutes": 90},
            {"title": "21. JVM Internals: ClassLoading & Bytecode", "description": "Bootstrap/App classloaders, bytecode structure, JIT compiler, and HotSpot optimization.", "difficulty": "Advanced", "minutes": 85},
            {"title": "22. JVM Garbage Collection Algorithms & Tuning", "description": "G1GC, ZGC, Shenandoah, heap analysis, GC log analysis, and latency tuning.", "difficulty": "Advanced", "minutes": 90},
            {"title": "23. Reactive Programming with Spring WebFlux", "description": "Project Reactor, Mono, Flux, backpressure, and non-blocking event loops.", "difficulty": "Advanced", "minutes": 90},
            {"title": "24. Observability: OpenTelemetry, Prometheus & Grafana", "description": "Micrometer metrics, distributed trace IDs, Zipkin/Jaeger, and Grafana dashboards.", "difficulty": "Advanced", "minutes": 85},
            {"title": "25. Enterprise Domain-Driven Design (DDD) & Clean Architecture", "description": "Aggregates, entities, value objects, domain events, hexagonal ports & adapters.", "difficulty": "Advanced", "minutes": 95},
        ],
    },
    "python": {
        "beginner": [
            {"title": "1. Python Setup & Interactive REPL", "description": "CPython interpreter, virtual environments, pip, and script execution.", "difficulty": "Beginner", "minutes": 40},
            {"title": "2. Python Primitive Types & Dynamic Typing", "description": "int, float, bool, NoneType, type inspection, and reference binding.", "difficulty": "Beginner", "minutes": 45},
            {"title": "3. Variables, Naming Rules & Scope", "description": "LEGB rule, global and nonlocal keywords, variable reassignment.", "difficulty": "Beginner", "minutes": 45},
            {"title": "4. Arithmetic, Comparison & Logical Operators", "description": "Operator precedence, chaining comparisons, truthiness and falsiness in Python.", "difficulty": "Beginner", "minutes": 45},
            {"title": "5. Conditional Branching (if, elif, else)", "description": "Indentation rules, boolean expressions, and match-case structural pattern matching.", "difficulty": "Beginner", "minutes": 50},
            {"title": "6. While Loops & Sentinel Values", "description": "Loop condition evaluation, infinite loop guards, break, and continue.", "difficulty": "Beginner", "minutes": 45},
            {"title": "7. For Loops & The range() Function", "description": "Iterating over sequences, step sizing, and loop else clause mechanics.", "difficulty": "Beginner", "minutes": 45},
            {"title": "8. Function Definitions & Return Values", "description": "def statements, return semantics, multiple return tuples, and docstrings.", "difficulty": "Beginner", "minutes": 50},
            {"title": "9. Function Arguments: Positional, Keyword & Defaults", "description": "Default value traps (mutable defaults), keyword arguments, and position-only args.", "difficulty": "Beginner", "minutes": 50},
            {"title": "10. Arbitrary Arguments: *args and **kwargs", "description": "Packing and unpacking sequences/dictionaries into function calls.", "difficulty": "Beginner", "minutes": 50},
            {"title": "11. String Operations & Formatting (f-strings)", "description": "String indexing, slicing, escaping, format specifiers, and string methods.", "difficulty": "Beginner", "minutes": 50},
            {"title": "12. Python Lists: Indexing, Slicing & Mutation", "description": "Dynamic array operations, append, extend, insert, pop, and list mutability.", "difficulty": "Beginner", "minutes": 50},
            {"title": "13. List Comprehensions & Conditional Filtering", "description": "Transforming collections declaratively with concise single-line expressions.", "difficulty": "Beginner", "minutes": 55},
            {"title": "14. Tuples & Sequence Unpacking", "description": "Immutable sequences, tuple unpacking, swap idioms, and namedtuples.", "difficulty": "Beginner", "minutes": 45},
            {"title": "15. Dictionaries: Key-Value Mapping & Operations", "description": "Hash tables, dict methods (.get, .items, .keys, .values), and dict comprehensions.", "difficulty": "Beginner", "minutes": 55},
            {"title": "16. Sets: Uniqueness & Mathematical Set Operations", "description": "Union, intersection, difference, symmetric difference, and fast membership testing.", "difficulty": "Beginner", "minutes": 45},
            {"title": "17. Exception Handling with try, except & finally", "description": "Catching specific exceptions, raise keyword, and resource cleanup with finally.", "difficulty": "Beginner", "minutes": 55},
            {"title": "18. File I/O & Context Managers (with statement)", "description": "Reading and writing text/CSV files safely with automated file closure.", "difficulty": "Beginner", "minutes": 55},
            {"title": "19. Modules, Packages & Import Mechanics", "description": "__init__.py, relative vs absolute imports, sys.path, and standard library overview.", "difficulty": "Beginner", "minutes": 50},
            {"title": "20. Intro to OOP: Classes, Instances & Attributes", "description": "Class definition, __init__ constructor, instance attributes vs class attributes.", "difficulty": "Beginner", "minutes": 60},
            {"title": "21. Methods: Instance, Class (@classmethod) & Static", "description": "self and cls parameters, alternative constructors, and utility methods.", "difficulty": "Beginner", "minutes": 55},
            {"title": "22. OOP Inheritance & super() Mechanics", "description": "Single inheritance, method overriding, and extending base class behavior.", "difficulty": "Beginner", "minutes": 60},
            {"title": "23. Encapsulation & Pythonic Properties (@property)", "description": "Private attribute conventions (_ and __), getters, setters, and deleter descriptors.", "difficulty": "Beginner", "minutes": 55},
            {"title": "24. Basic Python Special Methods (Dunder Methods)", "description": "__str__, __repr__, __len__, __eq__, and customized object representation.", "difficulty": "Beginner", "minutes": 60},
            {"title": "25. Automated Testing with pytest Basics", "description": "Writing test functions, assertions, running pytest, and testing edge cases.", "difficulty": "Beginner", "minutes": 60},
        ],
        "intermediate": [
            {"title": "1. Advanced Python Data Model & Dunder Methods", "description": "__getitem__, __setitem__, __call__, __hash__, and custom container protocols.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "2. Iterators, Iterables & The Iteration Protocol", "description": "__iter__ and __next__, StopIteration handling, and building custom iterators.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "3. Generators & Memory-Efficient Streaming with yield", "description": "Generator functions, generator expressions, send(), and large-dataset streaming.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "4. Closures & First-Class Functions", "description": "Functions as first-class objects, lexical scope preservation, and factory functions.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "5. Python Decorators: Function & Class Wrappers", "description": "functools.wraps, parameterized decorators, chaining decorators, and timing wrappers.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "6. Context Managers & contextlib Utility", "description": "__enter__ and __exit__, contextlib.contextmanager, and transaction boundaries.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "7. Python Type Hints & Static Type Checking with mypy", "description": "typing module (Union, Optional, Callable, Generic), TypeVar, and static verification.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "8. Pydantic v2: Data Parsing & Schema Validation", "description": "BaseModel, Field constraints, model_validator, custom validators, and serialization.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "9. Asynchronous Programming Fundamentals with asyncio", "description": "Event loop, async/await keywords, coroutines, tasks, and asyncio.gather.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "10. Async I/O: Networking & HTTP with httpx/aiohttp", "description": "Concurrent non-blocking HTTP requests, connection pooling, and timeout management.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "11. Relational Databases & SQL with SQLAlchemy Core", "description": "Engine, connection lifecycle, Table schema definitions, and SQL Expression Language.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "12. SQLAlchemy 2.0 ORM: Declarative Models & Mappings", "description": "Mapped, mapped_column, relationships, cascade rules, and database sessions.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "13. Database Migrations with Alembic", "description": "Setting up Alembic, generating revision scripts, upgrade/downgrade migrations.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "14. FastAPI Core: Routing, Path & Query Parameters", "description": "APIRouter, automatic OpenAPI Swagger docs, response models, and status codes.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "15. FastAPI Dependency Injection System", "description": "Depends, database session injection, security dependencies, and sub-dependencies.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "16. User Authentication with Passlib/Bcrypt & PyJWT", "description": "Password hashing, salt generation, JWT token signing, and bearer authentication.", "difficulty": "Intermediate", "minutes": 85},
            {"title": "17. API Error Handling & Custom HTTPExceptions", "description": "Exception handlers, request validation error hooks, and uniform JSON errors.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "18. Concurrency: Threading vs Multiprocessing in Python", "description": "GIL (Global Interpreter Lock) constraints, CPU-bound vs I/O-bound workload choices.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "19. Concurrent Futures & ProcessPoolExecutor", "description": "Parallel processing for computationally intensive tasks with worker pools.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "20. Logging Best Practices & Structlog in Python", "description": "Standard logging configuration, formatters, log rotation, and structured JSON logs.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "21. Advanced Testing with pytest: Fixtures & Parametrization", "description": "Scoped fixtures, monkeypatching, mock objects, and parameterized test matrices.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "22. WebSockets & Real-Time Communication in FastAPI", "description": "WebSocket endpoints, connection managers, broadcasts, and disconnect handling.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "23. Working with Redis for Caching & Session Storage", "description": "Key-value cache, TTL expiration, async redis-py client, and cache-aside patterns.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "24. Background Tasks & Task Queues in Python", "description": "FastAPI BackgroundTasks, Celery task broker overview, and async jobs.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "25. Packaging Python Projects: pyproject.toml & Wheels", "description": "Modern packaging standards, dependency pinning, and build tools (Hatch/Poetry).", "difficulty": "Intermediate", "minutes": 65},
        ],
        "advanced": [
            {"title": "1. Python Metaprogramming & Custom Metaclasses", "description": "type constructor, __new__ vs __init__ in metaclasses, and class registration hooks.", "difficulty": "Advanced", "minutes": 85},
            {"title": "2. Python Descriptors & Attribute Interception", "description": "__get__, __set__, __delete__, __set_name__, and building ORM-like descriptors.", "difficulty": "Advanced", "minutes": 85},
            {"title": "3. CPython Internals & Memory Management", "description": "Reference counting, cyclic garbage collector (gc module), PyObject structure, and arenas.", "difficulty": "Advanced", "minutes": 90},
            {"title": "4. Profiling & Performance Optimization (cProfile & py-spy)", "description": "CPU profiling, memory leak detection (tracemalloc), and hotspot optimization.", "difficulty": "Advanced", "minutes": 80},
            {"title": "5. High-Performance Python: Cython & C Extensions", "description": "Compiling C extensions, ctypes, and bridging Python with low-level libraries.", "difficulty": "Advanced", "minutes": 90},
            {"title": "6. Advanced Asyncio: Protocols, Transports & Custom Loops", "description": "Low-level socket programming, uvloop acceleration, and task cancellation mechanics.", "difficulty": "Advanced", "minutes": 90},
            {"title": "7. Distributed Task Processing with Celery & RabbitMQ", "description": "Task serialization, worker concurrency, retry mechanisms, and dead-letter queues.", "difficulty": "Advanced", "minutes": 90},
            {"title": "8. Enterprise FastAPI Microservices Architecture", "description": "Clean Architecture, repository pattern, domain service layers, and boundary isolation.", "difficulty": "Advanced", "minutes": 95},
            {"title": "9. Advanced SQLAlchemy: Sharding & Read/Write Splitting", "description": "Routing sessions across master-replica databases, composite primary keys, and CTEs.", "difficulty": "Advanced", "minutes": 90},
            {"title": "10. Event-Driven Systems with Kafka & Faust/aiokafka", "description": "Stream processing, consumer offset management, partition rebalancing, and schemas.", "difficulty": "Advanced", "minutes": 95},
            {"title": "11. Distributed Caching & Cache Invalidation with Redis Clusters", "description": "Redis Sentinel, Redis Cluster sharding, pub/sub, distributed locks with Redlock.", "difficulty": "Advanced", "minutes": 90},
            {"title": "12. API Gateway, Rate Limiting & Reverse Proxy Architecture", "description": "Token bucket algorithms, distributed rate limiters, Envoy/Traefik integration.", "difficulty": "Advanced", "minutes": 85},
            {"title": "13. Enterprise Security: OAuth2, OpenID Connect & mTLS", "description": "SSO integrations, authorization code flow with PKCE, and mutual TLS encryption.", "difficulty": "Advanced", "minutes": 90},
            {"title": "14. Microservices Observability: Distributed Tracing with OpenTelemetry", "description": "Trace spans, baggage propagation, Jaeger/Zipkin collectors, and APM instrumentation.", "difficulty": "Advanced", "minutes": 90},
            {"title": "15. Prometheus Metrics & Grafana Alerting for Python APIs", "description": "Prometheus client exporter, counter/gauge/histogram metrics, and SLO/SLA monitoring.", "difficulty": "Advanced", "minutes": 80},
            {"title": "16. Docker Multi-Stage Optimization for Python", "description": "Distroless Python images, wheel caching, non-root user security, and minimal footprints.", "difficulty": "Advanced", "minutes": 75},
            {"title": "17. Kubernetes Orchestration for Python Applications", "description": "StatefulSets, Horizontal Pod Autoscalers (HPA), ingress controllers, and zero-downtime rollouts.", "difficulty": "Advanced", "minutes": 90},
            {"title": "18. Database Performance Tuning: Indexing & Query Plans", "description": "B-Tree vs GIN indexes, EXPLAIN ANALYZE interpretation, and connection pool sizing.", "difficulty": "Advanced", "minutes": 90},
            {"title": "19. Resiliency Patterns: Circuit Breaker, Retries & Bulkheads", "description": "Fault-tolerant network architectures using Tenacity and PyBreaker.", "difficulty": "Advanced", "minutes": 80},
            {"title": "20. Distributed Consensus & Coordination with ZooKeeper / etcd", "description": "Leader election, service registration, distributed configuration synchronization.", "difficulty": "Advanced", "minutes": 90},
            {"title": "21. Eventual Consistency & The Saga Pattern in Python", "description": "Compensating transactions, state machines, and distributed saga orchestrators.", "difficulty": "Advanced", "minutes": 95},
            {"title": "22. GraphQL API Architecture with Strawberry GraphQL", "description": "Types, queries, mutations, subscriptions, dataloaders, and resolving N+1 queries.", "difficulty": "Advanced", "minutes": 85},
            {"title": "23. Machine Learning Inference API Deployment", "description": "Serving ONNX/PyTorch models with batching, GPU acceleration, and Triton server.", "difficulty": "Advanced", "minutes": 95},
            {"title": "24. Load Testing & Chaos Engineering (Locust & Chaos Mesh)", "description": "Simulating high-concurrency traffic, fault injection, latency degradation tests.", "difficulty": "Advanced", "minutes": 85},
            {"title": "25. System Design & Architectural Best Practices", "description": "CAP theorem trade-offs, high availability design, data partitioning, and disaster recovery.", "difficulty": "Advanced", "minutes": 100},
        ],
    },
    "web": {
        "beginner": [
            {"title": "1. Web Architecture & How the Internet Works", "description": "Clients, servers, DNS, HTTP/HTTPS request-response cycle, and web browsers.", "difficulty": "Beginner", "minutes": 45},
            {"title": "2. HTML5 Semantic Elements & Structure", "description": "header, nav, main, section, article, footer, and semantic document hierarchy.", "difficulty": "Beginner", "minutes": 45},
            {"title": "3. HTML Forms, Inputs & Accessibility (a11y)", "description": "Input types, labels, validation attributes, ARIA roles, and screen-reader accessibility.", "difficulty": "Beginner", "minutes": 50},
            {"title": "4. CSS3 Syntax, Selectors & Cascade Specificity", "description": "Class, ID, attribute selectors, pseudo-classes, pseudo-elements, and the cascade.", "difficulty": "Beginner", "minutes": 50},
            {"title": "5. The CSS Box Model & Sizing", "description": "Content, padding, border, margin, box-sizing: border-box, and layout calculations.", "difficulty": "Beginner", "minutes": 50},
            {"title": "6. Modern CSS Layouts: Flexbox Fundamentals", "description": "flex-direction, justify-content, align-items, flex-wrap, and flex item properties.", "difficulty": "Beginner", "minutes": 60},
            {"title": "7. Modern CSS Layouts: CSS Grid Architecture", "description": "Grid templates, grid areas, repeat(), minmax(), auto-fit, and responsive grid patterns.", "difficulty": "Beginner", "minutes": 65},
            {"title": "8. Responsive Web Design & Media Queries", "description": "Mobile-first design principles, viewport meta tag, breakpoints, and fluid typography.", "difficulty": "Beginner", "minutes": 55},
            {"title": "9. CSS Variables (Custom Properties) & Themes", "description": "Declaring custom properties, CSS scoping, and implementing dynamic dark/light themes.", "difficulty": "Beginner", "minutes": 50},
            {"title": "10. Modern JavaScript (ES6+): Variables & Primitives", "description": "let vs const vs var, block scoping, primitive types, and type coercion quirks.", "difficulty": "Beginner", "minutes": 45},
            {"title": "11. JS Functions, Arrow Functions & Scope", "description": "Function declarations vs expressions, arrow function this binding, and closures.", "difficulty": "Beginner", "minutes": 50},
            {"title": "12. Arrays & Modern Array Methods", "description": "map, filter, reduce, find, some, every, forEach, and immutability practices.", "difficulty": "Beginner", "minutes": 60},
            {"title": "13. JavaScript Objects & Destructuring", "description": "Object literals, property shorthand, object & array destructuring, spread/rest syntax.", "difficulty": "Beginner", "minutes": 55},
            {"title": "14. DOM Selection & Manipulation", "description": "querySelector, manipulating innerHTML/textContent, modifying classes and styles.", "difficulty": "Beginner", "minutes": 60},
            {"title": "15. DOM Event Handling & Event Delegation", "description": "addEventListener, event bubbling, event capturing, e.target vs e.currentTarget.", "difficulty": "Beginner", "minutes": 60},
            {"title": "16. Asynchronous JS: Callbacks & Promises", "description": "Event loop basics, callback hell, Promise states, .then(), .catch(), and .finally().", "difficulty": "Beginner", "minutes": 65},
            {"title": "17. Async/Await & Modern Fetch API", "description": "Syntactic sugar for Promises, try/catch error handling, and fetching remote JSON data.", "difficulty": "Beginner", "minutes": 60},
            {"title": "18. Browser Storage: LocalStorage & SessionStorage", "description": "Persistent key-value client storage, JSON serialization, and storage quotas.", "difficulty": "Beginner", "minutes": 45},
            {"title": "19. Introduction to React & JSX Syntax", "description": "Component-based architecture, virtual DOM reconciliation, and JSX expressions.", "difficulty": "Beginner", "minutes": 65},
            {"title": "20. React Components & Props Validation", "description": "Functional components, passing data via props, default props, and component reuse.", "difficulty": "Beginner", "minutes": 60},
            {"title": "21. State Management in React: useState Hook", "description": "Component state, immutable state updates, state lifting, and controlled inputs.", "difficulty": "Beginner", "minutes": 65},
            {"title": "22. Side Effects in React: useEffect Hook", "description": "Dependency array rules, lifecycle synchronization, cleanup functions, and data fetching.", "difficulty": "Beginner", "minutes": 70},
            {"title": "23. React Lists, Keys & Conditional Rendering", "description": "Rendering collections with .map(), key prop significance, ternary and short-circuit rendering.", "difficulty": "Beginner", "minutes": 55},
            {"title": "24. React Forms & Controlled Components", "description": "Handling multi-input forms, submission events, validation, and error feedback.", "difficulty": "Beginner", "minutes": 60},
            {"title": "25. Single Page Application Routing with React Router", "description": "BrowserRouter, Routes, Route, Link, NavLink, useParams, and programmatic navigation.", "difficulty": "Beginner", "minutes": 65},
        ],
        "intermediate": [
            {"title": "1. Advanced React Hooks: useRef & useMemo", "description": "DOM references, mutable instance values, expensive computation memoization.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "2. React useCallback & Component Optimization", "description": "Function reference stability, React.memo, and preventing unnecessary re-renders.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "3. Custom React Hooks Architecture", "description": "Extracting reusable stateful logic (useFetch, useDebounce, useLocalStorage, useAuth).", "difficulty": "Intermediate", "minutes": 75},
            {"title": "4. Global State Management with React Context API", "description": "createContext, useContext, Provider patterns, and state splitting techniques.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "5. Advanced State Management with Redux Toolkit / Zustand", "description": "Store setup, slices, reducers, actions, selectors, and immutable state updates.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "6. Asynchronous State & Caching with React Query / TanStack", "description": "useQuery, useMutation, query caching, background refetching, and optimistic updates.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "7. TypeScript for React Developers", "description": "Typing props, state, events, generic components, and strict type safety.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "8. Modern Styling Solutions: Tailwind CSS", "description": "Utility-first workflow, responsive modifiers, custom themes, and purge optimizations.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "9. CSS-in-JS & CSS Modules Architecture", "description": "Scoped styles, dynamic styling, Styled Components, and modular CSS patterns.", "difficulty": "Intermediate", "minutes": 60},
            {"title": "10. Full Stack REST API Integration & Axios Interceptors", "description": "Centralized API client, JWT injection headers, token refresh, and global error handling.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "11. Web Security: XSS, CSRF & Content Security Policy (CSP)", "description": "Sanitization, HttpOnly cookies, SameSite flags, CORS headers, and security defenses.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "12. Node.js Architecture & Asynchronous Event Loop", "description": "V8 engine, libuv event loop, non-blocking I/O, buffers, and streams in Node.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "13. Express.js / Fastify REST API Framework", "description": "Middleware pipeline, request/response lifecycle, router organization, and controllers.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "14. Database Design & Relational Modeling with PostgreSQL", "description": "Schema normalization (1NF-3NF), foreign keys, indexes, and transactions.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "15. Object-Relational Mapping with Prisma / TypeORM", "description": "Declarative data modeling, migrations, relationships, and type-safe queries.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "16. User Authentication: Session vs Stateless JWT", "description": "Bcrypt password hashing, access & refresh token rotation, and protected routes.", "difficulty": "Intermediate", "minutes": 85},
            {"title": "17. Real-Time Web Applications with Socket.io / WebSockets", "description": "Bi-directional events, rooms, namespaces, reconnection logic, and live updates.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "18. Frontend Performance Optimization & Core Web Vitals", "description": "LCP, FID/INP, CLS metrics, code splitting with React.lazy, and bundle analysis.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "19. Asset Optimization: Images, Fonts & Lazy Loading", "description": "Responsive images (webp/avif), font-display swap, and intersection observer loading.", "difficulty": "Intermediate", "minutes": 65},
            {"title": "20. Unit & Integration Testing with Vitest & React Testing Library", "description": "Testing user interactions, mock service workers (MSW), and assertion best practices.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "21. End-to-End (E2E) Testing with Playwright / Cypress", "description": "Simulating user journeys, automated browser testing, fixtures, and CI reporting.", "difficulty": "Intermediate", "minutes": 80},
            {"title": "22. Progressive Web Apps (PWA) & Service Workers", "description": "Manifest, service worker lifecycle, offline caching strategies, and installability.", "difficulty": "Intermediate", "minutes": 75},
            {"title": "23. Build Automation with Vite & Rollup Bundler", "description": "ESM modules, Hot Module Replacement (HMR), tree shaking, and production chunking.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "24. Git Workflow, Branching Strategies & GitHub Actions", "description": "Trunk-based development, semantic versioning, and automated CI/CD pipelines.", "difficulty": "Intermediate", "minutes": 70},
            {"title": "25. Containerizing Full Stack Apps with Docker & Docker Compose", "description": "Dockerfile best practices, multi-container compose for Frontend, API, and Database.", "difficulty": "Intermediate", "minutes": 80},
        ],
        "advanced": [
            {"title": "1. Next.js App Router: Server Components (RSC) & Streaming", "description": "Server-side rendering (SSR), static site generation (SSG), and Suspense streaming.", "difficulty": "Advanced", "minutes": 90},
            {"title": "2. Next.js Server Actions & Progressive Enhancement", "description": "Form mutations on the server, revalidation, optimistic UI, and type-safe actions.", "difficulty": "Advanced", "minutes": 85},
            {"title": "3. Edge Computing & Serverless Functions (Vercel/Cloudflare Workers)", "description": "Edge runtimes, global low-latency execution, cold start mitigation, and key-value stores.", "difficulty": "Advanced", "minutes": 85},
            {"title": "4. Micro-Frontends Architecture & Module Federation", "description": "Webpack/Vite Module Federation, independent deployments, and shared runtime state.", "difficulty": "Advanced", "minutes": 95},
            {"title": "5. Advanced Web Security: OAuth2, OpenID Connect & WebAuthn", "description": "Passkeys, biometric authentication, PKCE flows, and enterprise SSO integrations.", "difficulty": "Advanced", "minutes": 90},
            {"title": "6. WebAssembly (Wasm) & High-Performance Web Modules", "description": "Compiling Rust/C++ to Wasm, memory sharing, and executing CPU-intensive tasks in browser.", "difficulty": "Advanced", "minutes": 90},
            {"title": "7. GraphQL Federation & Apollo Gateway", "description": "Subgraphs, schema stitching, unified GraphQL supergraphs, and caching strategies.", "difficulty": "Advanced", "minutes": 90},
            {"title": "8. High-Throughput Message Streaming with Kafka / RabbitMQ", "description": "Event-driven backends, message durability, consumer groups, and backpressure handling.", "difficulty": "Advanced", "minutes": 95},
            {"title": "9. Distributed Caching & Invalidation with Redis / CDN", "description": "Stale-While-Revalidate headers, surrogate keys, edge purging, and multi-tier caching.", "difficulty": "Advanced", "minutes": 90},
            {"title": "10. Database Sharding, Partitioning & Master-Replica Routing", "description": "Horizontal scaling for databases, connection pooling with PgBouncer, and read replicas.", "difficulty": "Advanced", "minutes": 95},
            {"title": "11. Real-Time Collaboration Architecture with CRDTs & WebRTC", "description": "Conflict-free replicated data types (Yjs), peer-to-peer data channels, and operational transforms.", "difficulty": "Advanced", "minutes": 95},
            {"title": "12. Distributed Search & Indexing with Elasticsearch / OpenSearch", "description": "Full-text indexing, fuzzy search, inverted index mechanics, and vector embeddings.", "difficulty": "Advanced", "minutes": 90},
            {"title": "13. Resiliency & Chaos Engineering in Web Systems", "description": "Circuit breakers, graceful degradation, bulkhead patterns, and automated failover.", "difficulty": "Advanced", "minutes": 85},
            {"title": "14. API Gateway Design, Rate Limiting & Zero-Trust Mesh", "description": "Envoy proxy, Istio service mesh, mTLS inter-service encryption, and distributed quotas.", "difficulty": "Advanced", "minutes": 95},
            {"title": "15. Cloud Infrastructure as Code (IaC) with Terraform", "description": "Provisioning AWS/GCP resources (VPC, ECS, RDS, CloudFront) declaratively.", "difficulty": "Advanced", "minutes": 90},
            {"title": "16. Kubernetes Deployment & Canary Releases for Web Apps", "description": "ArgoCD GitOps, Helm charts, ingress controllers, and traffic shifting.", "difficulty": "Advanced", "minutes": 95},
            {"title": "17. Web Performance Profiling & Chrome DevTools Memory Heap Analysis", "description": "Memory leaks, JS execution bottlenecks, rendering performance, and compositing layers.", "difficulty": "Advanced", "minutes": 85},
            {"title": "18. Full-Stack Observability: OpenTelemetry, Tracing & APM", "description": "Distributed request traces, Datadog/Sentry integration, and real-user monitoring (RUM).", "difficulty": "Advanced", "minutes": 90},
            {"title": "19. Web Audio, Canvas & WebGL/Three.js Architecture", "description": "Hardware-accelerated 3D graphics rendering, shaders, and interactive data visualization.", "difficulty": "Advanced", "minutes": 90},
            {"title": "20. Accessibility (WCAG 2.1 AAA) & Automated Compliance", "description": "Keyboard navigation traps, color contrast mathematical checks, and axe-core CI audits.", "difficulty": "Advanced", "minutes": 75},
            {"title": "21. Monorepo Architecture with Turborepo / Nx", "description": "Shared packages, caching build artifacts, pipeline execution, and dependency boundaries.", "difficulty": "Advanced", "minutes": 80},
            {"title": "22. Search Engine Optimization (SEO) & Dynamic Metadata Architecture", "description": "JSON-LD structured data, Open Graph, dynamic sitemaps, and indexing strategies.", "difficulty": "Advanced", "minutes": 70},
            {"title": "23. Multi-Tenant SaaS Architecture & Data Isolation", "description": "Tenant schema routing, row-level security (RLS), billing integrations (Stripe), and quotas.", "difficulty": "Advanced", "minutes": 95},
            {"title": "24. Internationalization (i18n) & Localization Architecture", "description": "Pluralization rules, RTL layout support, dynamic bundle loading for languages.", "difficulty": "Advanced", "minutes": 75},
            {"title": "25. Enterprise Full-Stack System Design & Scale Architecture", "description": "Designing high-scale, multi-region, resilient web platforms handling millions of users.", "difficulty": "Advanced", "minutes": 105},
        ],
    },
}


def _get_default_topics_for_goal(goal_title: str, learning_level: str = "beginner") -> List[Dict]:
    """Resolves curriculum topics based on goal keywords and level or provides a 25-topic structured default."""
    lower_goal = goal_title.lower()
    norm_level = (learning_level or "beginner").lower()
    if norm_level not in ["beginner", "intermediate", "advanced"]:
        norm_level = "beginner"

    for key, level_dict in CURRICULUM_TEMPLATES.items():
        if key in lower_goal:
            return level_dict.get(norm_level, level_dict["beginner"])

    # Dynamic 25-topic structured prerequisite chain for any custom subject
    diff_label = norm_level.capitalize()
    return [
        {"title": f"1. Introduction to {goal_title} & Environment Setup", "description": f"Core terminology, architectural overview, and tooling initialization for {goal_title}.", "difficulty": diff_label, "minutes": 45},
        {"title": f"2. Foundational Syntax & Primitives in {goal_title}", "description": f"Core syntax patterns, primitive constructs, and basic execution rules.", "difficulty": diff_label, "minutes": 45},
        {"title": f"3. Variables, Types & Memory Structures", "description": f"Data typing, variable declarations, and memory management principles in {goal_title}.", "difficulty": diff_label, "minutes": 50},
        {"title": f"4. Control Flow & Logical Decision Paths", "description": f"Conditional evaluations, branching logic, and decision structures.", "difficulty": diff_label, "minutes": 50},
        {"title": f"5. Iteration Mechanisms & Looping Constructs", "description": f"Repetitive execution, traversal idioms, and loop control strategies.", "difficulty": diff_label, "minutes": 50},
        {"title": f"6. Modular Functions & Subroutines in {goal_title}", "description": f"Decomposing code into reusable modular functions and parameter handling.", "difficulty": diff_label, "minutes": 55},
        {"title": f"7. Data Collections & Array Structures", "description": f"Sequential data storage, indexing, and core collection manipulation.", "difficulty": diff_label, "minutes": 55},
        {"title": f"8. Key-Value Mappings & Hash Structures", "description": f"Associative data structures, hash tables, and fast lookup patterns.", "difficulty": diff_label, "minutes": 55},
        {"title": f"9. Error Handling & Exception Management", "description": f"Defensive programming, exception hierarchies, and graceful failure recovery.", "difficulty": diff_label, "minutes": 60},
        {"title": f"10. File Operations & Input/Output Streams", "description": f"Reading, writing, and parsing persistent data streams in {goal_title}.", "difficulty": diff_label, "minutes": 60},
        {"title": f"11. Object-Oriented Principles: Abstraction & Classes", "description": f"Modeling domain entities, state encapsulation, and class anatomy.", "difficulty": diff_label, "minutes": 60},
        {"title": f"12. Encapsulation & Access Boundary Control", "description": f"Information hiding, invariant protection, and clean interface boundaries.", "difficulty": diff_label, "minutes": 60},
        {"title": f"13. Inheritance & Hierarchical Classification", "description": f"Code reuse, class hierarchies, and base-to-derived relationships.", "difficulty": diff_label, "minutes": 65},
        {"title": f"14. Polymorphism & Interface Contracts", "description": f"Dynamic method dispatch, contract adherence, and decoupling components.", "difficulty": diff_label, "minutes": 65},
        {"title": f"15. Generics & Type-Safe Parameterization", "description": f"Parameterized types, compile-time safety, and generic algorithm reuse.", "difficulty": diff_label, "minutes": 65},
        {"title": f"16. Concurrency & Parallel Execution Basics", "description": f"Thread models, asynchronous workers, and non-blocking patterns.", "difficulty": diff_label, "minutes": 70},
        {"title": f"17. Asynchronous I/O & Event-Driven Patterns", "description": f"Event loops, promises/futures, and reactive execution flows.", "difficulty": diff_label, "minutes": 70},
        {"title": f"18. Database Integration & Persistence Layer", "description": f"Connecting to relational/NoSQL databases, queries, and ORM abstractions.", "difficulty": diff_label, "minutes": 75},
        {"title": f"19. API Design & RESTful Service Construction", "description": f"Building robust web endpoints, HTTP methods, and payload validation.", "difficulty": diff_label, "minutes": 75},
        {"title": f"20. Security Fundamentals & Authentication Defense", "description": f"Access control, input sanitization, token validation, and encryption in {goal_title}.", "difficulty": diff_label, "minutes": 80},
        {"title": f"21. Automated Unit Testing & Test-Driven Development", "description": f"Writing test suites, mocks, assertions, and verifying edge-case coverage.", "difficulty": diff_label, "minutes": 75},
        {"title": f"22. Performance Profiling & Resource Optimization", "description": f"Memory profiling, CPU hotspot analysis, and algorithmic tuning for {goal_title}.", "difficulty": diff_label, "minutes": 80},
        {"title": f"23. Application Packaging & Containerization (Docker)", "description": f"Containerized builds, environment replication, and dependency isolation.", "difficulty": diff_label, "minutes": 75},
        {"title": f"24. Architecture Patterns & Clean Code Design", "description": f"Layered architecture, dependency injection, and scalable structural idioms.", "difficulty": diff_label, "minutes": 85},
        {"title": f"25. Capstone Integration & Production Deployment", "description": f"End-to-end integration, CI/CD pipelines, and cloud release engineering for {goal_title}.", "difficulty": diff_label, "minutes": 90},
    ]


def get_or_create_learning_map(
    db: Session,
    user: User,
    goal_title: Optional[str] = None,
    learning_level: Optional[str] = None,
    force_regenerate: bool = False,
) -> LearningMap:
    """
    Creates or retrieves a student's personalized learning map:
    1. Resolves goal and learning_level from input parameter or student's profile.
    2. Checks if an active map already exists for this goal AND level (REUSE PRINCIPLE).
    3. If not existing or forced, calls AI Service to generate personalized 25-30 topic roadmap.
    4. Persists LearningMap and child Topic entities in PostgreSQL.
    5. Initializes TopicProgress records (Topic 1: NOT_STARTED, Topics 2+: LOCKED).
    """
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    profile_context = None

    # 1. Resolve target goal & learning level
    resolved_goal = goal_title.strip() if goal_title else None
    if not resolved_goal:
        if profile and profile.target_goal:
            resolved_goal = profile.target_goal.strip()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please specify a goal_title or set up your learning profile first.",
            )

    resolved_level = (learning_level or (profile.current_skill_level if profile else "beginner")).lower()
    if resolved_level not in ["beginner", "intermediate", "advanced"]:
        resolved_level = "beginner"

    if profile:
        profile_context = {
            "education_level": profile.education_level,
            "current_skill_level": resolved_level,
            "weekly_hours_available": profile.weekly_hours_available,
            "preferred_learning_style": profile.preferred_learning_style,
        }

    # 2. Check for existing active map (REUSE PRINCIPLE: same goal AND same level)
    if not force_regenerate:
        existing_map = db.scalar(
            select(LearningMap).where(
                LearningMap.user_id == user.id,
                LearningMap.is_active == True,
                func.lower(LearningMap.goal_title) == resolved_goal.lower(),
                func.lower(LearningMap.learning_level) == resolved_level,
            )
        )
        if existing_map and len(existing_map.topics) >= 25:
            return existing_map

    # 3. Deactivate previous active maps if generating a new one
    db.execute(
        update(LearningMap)
        .where(LearningMap.user_id == user.id)
        .values(is_active=False)
    )

    # 4. Generate structured 25-30 topic roadmap via AI Service Layer
    ai_roadmap = ai_service.generate_learning_roadmap(
        goal_title=resolved_goal,
        profile_context=profile_context,
        learning_level=resolved_level,
    )

    # 5. Create new LearningMap record
    new_map = LearningMap(
        user_id=user.id,
        goal_title=resolved_goal,
        learning_level=resolved_level,
        description=ai_roadmap.description or f"Personalized, adaptive {resolved_level.capitalize()} learning roadmap tailored for {resolved_goal}.",
        is_active=True,
    )
    db.add(new_map)
    db.commit()
    db.refresh(new_map)

    # 6. Populate topics from AI response
    created_topics = []
    for idx, item in enumerate(ai_roadmap.topics, start=1):
        topic = Topic(
            learning_map_id=new_map.id,
            title=item.title,
            description=item.description,
            sequence_order=idx,
            difficulty=item.difficulty or resolved_level.capitalize(),
            estimated_minutes=item.estimated_minutes or 50,
        )
        db.add(topic)
        created_topics.append(topic)

    db.commit()

    # 7. Initialize TopicProgress records for student
    for idx, topic in enumerate(created_topics, start=1):
        # First topic is unlocked (NOT_STARTED); subsequent topics are LOCKED
        initial_status = "NOT_STARTED" if idx == 1 else "LOCKED"
        progress = TopicProgress(
            user_id=user.id,
            topic_id=topic.id,
            status=initial_status,
            mastery_score=0,
        )
        db.add(progress)

    db.commit()
    db.refresh(new_map)
    return new_map


def build_learning_map_response(db: Session, lmap: LearningMap, user_id: str) -> LearningMapResponse:
    """Helper to assemble a LearningMap response with topic cards and attached progress."""
    topic_ids = [t.id for t in lmap.topics]
    progress_records = db.scalars(
        select(TopicProgress).where(
            TopicProgress.user_id == user_id,
            TopicProgress.topic_id.in_(topic_ids),
        )
    ).all()
    progress_by_topic_id = {p.topic_id: p for p in progress_records}

    topics_summary: List[TopicSummaryResponse] = []
    for t in sorted(lmap.topics, key=lambda x: x.sequence_order):
        p_record = progress_by_topic_id.get(t.id)
        prog_summary = None
        if p_record:
            prog_summary = TopicProgressSummary(
                status=p_record.status,
                mastery_score=p_record.mastery_score,
                completed_at=p_record.completed_at,
            )
        topics_summary.append(
            TopicSummaryResponse(
                id=t.id,
                learning_map_id=t.learning_map_id,
                title=t.title,
                description=t.description,
                sequence_order=t.sequence_order,
                difficulty=t.difficulty,
                estimated_minutes=t.estimated_minutes,
                progress=prog_summary,
            )
        )

    return LearningMapResponse(
        id=lmap.id,
        user_id=lmap.user_id,
        goal_title=lmap.goal_title,
        learning_level=getattr(lmap, "learning_level", "beginner") or "beginner",
        description=lmap.description,
        is_active=lmap.is_active,
        created_at=lmap.created_at,
        updated_at=lmap.updated_at,
        topics=topics_summary,
    )
