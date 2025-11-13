# notification_service/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# We just run the listener, no web server needed
CMD ["python", "listener.py"]