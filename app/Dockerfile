FROM python:3.12

RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/America/Bogota /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata\

&& mkdir /app
WORKDIR /app

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

EXPOSE 8003

CMD ["uvicorn", "app:app", "--host=0.0.0.0","--port=8003","--reload"]
