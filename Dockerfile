FROM python:3.9.16-slim-buster

COPY /backend /taskerbot/backend
COPY /tasks /taskerbot/tasks
COPY /telegeram /taskerbot/telegram
COPY requirements.txt /taskerbot/requirements.txt
COPY manage.py /taskerbot/manage.py

RUN pip3 install -r /taskerbot/requirements.txt

CMD python /taskerbot/telegram/bot.py