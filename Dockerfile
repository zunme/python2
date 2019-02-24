FROM python:3.6-stretch

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./
RUN pyarmor obfuscate index.py
RUN rm index.py

RUN mv ./config ./dist/config

RUN rm -f requirements.txt

CMD [ "python", "./dist/index.py" ]
