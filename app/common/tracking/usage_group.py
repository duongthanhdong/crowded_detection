import math
from common.tracking.group import Group_Object
from utils.math import bbox_xywh_to_xyxy
import numpy as np
def iou(bb_test,bb_gt):
  """
  Computes IUO between two bboxes in the form [x1,y1,x2,y2]
  """
  xx1 = np.maximum(bb_test[0], bb_gt[0])
  yy1 = np.maximum(bb_test[1], bb_gt[1])
  xx2 = np.minimum(bb_test[2], bb_gt[2])
  yy2 = np.minimum(bb_test[3], bb_gt[3])
  w = np.maximum(0., xx2 - xx1)
  h = np.maximum(0., yy2 - yy1)
  wh = w * h
  o = wh / ((bb_test[2]-bb_test[0])*(bb_test[3]-bb_test[1])
    + (bb_gt[2]-bb_gt[0])*(bb_gt[3]-bb_gt[1]) - wh)
  return(o)

class Usage_Group():
    def __init__(self,thresh_distance, thresh_people, max_age = 1, age = 0):
        self.__manage_group = {}
        self.__thresh_distance = thresh_distance
        self.__thresh_people = thresh_people
        self.__notification = False
        self.__max_age = 1
        self.__age = 0

    def __check_distance(self, last_element, bbox, distance_thresh, img_width, img_height):
        """
        Function to check distance of the object with the previous

        :param last_element: bbox[x,y,w,h] with x,y,w,h in the radio form of image size
        :param bbox: bbox[x,y,w,h] with x,y,w,h in the radio form of image size
        :param distance_thresh: bound of distance that object with the previous
        :param img_width: width of image
        :param img_height: height of image
        :return: True : if distance is less than thresh
                 False : the opposite
        """
        x = last_element[0] * img_width
        y = last_element[1] * img_height
        w = last_element[2] * img_width
        h = last_element[3] * img_height
        x1 = bbox[0] * img_width
        y1 = bbox[1] * img_height
        w1 = bbox[2] * img_width
        h1 = bbox[3] * img_height
        x_center = x + w / 2
        y_center = y + h / 2
        x1_center = x1 + w1 / 2
        y1_center = y1 + h1 / 2
        distance = math.floor(math.sqrt(math.pow(x_center - x1_center, 2) + math.pow(y_center - y1_center, 2)))

        if distance < distance_thresh:
            # push your code into here
            return True
        return False

    def __check_member_belongGroups(self, bbox, width, height,skip_group = None):
        """
        Function to check object whether is belong to group
        :param bbox: bbox
        :param width: pass
        :param height: pass
        :param skip_group:
        :return: list(group belong to)
        """
        # browse through each group in self.face_tracker
        belong_group = []
        for key in self.__manage_group:
            # if skip_group == key:
            #     continue
            # browse through each member in group
            members = self.__manage_group[key].get_member()
            for member in members.keys():
                bbox_group = members[member][:4]
                object_iou = iou(bbox_xywh_to_xyxy(bbox, width, height), bbox_xywh_to_xyxy(bbox_group, width, height))
                if object_iou > 0:
                    belong_group.append(key)
                    break
                check_belong_group = self.__check_distance(bbox, bbox_group, self.__thresh_distance, width, height)
                if check_belong_group:
                    belong_group.append(key)
                    break
        return belong_group

    def __mergeGroup_OR_create_new(self, group_id, bbox, width, height, skip_group=None):
        """
        Funtion to arrange object into group
        :param group_id: index of group (int or unit)
        :param bbox: bounding box in format (x,y,w,h)
        :param width: pass
        :param height: pass
        :param skip_group: pass
        :return: None
        """
        belong_group = self.__check_member_belongGroups(bbox, width, height, skip_group)
        # if the object don't belong to any group
        if len(belong_group) == 0:
            member = {
                group_id: bbox,
            }
            total = 1
            self.__manage_group[group_id] = Group_Object(group_id, total, member, bbox)
        # if it belong to one group only
        # merge the new one object to group that it is belong to
        else:
            self.__manage_group[belong_group[0]].add_member(group_id, bbox)
            # self.__manage_group[]
            for num_group in range(1, len(belong_group)):
                members = self.__manage_group[belong_group[num_group]].get_member()
                for member in members:
                    self.__manage_group[belong_group[0]].add_member(member, members[member])
                del self.__manage_group[belong_group[num_group]]

    def __violate_crow(self):
        self.__age +=1
        # print(self.__age)
        # print("hello")
        if self.__max_age < self.__age:
            return True
        return False

    def __check_violate(self,violate):
        """
        increase age of group , and check condition
        :param violate: group exceed threshold
        :return: True / False
        """
        check = violate
        notification = False
        if check:
            notification = self.__violate_crow() # age +1
            # self.__notification = notification
        else:
            self.__update()
        self.__notification = notification
        return self.__notification

    def __get_list_info_group(self):
        """
        Function to get list group and check violate with condition
        :return: object {
            "violate": True/False,
            'list_info_group': list info group consist of bbox,a number of member.
        }
        """
        list_info_group = []
        violate = False
        for group in self.__manage_group:
            total = self.__manage_group[group].get_total()
            if total >= self.__thresh_people:
                violate = True
            info = {
                "number_member" : total,
                "bbox":self.__manage_group[group].get_bbox(),
                "member": self.__manage_group[group].get_member()
            }
            list_info_group.append(info)
        self.__clear_group()
        check_violate = self.__check_violate(violate)
        result = {
            "violate": check_violate,
            "list_info_group":list_info_group
        }
        return result

    def __clear_group(self):
        self.__manage_group = {}

    def __update(self):
        self.__age = 0

    def process(self, objs, width, height):
        """
        Arrangement object into group and check a number of the group with the threshold and age max

        return: Object :{
                         "violate": if one of the groups violate that is True else False
                         "list_info_group": {
                                            "number_member": int,
                                            "bbox" : [x,y,w,h] in format ratio
                                            }
                        }
        """
        result = {}
        if objs ==[]:
            self.__update()
            result={
                "violate":False,
                "list_info_group":{},
            }
        else:
            for i, obj in enumerate(objs):
                bbox = obj["bbox"]
                self.__mergeGroup_OR_create_new(i, bbox, width, height)
            result = self.__get_list_info_group()
        return result



