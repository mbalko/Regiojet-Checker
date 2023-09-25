FROM python:3.10-alpine

ENV DOCKER=1
WORKDIR /app
COPY . .
RUN pip3 install -r requirements.txt

ENTRYPOINT [ "python3", "rjchecker.py" ]
