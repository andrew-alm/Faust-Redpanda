FROM python:3.11.0

RUN mkdir /app
RUN pip install pipenv

COPY Pipfile .
RUN pipenv install --deploy

WORKDIR /app

COPY entrypoint.sh .
COPY reddit_app.py /app

CMD ["./entrypoint.sh"]