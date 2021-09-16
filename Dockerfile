FROM python:alpine3.6

RUN apk add --no-cache --update \
    --no-cache build-base libffi-dev gcc libc6-compat \
    curl \
    bash \
    linux-headers


WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000

CMD ["flask", "run", "--host", "0.0.0.0"]