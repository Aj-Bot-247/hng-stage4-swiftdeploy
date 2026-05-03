# Use Alpine Linux for an ultra-lightweight image (< 300MB)
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app/

# Create a non-root user and switch to it for security
RUN adduser -D appuser && chown -R appuser /app
USER appuser

# Expose a default port (though Compose will override this)
EXPOSE 3000

# Run Gunicorn, binding to the APP_PORT environment variable (default 3000)
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${APP_PORT:-3000} app.main:app"]