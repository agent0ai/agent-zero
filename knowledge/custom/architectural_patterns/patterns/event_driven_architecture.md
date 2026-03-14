# Pattern: Event-Driven Architecture (EDA)

## Overview

Event-Driven Architecture is a design pattern where the flow of the program is determined by events—changes in state or significant occurrences detected by the system.

## In the Context of Agent Jumbo

Agents often operate asynchronously. Using events allows multiple agents to react to the same trigger (e.g., a new email) without direct coupling.

## Trade-offs

| Attribute | Benefit | Drawback |
| :--- | :--- | :--- |
| **Scalability** | High (Asynchronous processing) | Complex debugging (Distributed tracing) |
| **Agility** | High (New consumers can be added) | Eventually consistent data |
| **Performance** | High throughput | Increased latency for single request |

## Deployment on Azure

- **Primary**: Azure Event Grid (for low latency, serverless)
- **Secondary**: Azure Service Bus (for high reliability, FIFO)
- **Logistics**: Azure Event Hubs (for big data/streaming)

## Decision Key

Use EDA when you have:

1. Long-running background tasks.
2. Multiple downstream systems needing the same data.
3. A requirement for high availability and loose coupling.
