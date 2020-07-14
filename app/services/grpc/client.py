# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the GRPC helloworld.Greeter client."""

from __future__ import print_function
import logging

import grpc
import helloworld_pb2
import helloworld_pb2_grpc
import cv2
import time 
import json

def drawing_frame( frame, objs):
        height_ori, width_ori = frame.shape[:2]
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 0, 255), (128, 0, 0),
                  (0, 128, 0), (0, 0, 128), (128, 0, 128), (128, 128, 0), (0, 128, 128)]
        if objs != None:
            for obj in objs:
                name = obj['name']
                class_id = obj['class_id']
                prob = obj['prob']
                x = int(obj['bbox'][0] * width_ori)
                y = int(obj['bbox'][1] * height_ori)
                w = int(obj['bbox'][2] * width_ori)
                h = int(obj['bbox'][3] * height_ori)
                cv2.rectangle(frame, (x, y), (x + w, y + h), colors[class_id], 2)

                str_display = str(name) + "||" + str(round(prob, 2)) + "||" + str(class_id)
                y_backgroud_classes = y - 35 if y > 30 else y + 35
                y_classes = y - 10 if y > 30 else y_backgroud_classes - 10
                # cv2.rectangle(frame, (x, y_backgroud_classes), (x + len(str_display) * 19 + 10, y), (200,255,255), -1)
                cv2.putText(frame, str(round(prob, 2)), (x + 5, y_classes),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, colors[class_id], 3)

def run():
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    with grpc.insecure_channel('192.168.1.45:50051') as channel:
        stub = helloworld_pb2_grpc.GreeterStub(channel)

        image = cv2.imread('test.jpg')
        image = cv2.resize(image, (300, 300))

        is_success, im_buf_arr = cv2.imencode(".jpg", image)
        byte_im = im_buf_arr.tobytes()
        files = {'body': byte_im}

        while 1:
            start = time.time()
            response = stub.SayHello(helloworld_pb2.HelloRequest(name="thanh dong", img=byte_im))
            end = time.time()
            elapsed = end - start
            fps = 1/ elapsed
            print(elapsed, fps) 
            detection = response.message
            # print(detection)

            # detection = json.loads(detection)
            # print(type(detection))
            # drawing_frame(image, detection )
            # cv2.imshow("image",cv2.resize(image,(800,600)))
            # cv2.waitKey(0)
            
        # print("Greeter client received: " + messages)

        # response = stub.SayHelloAgain(helloworld_pb2.HelloRequest(name='Bao'))
        # print("Greeter client received: " + response.message)


if __name__ == '__main__':
    logging.basicConfig()
    run()
