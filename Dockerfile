FROM python:3.8-alpine
RUN pip install pipenv
WORKDIR /app
ADD Pipfile /app
RUN pipenv lock --keep-outdated --requirements > requirements.txt
RUN apk --update add gcc build-base
RUN pip install -r requirements.txt
ADD ur_operator /app
CMD kopf run --standalone ur_operator/handlers.py
