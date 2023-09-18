FROM python:3.11-alpine
WORKDIR /application
COPY application ./application
COPY requirements.txt ./
COPY .env ./
COPY asgi.py ./
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
RUN source .env
ENTRYPOINT ["uvicorn"]
CMD ["asgi:asgi_app", "--host", "0.0.0.0", "--port", "5000"]