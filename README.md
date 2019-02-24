docker run --name py -d zunme/pyimg:latest /bin/sh -c "while true; do ping 8.8.8.8 -i 10; done"
docker run --name py -d -v /data/docker/myapp/config:/usr/src/app/dist/config zunme/pyimg:latest 
docker run -it --rm --name my_py_app zunme/pyimg:latest
docker run -it --rm --name my_py_app -v /data/docker/myapp/config:/usr/src/app/dist/config zunme/pyimg:latest
