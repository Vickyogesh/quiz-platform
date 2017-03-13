FROM ubuntu:16.04
MAINTAINER vertuzz <vertuzz@yandex.ru>

ENV DEBIAN_FRONTEND noninteractive
ENV DOCKER_STATE prod

RUN apt-get update && apt-get install -y \
    python-pip python-dev uwsgi-plugin-python \
    nginx supervisor uwsgi python-mysqldb libmysqlclient-dev \
    openjdk-8-jre unzip
RUN pip install --upgrade pip && pip install --upgrade setuptools
COPY nginx/flask.conf /etc/nginx/sites-available/
COPY nginx/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /var/www/quiz2/data/quiz/img
COPY wsgi /var/www/quiz2/wsgi
COPY web /var/www/quiz2/web
COPY misc /var/www/quiz2/misc
COPY requirements.txt /var/www/quiz2/requirements.txt
COPY manage.py /var/www/quiz2/manage.py
COPY uwsgi.ini /var/www/quiz2/uwsgi.ini
RUN unzip /var/www/quiz2/misc/img.zip -d /var/www/quiz2/data/quiz/img

RUN mkdir -p /var/log/nginx/app /var/log/uwsgi/app /var/log/supervisor \
    && rm /etc/nginx/sites-enabled/default \
    && ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf \
    && echo "daemon off;" >> /etc/nginx/nginx.conf \
    &&  pip install -r /var/www/quiz2/requirements.txt \
    && chown -R www-data:www-data /var/www/quiz2 \
    && chown -R www-data:www-data /var/log

CMD ["/usr/bin/supervisord"]
