# Stage 1: Base build stage
FROM python:3.13-slim AS builder

# Create the app directory
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Copy the requirements file first (better caching)
COPY requirements.txt .

# Install Python dependencies 
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production Stage
FROM python:3.13-slim

# Create a non-root user and app directory
RUN useradd -m -r appuser && \
   mkdir /app && \
   chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the start script
COPY start.sh /app/start.sh

# Set the working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables to optimize python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Switch to non root user
USER appuser

# Expose the application port
EXPOSE 8000

# Use the start script as the entry point
ENTRYPOINT ["/app/start.sh"]
