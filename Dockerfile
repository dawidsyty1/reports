FROM python:3.10

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/

RUN apt update && apt install iproute2 -y

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
   && tar -xzf ta-lib-0.4.0-src.tar.gz \
   && cd ta-lib/ \
   && ./configure  --prefix=/usr \
   && make && make check && make install

WORKDIR /usr/src/app
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
