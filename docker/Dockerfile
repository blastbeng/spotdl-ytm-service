FROM python:3.11-slim-bullseye

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
        ffmpeg \
        locales \
        curl

RUN echo 'vm.overcommit_memory=1' >> /etc/sysctl.conf

RUN sed -i '/it_IT.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG it_IT.UTF-8  
ENV LANGUAGE it_IT:it  
ENV LC_ALL it_IT.UTF-8

COPY requirements.txt .

RUN pip3 install -U pip
RUN pip3 install --no-cache --upgrade pip setuptools
RUN pip3 install wheel
RUN pip3 install --default-timeout=900 -r requirements.txt

WORKDIR /app

COPY app.py .
COPY config.py .
COPY config_gunicorn.py .
COPY get_music.py .
COPY docker/entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p /home/ytmuser/.spotdl/temp
RUN mkdir -p /home/ytmuser/.spotdl/errors
RUN touch /home/ytmuser/.spotdl/.spotify_cache
RUN useradd --create-home ytmuser
RUN chown -R ytmuser:ytmuser /home/ytmuser/.spotdl
RUN chown -R ytmuser:ytmuser /home/ytmuser
RUN chown -R ytmuser:ytmuser /app

USER ytmuser
CMD ["./entrypoint.sh"]
