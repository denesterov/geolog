# Use official Python 3 base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install git and other dependencies
RUN apt-get update && apt-get install -y git && apt-get clean

# Set working directory
WORKDIR /app

# Clone the GitHub repository (replace URL with actual repo)
RUN git clone https://github.com/<username>/<repo>.git . 

# Install Python dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Command to run your bot (adjust based on your repo)
CMD ["python", "bot.py"]
