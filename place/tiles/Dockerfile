FROM python:3.10-slim as base

# Any python libraries that require system libraries to be installed will likely
# need the following packages in order to build
RUN apt update && \
    apt -y upgrade && \
    apt install -y build-essential python3-dev libpq-dev && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

FROM base as builder

WORKDIR /app

COPY . /app

RUN pip install -e ./place/tiles
RUN pip install -e ./place/common