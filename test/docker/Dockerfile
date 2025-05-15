FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git make pip && apt-get clean

WORKDIR /app/src
RUN make setup
RUN pip install -r /app/test/requirements-test.txt

WORKDIR /app
CMD ["pytest", "-v", "-c", "/app/test/pytest.ini"] 
