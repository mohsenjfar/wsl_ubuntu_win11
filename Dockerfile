FROM python:3.9.16-slim-buster
COPY requirements.txt /root/requirements.txt
COPY tasks.py /root/tasks.py
RUN pip3 install -r /root/requirements.txt
CMD python /root/tasks.py