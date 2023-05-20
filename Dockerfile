FROM python:3.9.16-slim-buster
COPY requirements.txt requirements.txt
COPY tasks.py tasks.py
RUN pip3 install -r requirements.txt
CMD python tasks.py