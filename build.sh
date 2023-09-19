docker build -t temp_ui .
docker tag temp_ui:latest 779378414698.dkr.ecr.eu-central-1.amazonaws.com/temp_ui:latest
#docker run -p 5000:5000 -t temp_ui
