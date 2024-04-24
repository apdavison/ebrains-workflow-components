FROM debian:bookworm-slim

RUN apt-get update --fix-missing; apt-get -y -q install python3-pip git docker.io
RUN apt-get install -y python3-venv

WORKDIR /opt

RUN python3 -m venv env

RUN /opt/env/bin/pip install cwltool
