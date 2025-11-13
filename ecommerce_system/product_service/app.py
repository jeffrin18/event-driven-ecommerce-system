# product_service/app.py
from flask import Flask, jsonify
import pika
import threading
import time
import psycopg2
import os

app = Flask(__name__)

# Get database connection details from environment variables
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_USER = os.environ.get('DB_USER', 'myuser')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'mypassword')
DB_NAME = os.environ.get('DB_NAME', 'ecommerce')

def get_db_connection():
    """Connects to the database. Retries until successful."""
    while True:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            print(" [*] Database: Connection successful.")
            return conn
        except psycopg2.OperationalError as e:
            print(f"Failed to connect to database: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def init_db():
    """Initializes the database, creates the table, and inserts default products."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create the products table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id VARCHAR(10) PRIMARY KEY,
            name VARCHAR(100),
            stock INTEGER
        );
    """)
    
    # Check if the table is empty before inserting
    cur.execute("SELECT COUNT(*) FROM products;")
    if cur.fetchone()[0] == 0:
        print(" [*] Database: No products found, inserting defaults.")
        cur.execute("INSERT INTO products (id, name, stock) VALUES (%s, %s, %s);",
                    ('123', 'Laptop', 10))
        cur.execute("INSERT INTO products (id, name, stock) VALUES (%s, %s, %s);",
                    ('456', 'Mouse', 50))
    else:
        print(" [*] Database: Products already exist.")
        
    conn.commit()
    cur.close()
    conn.close()

def start_listener():
    print(' [*] Product Listener: Waiting for RabbitMQ...')
    
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            channel = connection.channel()
            channel.exchange_declare(exchange='order_exchange', exchange_type='fanout')
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            channel.queue_bind(exchange='order_exchange', queue=queue_name)
            
            print(f' [*] Product Listener bound to exchange. Waiting for messages.')

            def callback(ch, method, properties, body):
                product_id = body.decode()
                print(f" [x] PRODUCT: Received order for product: {product_id}")
                
                # --- THIS IS THE NEW DB LOGIC ---
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # 1. Get current stock
                    cur.execute("SELECT stock FROM products WHERE id = %s;", (product_id,))
                    current_stock = cur.fetchone()
                    
                    if current_stock and current_stock[0] > 0:
                        # 2. Reduce stock
                        new_stock = current_stock[0] - 1
                        cur.execute("UPDATE products SET stock = %s WHERE id = %s;", (new_stock, product_id))
                        conn.commit()
                        print(f"Stock for product {product_id} reduced. New stock: {new_stock}")
                    else:
                        print(f"Product {product_id} not found or out of stock.")
                        
                    cur.close()
                    conn.close()
                except Exception as e:
                    print(f"DB Error in callback: {e}")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
            
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            channel.start_consuming()
        
        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ Connection Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

@app.route('/products')
def get_products():
    """Fetches all products from the database."""
    products = {}
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name, stock FROM products;")
        for row in cur.fetchall():
            products[row[0]] = {'name': row[1], 'stock': row[2]}
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error in /products: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
        
    return jsonify(products)

if __name__ == '__main__':
    # Initialize the database *before* starting anything else
    print(" [*] Main: Initializing Database...")
    init_db()
    
    # Start the RabbitMQ listener
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()
    
    # Start the Flask web server
    print(" [*] Main: Starting Flask server...")
    app.run(port=5001, debug=False, host='0.0.0.0')