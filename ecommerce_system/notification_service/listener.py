# notification_service/listener.py
import pika
import time

print(' [*] Notification Service: Waiting for RabbitMQ...')

def start_listener():
    while True:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
            channel = connection.channel()
            
            # 1. We declare the SAME exchange
            channel.exchange_declare(exchange='order_exchange', exchange_type='fanout')
            
            # 2. We create our OWN queue
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue
            
            # 3. We "bind" our queue to the exchange
            channel.queue_bind(exchange='order_exchange', queue=queue_name)
            
            print(f' [*] Notification Listener bound to exchange. Waiting on queue "{queue_name}"')

            def callback(ch, method, properties, body):
                product_id = body.decode()
                
                print(f" [x] NOTIFICATION: 'Sending email' for purchased product: {product_id}")
                
                ch.basic_ack(delivery_tag=method.delivery_tag)
                
            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
            
            channel.start_consuming()
        
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Failed to connect to RabbitMQ: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == '__main__':
    start_listener()