# docker build -t ants3107/gigtag:fe -f Dockerfile-fe --platform=linux/arm64/v8 .
docker build -t ants3107/gigtag:fe -f Dockerfile-fe .
docker push ants3107/gigtag:fe 
