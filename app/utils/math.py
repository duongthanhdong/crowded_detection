

# Convert inner bbox of object (license plate) to coordinate of frame
def bbox_abs(inner, outer):
    x = outer[0] + inner[0] * outer[2]
    y = outer[1] + inner[1] * outer[3]
    w = inner[2] * outer[2]
    h = inner[3] * outer[3]

    return [x, y, w, h]


def bbox_xyxy_to_xywh(xywh, width=1, height=1):
    x = int(xywh[0] * width)
    y = int(xywh[1] * height)
    w = int((xywh[2] - xywh[0]) * width)
    h = int((xywh[3] - xywh[1]) * height)
    return [x, y, w, h]


def bbox_xywh_to_xyxy(xywh, width=1, height=1):
    x1 = xywh[0] * width
    y1 = xywh[1] * height
    x2 = (xywh[0] + xywh[2]) * width
    y2 = (xywh[1] + xywh[3]) * height

    if x1 < 0:
        x1 = 0
    if x2 > width:
        x2 = width
    if y1 < 0:
        y1 = 0
    if y2 > height:
        y2 = height
    return [x1, y1, x2, y2]


def bbox_pixel_to_relative(xywh, width, height):
    x = xywh[0] / width
    y = xywh[1] / height
    w = xywh[2] / width
    h = xywh[3] / height

    return [x, y, w, h]

def bbox_to_scale_bbox(xyxy, width, height):
    x1 = int(xyxy[0] * width)
    y1 = int(xyxy[1] * height)
    x2 = int(xyxy[2] * width)
    y2 = int(xyxy[3] * height)
    return [x1,y1,x2,y2]