FROM python:3.11-alpine
COPY application ./application
COPY requirements.txt ./
COPY .env ./
RUN pip install -r requirements.txt
EXPOSE 5000
RUN source .env
ENTRYPOINT ["flask"]
CMD ["run"]