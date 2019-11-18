FROM python:3.7

RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y postgresql postgresql-contrib supervisor gettext pandoc  && \
    pip3 install uwsgi


RUN mkdir /app

COPY ./requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt

RUN mkdir -p /app

ENV DJANGO_LOG_FILE=logfile.log

COPY ./ /app/

RUN mkdir -p /app/data/logs && \
  mkdir -p /app/data/media && \
  mkdir -p /app/static && \
  touch /app/data/logs/$DJANGO_LOG_FILE

RUN python /app/manage.py migrate
RUN python /app/manage.py collectstatic --noinput


WORKDIR /app

ENV APP_MODE=web
# APP_MODE web | celery

EXPOSE 80

VOLUME ["/app/data"]
# Server

STOPSIGNAL SIGINT
CMD /usr/sbin/sshd \
    mkdir -p /app/data/logs; \
    mkdir -p /app/data/media; \
    touch /app/data/logs/$DJANGO_LOG_FILE; \
    sh -c 'ln -s /dev/null /dev/raw1394'; \
    echo "Running with APP_MODE='$APP_MODE'"; \
    supervisord -n -c /app/deploy/supervisord_$APP_MODE.conf; \
