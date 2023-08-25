FROM python
LABEL description="A Telegram bot that simplifies global time tracking, synchronization, and conversion with ease"
COPY bot.py /bot.py
COPY en_strings.json /en_strings.json
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
ENTRYPOINT [ "python", "/bot.py" ]
