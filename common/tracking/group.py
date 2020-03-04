class Group_Object():
    def __init__(self,id, total, member, bbox):
        self.__id = id
        self.__total = total
        self.__member = member
        self.__bbox = bbox
    def get_member(self):
        return self.__member

    def get_bbox(self):
        return self.__bbox

    def get_total(self):
        return self.__total

    def get_id(self):
        return self.__id

    def update_bbox(self,bbox):
        self.__bbox = bbox

    def add_member(self,trk_id,element):
        self.__member[trk_id] = element
        self.__bbox = self.__merge_bbox(self.__bbox,element)
        self.__total = len(self.get_member())

    def update_member(self,trk,bbox):
        self.__member[trk]=bbox
        self.__bbox = self.__merge_bbox(self.__bbox,bbox)

    def delete_member(self,trk):
        del self.__member[trk]
        members = self.get_member()
        self.__total = len(members)
        if len(members) > 0:
            bbox_group = [1,1,-1,-1]
            for member in members:
                bbox = members[member]
                bbox_group = self.__merge_bbox(bbox_group,bbox)
            self.__bbox = bbox_group
            return True
        #return false when group empty after delete_member
        return False


    def __merge_bbox(self, bbox_group, bbox2):
        x1, y1, w1, h1 = bbox_group
        x1_bottom = x1 + w1
        y1_bottom = y1 + h1
        x2, y2, w2, h2 = bbox2
        x2_bottom = x2 + w2
        y2_bottom = y2 + h2

        x = x1 if x1 < x2 else x2
        y = y1 if y1 < y2 else y2
        x_bottom = x1_bottom if x1_bottom > x2_bottom else x2_bottom
        y_bottom = y1_bottom if y1_bottom > y2_bottom else y2_bottom
        w = x_bottom - x
        h = y_bottom - y
        return [x, y, w, h]