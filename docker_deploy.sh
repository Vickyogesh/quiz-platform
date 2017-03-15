#!/bin/bash

# Clean untagged docker images (trash)
docker rmi $(docker images -a | grep "^<none>" | awk '{print $3}')

docker build . -t quiz;

docker-compose down;

docker-compose up -d --force-recreate;
