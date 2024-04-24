FROM debian:bookworm-slim

RUN apt-get update --fix-missing; apt-get -y -q install python3-pip python3-venv git podman

WORKDIR /opt

RUN python3 -m venv env

RUN /opt/env/bin/pip install cwltool
