FROM python:3.10.3-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
# RUN apk del .build-deps

COPY . .

CMD [ "python", "./main.py"]
