# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV=production
ENV FAISS_INDEX_PATH=/app/data/faiss_index.index
ENV LEADS_FILE=/app/data/leads.json
ENV CHAT_HISTORY_FILE=/app/data/chat_history.json
ENV USERS_FILE=/app/data/users.json

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create data directory and initialize files
RUN mkdir -p /app/data && \
    if [ ! -f "$LEADS_FILE" ]; then touch "$LEADS_FILE" && echo "[]" > "$LEADS_FILE"; fi && \
    if [ ! -f "$CHAT_HISTORY_FILE" ]; then touch "$CHAT_HISTORY_FILE" && echo "[]" > "$CHAT_HISTORY_FILE"; fi && \
    if [ ! -f "$USERS_FILE" ]; then touch "$USERS_FILE" && echo "[]" > "$USERS_FILE"; fi

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]