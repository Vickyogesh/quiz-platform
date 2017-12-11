#!/bin/bash

docker-compose down;

# Clean untagged docker images (trash)
docker rmi $(docker images -a | grep "^<none>" | awk '{print $3}')

docker build . -t quiz;

if [ $APP_PROD = 1 ]
then
    echo "Production env"
    docker build nginx -f nginx/Dockerfile-prod -t front_proxy;
else
    echo "Development env"
    docker build nginx -f nginx/Dockerfile-dev -t front_proxy;
fi

docker-compose up -d --force-recreate;
