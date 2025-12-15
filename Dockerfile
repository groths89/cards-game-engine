# Stage 1: Build Stage - Use a full Python image to compile dependencies
FROM python:3.12 AS builder

WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .

# Install Gunicorn, Eventlet (for async SocketIO), and your dependencies
# NOTE: Eventlet is critical for running SocketIO with Gunicorn
RUN pip install --no-cache-dir gunicorn eventlet 
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final Production Image - Use a smaller, slimmer image for security and size
FROM python:3.12-slim

WORKDIR /app

# Copy installed libraries from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/

COPY . /app

EXPOSE 80

CMD ["./start.sh"]