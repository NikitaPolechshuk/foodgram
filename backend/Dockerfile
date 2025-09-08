FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .

RUN pip install gunicorn==23.0.0 

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]