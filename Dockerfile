FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 \
    libxkbcommon-x11-0 libxcb-xinerama0 libxi-dev libxtst-dev libnss3 libatk-bridge2.0-0 libgtk-3-0 \
    fonts-noto-cjk fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.11 /usr/bin/python

WORKDIR /app

COPY . /app

RUN python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt PyQt5

RUN apt-get update && apt-get install -y locales && rm -rf /var/lib/apt/lists/* && \
    locale-gen en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

ENV DISPLAY=:0

CMD ["python", "main.py"]
