FROM python:3.11-alpine

WORKDIR /usr/src/app

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir click https://github.com/HumanBrainProject/fairgraph/archive/refs/heads/master.zip

COPY download_KG_datafile.py download_KG_datafile.py
RUN chmod +x download_KG_datafile.py

ENV PATH="/usr/src/app:$PATH"

CMD [ "/bin/sh" ]
