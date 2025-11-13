# 🚀 Event-Driven E-Commerce Microservices

This is a professional-grade backend system for an e-commerce platform, built using a modern, event-driven microservice architecture.

This project demonstrates a system that is **decoupled**, **scalable**, and **fault-tolerant**. Instead of one giant application, this system is composed of small, independent services that communicate asynchronously using a message broker.

### System Architecture & "Fan-Out" Pattern

When a new order is created, the `Order Service` publishes a single "event" to a "fan-out" exchange. This exchange acts like a photocopier, instantly delivering a *copy* of that event to every service that's listening.

This allows two independent actions to happen at the same time:
1.  The `Product Service` receives the message and reduces the item's stock in the database.
2.  The `Notification Service` receives the *same* message and "sends an email" to the customer.

This is highly impressive because the `Order Service` has **no idea** what happens after it publishes its event. You can add 10 more services (payments, shipping, analytics) without *ever* changing the original `Order Service`.

**Simple Diagram:**
`[Order Service]` -> `[RabbitMQ Exchange]` -> (copy 1) -> `[Product Service]` -> `[PostgreSQL DB]`
` ` -> (copy 2) -> `[Notification Service]`

---

## ✨ Key Features & Tech Stack

* **Microservice Architecture:** Three fully independent services (`order`, `product`, `notification`).
* **Event-Driven:** Services communicate asynchronously using **RabbitMQ** (a message broker).
* **Decoupled & Scalable:** Uses a "Fan-Out" Exchange to trigger multiple actions from one event.
* **Persistent Data:** Uses a **PostgreSQL** database to store product data, which persists even after a full system restart.
* **Containerized:** The entire system (all 4 services) is fully containerized with **Docker** and launched with a single `docker compose` command.

**Tech Stack:**
* **Python (Flask)**: To build the lightweight services.
* **RabbitMQ**: The message broker for event-driven communication.
* **PostgreSQL**: The persistent SQL database for product inventory.
* **Psycopg2**: The Python library to connect to PostgreSQL.
* **Docker & Docker Compose**: To build, run, and manage the entire multi-container application.

---

## 🚀 How to Run

1.  Make sure you have **Docker Desktop** installed and **running**.
2.  Clone this repository.
3.  Open a terminal in the project's root folder.
4.  Run the single command to build and launch the entire system:
    ```bash
    docker compose up --build
    ```
5.  Wait for all services to start. You will see logs indicating the database is initialized and the listeners are connected.

---

## 🧪 How to Test

Once the system is running, you can test the full "fan-out" flow.

**1. "Buy" a Product:**
* Open a **new** terminal.
* Run the following command to simulate an order being placed:
    ```bash
    curl -X POST http://localhost:5002/create_order
    ```
* You will see a response like `{"message":"Order created and message sent!"}`.

**2. Check the Logs:**
* Go back to your main `docker compose` terminal. You will see **both** services react to the single message:
    ```bash
    notification_service-1 |  [x] NOTIFICATION: 'Sending email' for purchased product: 123
    product_service-1      |  [x] PRODUCT: Received order for product: 123
    product_service-1      | Stock for product 123 reduced. New stock: 9
    ```

**3. Verify Persistent Stock:**
* You can check the stock at any time using the `Product Service`'s API:
    ```bash
    curl http://localhost:5001/products
    ```
* You will see the stock for the "Laptop" (ID 123) has been reduced. If you stop (`Ctrl+C`) and restart the system (`docker compose up`), the stock will **remain** at its new value.