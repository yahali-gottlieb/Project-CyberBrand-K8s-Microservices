# Using a fixed Python version, not latest
FROM python:3.10-slim-bullseye

# Create a non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API script
COPY app.py .

# Create logs directory and set ownership to the non-root user
RUN mkdir -p logs && chown -R appuser:appuser /app

# Switch to the non-root user for security
USER appuser

# Expose the API port
EXPOSE 5001

# Start the Flask app
CMD ["python", "app.py"]
