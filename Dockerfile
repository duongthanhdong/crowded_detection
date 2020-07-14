FROM python:3.7-buster
WORKDIR app
COPY requirement.txt /app

#RUN echo 'deb http://www.rabbitmq.com/debian/ testing main' |  tee /etc/apt/sources.list.d/rabbitmq.list
#RUN wget -O- https://www.rabbitmq.com/rabbitmq-release-signing-key.asc |  apt-key add -
#RUN apt-get update
#RUN apt-get -y install rabbitmq-server

RUN pip3 install wheel
RUN pip3 install -r /app/requirement.txt
COPY app /app

