FROM python:3.6-alpine

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./
COPY _pytransform.so /usr/local/lib/python3.6/site-packages/pyarmor/platforms/linux64/_pytransform.so

RUN pyarmor obfuscate index.py
RUN rm index.py

RUN mv ./config ./dist/config

RUN rm -f requirements.txt

CMD [ "python", "./dist/index.py" ]
