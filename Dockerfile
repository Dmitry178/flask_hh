FROM python:3.10-slim
RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . ./
EXPOSE 5000
ENTRYPOINT ["python", "/app/main.py"]
