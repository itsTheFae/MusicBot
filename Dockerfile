# This uses an alpine linux based image.
FROM python:3.12-alpine

# Add project source
WORKDIR /musicbot
COPY . ./
COPY ./config sample_config

# Install build dependencies using apline package manager
RUN apk update && apk add --no-cache --virtual .build-deps \
  build-base \
  libffi-dev \
  libsodium-dev

# Install dependencies using apline package manager
RUN apk update && apk add --no-cache \
  ca-certificates \
  ffmpeg \
  opus-dev \
  libffi \
  libsodium \
  gcc \
  git

# Install pip dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Clean up build dependencies from apline package manager
RUN apk del .build-deps

# Create volumes for audio cache, config, data and logs
VOLUME ["/musicbot/audio_cache", "/musicbot/config", "/musicbot/data", "/musicbot/logs", "/musicbot/media"]

ENV APP_ENV=docker

ENTRYPOINT ["/bin/sh", "docker-entrypoint.sh"]
