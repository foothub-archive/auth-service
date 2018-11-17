FROM python:3.6
ENV PYTHONUNBUFFERED 1

RUN pip3.6 install pipenv

COPY . code
WORKDIR /code
RUN pipenv install --system --deploy --dev
EXPOSE 8000

CMD cd auth && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --access-logfile - auth.wsgi:application
