FROM python:3.10.2-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN apk add --update --no-cache --virtual .build-deps libxml2-dev python3-dev musl-dev libxslt-dev gcc
RUN pip3 install --no-cache-dir -r requirements.txt
# RUN apk del .build-deps

COPY . .

CMD [ "python", "./main.py"]
