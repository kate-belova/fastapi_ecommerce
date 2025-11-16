FROM python:3.12-alpine

ENV HOME=/home/fast \
    APP_HOME=/home/fast/app \
    PYTHONPATH="$PYTHONPATH:/home/fast" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup -S fast && adduser -S fast -G fast

WORKDIR $HOME

COPY ./requirements.txt ./

RUN apk update && apk add --no-cache \
    postgresql-dev \
    gcc \
    python3-dev \
    musl-dev \
    libffi-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del --purge gcc python3-dev musl-dev libffi-dev

COPY ./app $APP_HOME
COPY ./alembic.ini ./

RUN chown -R fast:fast $HOME

USER fast

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]