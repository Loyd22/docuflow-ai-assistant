
# Use a smaller official Python runtime image.
FROM python:3.12-slim

# Keep Python logs visible and avoid bytecode files.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# All application files live here.
WORKDIR /app

# Install dependencies before copying application code.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for the application.
RUN useradd --create-home --shell /usr/sbin/nologin appuser

# Copy the application and migration files.
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini ./alembic.ini

# Allow the application user to write temporary uploads.
RUN mkdir -p /app/uploads \
    && chown -R appuser:appuser /app/uploads

# Run the application without root privileges.
USER appuser

# Document the application's internal port.
EXPOSE 8000

# Start FastAPI without development auto-reload.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
