FROM python:3.11-slim-bullseye

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        ffmpeg

ENV PATH="/home/uwsgi/.local/bin:${PATH}"

COPY requirements.txt .

RUN pip3 install -U pip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install wheel
RUN pip3 install --default-timeout=900 -r requirements.txt

WORKDIR /app

COPY get_music.py .
COPY docker/entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /home/ytmuser/.config/spotdl
RUN useradd --create-home ytmuser
RUN chown -R ytmuser /home/ytmuser
RUN chown -R ytmuser /app

USER ytmuser
CMD ["./entrypoint.sh"]
