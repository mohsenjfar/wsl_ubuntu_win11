FROM python:3

COPY /backend /code/backend
COPY /tasks /code/tasks
COPY /telegram /code/telegram
COPY requirements.txt /code/requirements.txt
COPY manage.py /code/manage.py

RUN pip3 install -r /code/requirements.txt

CMD python /code/telegram/bot.py

