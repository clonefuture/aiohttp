FROM python:3.9

WORKDIR /aiohttp

COPY . /aiohttp

RUN pip install -r requirements.txt

EXPOSE 8080

CMD [ "python3", "server.py" ]
