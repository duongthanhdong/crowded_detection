from __future__ import print_function
import logging

import grpc
from services.grpc import helloworld_pb2, helloworld_pb2_grpc
import cv2
import time

ip = 'localhost'
port = "50051"


class Client_gRPC():

    def __init__(self, url_server_serving):
        logging.warning("Init gRPC Client")
        self.__channel = grpc.insecure_channel(url_server_serving)
        self.__stub = helloworld_pb2_grpc.GreeterStub(self.__channel)
        logging.warning("Successful")


    def send_request(self, image):
        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        byte_im = im_buf_arr.tobytes()
        response = self.__stub.SayHello(helloworld_pb2.HelloRequest(name="thanh dong", img=byte_im))
        return response.message
