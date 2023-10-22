FROM python:3.11-slim 
LABEL description="A Telegram bot that simplifies global time tracking, synchronization, and conversion with ease"
COPY main.py /main.py
COPY bot.py /bot.py
COPY utils.py /utils.py
COPY en_strings.json /en_strings.json
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt
ENTRYPOINT [ "python", "/main.py" ]
