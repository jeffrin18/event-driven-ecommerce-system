# order_service/app.py
from flask import Flask, jsonify
import pika

app = Flask(__name__)

@app.route('/create_order', methods=['POST'])
def create_order():
    order = {'product_id': '123', 'quantity': 1}
    
    connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
    channel = connection.channel()
    
    # 1. We declare an 'exchange' (our photocopier)
    channel.exchange_declare(exchange='order_exchange', exchange_type='fanout')
    
    # 2. We publish the message to the EXCHANGE, not the queue
    channel.basic_publish(
        exchange='order_exchange', # Publish to the exchange
        routing_key='',          # routing_key is ignored for fanout
        body=order['product_id'],
        properties=pika.BasicProperties(delivery_mode=2) # Persistent
    )
    
    connection.close()
    
    print(f" [x] Sent message to fanout exchange for product: {order['product_id']}")
    
    return jsonify({"message": "Order created and message sent!"}), 201

if __name__ == '__main__':
    app.run(port=5002, debug=False, host='0.0.0.0')