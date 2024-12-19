FROM python:3.11-slim

# install dependencies
RUN pip install --no-cache-dir argparse requests

# copy python script, make executable and add to path
COPY bucket_push_file.py /home/tool/bucket_push_file.py
RUN chmod +x /home/tool/bucket_push_file.py
ENV PATH="/home/tool:$PATH"

CMD [ "/bin/bash" ]
