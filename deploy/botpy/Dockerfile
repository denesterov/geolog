FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git make && apt-get clean

WORKDIR /app

COPY . .

RUN make setup

CMD ["make", "run"]
