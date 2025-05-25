FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git make pip && apt-get clean

RUN mkdir -p /app/src /app/test

# Copy only requirements files first to cache the setup step
# Note: COPY source path is relative to the build context (project root)
WORKDIR /app/src
COPY src/requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app/test
COPY test/requirements-test.txt .
RUN pip install -r requirements-test.txt

WORKDIR /app
CMD ["pytest", "-vv", "--cov=/app/src", "--cov-report=html:/app/test-results/coverage", "-c", "/app/test/pytest.ini"]
