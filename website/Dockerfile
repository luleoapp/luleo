# Use the official Python image.
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential

# Install Poetry
RUN pip install --no-cache-dir poetry

# Set the working directory
WORKDIR /app

# Copy only the necessary files
COPY pyproject.toml poetry.lock /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main

# Copy the rest of the code
COPY . /app

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Set environment variables (optional)
# ENV FLASK_ENV=production

# Command to run the app
CMD ["poetry", "run", "python", "main.py"]