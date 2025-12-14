FROM python:3.14-slim

WORKDIR /app
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app

# Default command
CMD ["scrapy", "crawl", "workplacespider"]
