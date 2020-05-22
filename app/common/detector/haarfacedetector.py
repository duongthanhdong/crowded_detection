import cv2


class HaarCascadeDetector(object):

    def __init__(self, detector_url,crop_image=False, scaleFactor=1.3, minNeighbors=5, minSize=(10, 10)):
        self.face_cascade = cv2.CascadeClassifier(detector_url)
        self.scaleFactor = scaleFactor
        self.minNeighbors = minNeighbors
        self.minSize = minSize
        self.crop_image=crop_image

    def detect(self, frame,minFace=(30,30)):
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray_frame, scaleFactor=self.scaleFactor, minNeighbors=self.minNeighbors, minSize=self.minSize, flags=cv2.CASCADE_SCALE_IMAGE)
        for (x,y,w,h) in faces:
        	if w>=minFace[0] and h>=minFace[1]:
        		if self.crop_image is False:
        			return [x,y,w,h]
        		else:
        			return frame[y:y+w,x:x+w]

