import math


class MathUtils:

    @staticmethod
    def tranform_bbox_to_point(array_point):
        x = array_point[0]
        y = array_point[1]
        w = array_point[2]
        h = array_point[3]
        a = x + (w / 2)
        b = y + (h / 2)
        return [a, b]

    @staticmethod
    def is_point_in_polygon(point, poly):
        """
        This function to check if a 2D point (x, y) is in a polygon (zone)
        params:
            - point
            - poly
        """
        x = point[0]
        y = point[1]
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x, p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def caculate_dot(vA, vB):
        return vA[0] * vB[0] + vA[1] * vB[1]

    @staticmethod
    def caculate_angle(lineA, lineB):
        vA = [(lineA[0][0] - lineA[1][0]), (lineA[0][1] - lineA[1][1])]
        vB = [(lineB[0][0] - lineB[1][0]), (lineB[0][1] - lineB[1][1])]
        dot_prod = MathUtils.caculate_dot(vA, vB)
        magA = MathUtils.caculate_dot(vA, vA)**0.5
        magB = MathUtils.caculate_dot(vB, vB)**0.5
        angle = math.acos(dot_prod / magB / magA)
        ang_deg = math.degrees(angle) % 360

        if ang_deg - 180 >= 0:
            return 360 - ang_deg
        else:
            return ang_deg

    @staticmethod
    def is_intersect(A, B, C, D):
        return MathUtils.is_ccw(A, C, D) != MathUtils.is_ccw(B, C, D) and \
            MathUtils.is_ccw(A, B, C) != MathUtils.is_ccw(A, B, D)

    @staticmethod
    def is_ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    @staticmethod
    def calculate_distance(startPoint, endPoint):
        x1 = startPoint[0]
        y1 = startPoint[1]
        x2 = endPoint[0]
        y2 = endPoint[1]
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        return dist
