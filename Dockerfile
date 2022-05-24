FROM python:3.8-alpine
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /requirements.txt
RUN apk add --update --no-cache --virtual .tmp gcc libc-dev linux-headers
RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add libffi-dev

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir pillow
RUN pip install --no-cache-dir cffi

RUN pip install -r /requirements.txt
RUN apk del .tmp

RUN mkdir /MyChatApp
COPY ./src /MyChatApp
WORKDIR /MyChatApp



