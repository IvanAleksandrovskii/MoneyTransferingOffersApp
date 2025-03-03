# Use a slim Python runtime as a parent image
FROM python:3.12-slim

# Additional fixing installation for Postgres, needed to work with db with Linux system
RUN apt-get update && apt-get install -y libpq-dev
# Installing netcat
RUN apt-get update && apt-get install -y netcat-openbsd

# Create a working directory
WORKDIR /app

# Copy and install requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files to the container
COPY . /app

# Create media dir for the volume
RUN mkdir -p /app/media && chmod 777 /app/media

# Ensure start.sh has executable permissions
RUN chmod +x /app/start.sh
