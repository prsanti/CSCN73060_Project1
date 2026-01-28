FROM python:3-slim

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

EXPOSE 7500

CMD ["python", "app.py"]