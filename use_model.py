import cv2

from darknet import YoloDetector

model = YoloDetector()
image = cv2.imread("/home/server-face/face/darknet/Detect_Full_Person/images/data/000000188845.jpg")
a = model.detect(image)
print(a)
bbox = a[0][2][:]
x, y, w, h = bbox
x = int(x)
y = int(y)
w = int(w)
h = int(h)
x1 = int(x - w / 2)
y1 = int(y - h / 2)
x2 = int(x + w / 2)
y2 = int(y + h / 2)
cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)
cv2.imshow("iamge", image)
cv2.waitKey(0)
