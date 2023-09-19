FROM python:3.11-alpine
ENV TZ=Europe/Berlin
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt
COPY application ./application
COPY .env ./
COPY requirements.txt ./
EXPOSE 5000
CMD gunicorn application:app -w 2 --threads 2 -b 0.0.0.0:5000