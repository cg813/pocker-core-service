############
# BUILDER ##
############

# pull offical base image
FROM python:3.9.9-slim-buster as builder

# set work direcotry
WORKDIR /usr/src/app


# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# install system dependencies
RUN apt-get update \
  && apt-get -y install netcat gcc postgresql \
  && apt-get clean
## install psycopg2 dependencies
#RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
#RUN apk update \
#    && apk add alpine-sdk gcc musl-dev python3-dev libffi-dev openssl-dev cargo jpeg-dev zlib-dev ffmpeg
#
# lint
RUN pip install --upgrade pip
COPY . .

# install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt


##########
# FINAL #
##########

# pull official base image

FROM python:3.9.9-slim-buster

# create direcotry for the app user
RUN mkdir -p /home/app

# create the app user
#RUN #addgroup -S app && adduser -S app -G app
RUN addgroup --system app && adduser --system --group app

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

RUN pip install --upgrade pip
# install dependencies
COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --no-cache /wheels/*
# copy entrypoint-prod.sh
COPY entrypoint.prod.sh  $APP_HOME

# copy project
COPY . $APP_HOME

RUN mkdir $APP_HOME/config/staticfiles
# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# run entrypoint.prod.sh
#entrypoint.prod.sh
#ENTRYPOINT ["/home/app/web/entrypoint.prod.sh"]
