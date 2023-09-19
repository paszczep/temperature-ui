FROM python:3.11-alpine
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt
COPY application ./application
COPY .env ./
COPY requirements.txt ./
COPY gunicorn_go.sh ./
EXPOSE 5000
CMD gunicorn application:app -w 2 --threads 2 -b 0.0.0.0:5000