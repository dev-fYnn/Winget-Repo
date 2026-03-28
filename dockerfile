FROM python:3.13-slim

WORKDIR /wingetrepo

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "./main.py", "/docker"]
