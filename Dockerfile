FROM docker-registry.vnpttiengiang.vn/face/opencv-darknet-py36-base:latest
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip3 install wheel
RUN pip3 install -r /app/requirements.txt
COPY app /app

CMD ["python3 /app/app.py"]
