FROM python:3.8-alpine
LABEL org.opencontainers.image.source https://github.com/brennerm/uptimerobot-operator
ENV KOPF_OPTS="--all-namespaces"
RUN pip install pipenv
WORKDIR /app
ADD Pipfile /app
RUN pipenv lock --keep-outdated --requirements > requirements.txt
RUN apk --update add gcc build-base
RUN pip install -r requirements.txt
ADD ur_operator /app/ur_operator
RUN adduser --disabled-password ur_operator
USER ur_operator
CMD kopf run --standalone $KOPF_OPTS /app/ur_operator/handlers.py
