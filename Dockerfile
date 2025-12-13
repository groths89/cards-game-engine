# Stage 1: Build stage for installing dependencies
FROM python:3.9-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Lambda Runtime Stage ---
# Use the official AWS Python base image for container-based Lambda
FROM public.ecr.aws/lambda/python:3.9 

WORKDIR /app

# Copy the application code and the installed dependencies
COPY --from=builder /usr/local/lib/python3.9/site-packages /var/task/
COPY . /var/task/

# Set the handler to your main application file and entry function.
# This is where Lambda will start execution.
# The format is: <file_name>.<function_name>
# You will need to refactor your 'api.api' entry point to expose a handler function.
# Example: api/api.py contains a function named 'lambda_handler'
CMD ["api.api.lambda_handler"]