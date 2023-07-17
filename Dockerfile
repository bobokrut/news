FROM arm32v7/python:3.10.10-slim as base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1

WORKDIR /app


FROM base as builder

ENV PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

FROM base as final

COPY . .

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local:$PATH

CMD [ "python", "./main.py" ]
