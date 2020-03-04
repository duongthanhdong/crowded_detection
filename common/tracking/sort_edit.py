from __future__ import print_function
import uuid
import numpy as np
from scipy.optimize import linear_sum_assignment
import argparse
from filterpy.kalman import KalmanFilter
import math
from crowed_detection.utils.math import bbox_xywh_to_xyxy

from .group import Group_Object

import logging
import cv2
from PIL import Image
from datetime import datetime
import os

import trafficlight
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

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

def convert_bbox_to_z(bbox):
  """
  Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
    [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
    the aspect ratio
  """
  w = bbox[2]-bbox[0]
  h = bbox[3]-bbox[1]
  x = bbox[0]+w/2.
  y = bbox[1]+h/2.
  s = w*h    #scale is just area
  r = w/float(h)
  return np.array([x,y,s,r]).reshape((4,1))

def convert_x_to_bbox(x,score=None,cls=None):
  """
  Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
    [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
  """
  w = np.sqrt(x[2]*x[3])
  h = x[2]/w
  if(score==None or cls==None):
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.]).reshape((1,4))
  else:
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.,[score],[cls]]).reshape((1,6))

def convert_xyxy_2_rxywh(objs,width,height):
  x, y, x1, y1 = objs[:4]
  # print(width,height)
  # print(objs[:4])
  w = (x1-x) / width
  h = (y1-y) / height
  x = x/width
  y = y/height
  objs[:4] = x,y,w,h
  return objs



class KalmanBoxTracker(object):
  """
  This class represents the internel state of individual tracked objects observed as bbox.
  """
  count = 0
  def __init__(self,bbox,name,track_id=None):
    """
    Initialises a tracker using initial bounding box.
    """
    #define constant velocity model
    self.kf = KalmanFilter(dim_x=7, dim_z=4)
    self.kf.F = np.array([[1,0,0,0,1,0,0],[0,1,0,0,0,1,0],[0,0,1,0,0,0,1],[0,0,0,1,0,0,0],  [0,0,0,0,1,0,0],[0,0,0,0,0,1,0],[0,0,0,0,0,0,1]])
    self.kf.H = np.array([[1,0,0,0,0,0,0],[0,1,0,0,0,0,0],[0,0,1,0,0,0,0],[0,0,0,1,0,0,0]])

    self.kf.R[2:,2:] *= 10.
    self.kf.P[4:,4:] *= 1000. #give high uncertainty to the unobservable initial velocities
    self.kf.P *= 10.
    self.kf.Q[-1,-1] *= 0.01
    self.kf.Q[4:,4:] *= 0.01

    ##START EDIT
    self.cls = bbox[5]
    self.prob = bbox[4]
    self.id = track_id if track_id else uuid.uuid4()
    self.name = name
    #END EDIT
    self.kf.x[:4] = convert_bbox_to_z(bbox[:4])
    self.time_since_update = 0
    # KalmanBoxTracker.count = uuid.uuid4()
    # self.id = KalmanBoxTracker.count
    self.history = []
    self.hits = 0
    self.hit_streak = 0
    self.age = 0

  def update(self,bbox):
    """
    Updates the state vector with observed bbox.
    """
    self.time_since_update = 0
    self.history = []
    self.hits += 1
    self.hit_streak += 1
    self.kf.update(convert_bbox_to_z(bbox))
    #edit from here
    self.prob=bbox[4]
    self.cls = bbox[5]

  def predict(self):
    """
    Advances the state vector and returns the predicted bounding box estimate.
    """
    if((self.kf.x[6]+self.kf.x[2])<=0):
      self.kf.x[6] *= 0.0
    self.kf.predict()
    self.age += 1
    if(self.time_since_update>0):
      self.hit_streak = 0
    self.time_since_update += 1
    self.history.append(convert_x_to_bbox(self.kf.x,score=self.prob,cls=self.cls))
    return self.history[-1]

  def get_state(self):
    """
    Returns the current bounding box estimate.
    """
    return convert_x_to_bbox(self.kf.x,score=self.prob,cls=self.cls)



  # def is_missed(self):
  #   if self.time_since_update >= self.max_age:
  #     return True
  #   return False
  #
  # def is_confirmed(self):
  #   return self.hits > 0

def associate_detections_to_trackers(detections,trackers,iou_threshold = 0.3):
  """
  Assigns detections to tracked object (both represented as bounding boxes)

  Returns 3 lists of matches, unmatched_detections and unmatched_trackers
  """
  if(len(trackers)==0):
    return np.empty((0,2),dtype=int), np.arange(len(detections)), np.empty((0,5),dtype=int)
  iou_matrix = np.zeros((len(detections),len(trackers)),dtype=np.float32)
  # print(iou_matrix.shape)

  for d,det in enumerate(detections):
    for t,trk in enumerate(trackers):
      iou_matrix[d,t] = iou(det,trk)

  # matched_indices = linear_assignment(-iou_matrix)
  matched_indices = linear_sum_assignment(-iou_matrix)
  matched_indices=np.transpose(np.asarray(matched_indices))

  unmatched_detections = []
  for d,det in enumerate(detections):
    if(d not in matched_indices[:,0]):
      unmatched_detections.append(d)
  unmatched_trackers = []
  for t,trk in enumerate(trackers):
    if(t not in matched_indices[:,1]):
      unmatched_trackers.append(t)

  #filter out matched with low IOU
  matches = []
  for m in matched_indices:
    if(iou_matrix[m[0],m[1]]<iou_threshold):
      unmatched_detections.append(m[0])
      unmatched_trackers.append(m[1])
    else:
      matches.append(m.reshape(1,2))
  if(len(matches)==0):
    matches = np.empty((0,2),dtype=int)
  else:
    matches = np.concatenate(matches,axis=0)

  return matches, np.array(unmatched_detections), np.array(unmatched_trackers)

class Sort(object):
  def __init__(self,height=1920,width=1080,max_age=10,min_hits=5):
    """
    Sets key parameters for SORT
    """
    self.max_age = max_age
    self.min_hits = min_hits
    self.trackers = {}
    self.frame_count = 0
    self.manage_group = {}
    self.height = height
    self.width = width
    self.thresh_distance = open('data.txt','r').read().split('\n')[0]

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

  def __get_member_group(self,trk_id):
    for group in self.manage_group:
      members = self.manage_group[group].get_member()
      for member in members:
        if trk_id == member:
          return group
    return False

  def __surviral_inGroup(self,group,trk_id,bbox,height,width):
    members = self.manage_group[group].get_member()
    for member in members:
      if member == trk_id:
        continue
      check_distance = self.__check_distance(members[member],bbox,self.thresh_distance,width,height)
      if check_distance:
        return check_distance
    return False

  def __check_member_belongGroups(self,bbox,width,height,skip_group):
    # browse through each group in self.face_tracker
    belong_group = []
    for key in self.manage_group:
      if skip_group == key:
        continue
      # browse through each member in group
      members = self.manage_group[key].get_member()
      for member in members.keys():
        bbox_group = members[member][:4]
        object_iou =iou(bbox_xywh_to_xyxy(bbox,width,height),bbox_xywh_to_xyxy(bbox_group,width,height))
        if object_iou > 0 :
          belong_group.append(key)
          continue
        check_belong_group = self.__check_distance(bbox, bbox_group, self.thresh_distance, width, height)
        if check_belong_group:
          belong_group.append(key)
    return belong_group

  def __mergeGroup_OR_create_new(self,group_id,bbox,width,height,skip_group=None):
    belong_group = self.__check_member_belongGroups(bbox, width, height,skip_group)
    # if the object don't belong to any group
    if len(belong_group) == 0:
      member = {
        group_id: bbox,
      }
      total = 1
      self.manage_group[group_id] = Group_Object(group_id, total, member, bbox)

    # if it belong to one group only
    # merge the new one object to group that it is belong to
    else:
      self.manage_group[belong_group[0]].add_member(group_id, bbox)
      # self.manage_group[]
      for num_group in range(1, len(belong_group)):
        members = self.manage_group[belong_group[num_group]].get_member()
        for member in members:
          self.manage_group[belong_group[0]].add_member(member, members[member])
        del self.manage_group[belong_group[num_group]]

  def __delete_member(self,group,trk_id):
    delete_member = self.manage_group[group].delete_member(trk_id)
    #if group is empty after delete action finished .Remove group
    if not delete_member:
      del self.manage_group[group]

  def __new_object(self,group_id,d,height,width):
    bbox = d[:4]
    if len(self.manage_group) == 0:
      member = {
        group_id : bbox,
        }
      total = 1
      self.manage_group[group_id] = Group_Object(group_id, total, member, bbox)
    else :
      self.__mergeGroup_OR_create_new(group_id,bbox,width,height)


  def update(self, objs, frames, track_num_skip,img):
    """
    :param objs: Dictionary include info of the objects
    :param frames: number about frame in stream flow
    :param track_num_skip: number of frame which will capture in tracking object
    :param img: image which will serve for width and height to convert bounding box
    :return:
        - track : the current object of in KalmanFilter
        - follow : include info about objects when the tracking process is finished
    """
    self.frame_count += 1
    #get predicted locations from existing trackers.
    trks = np.zeros((len(self.trackers),5))
    to_del = []
    ret = []
    dets = []
    dead_id = []
    follow = {}
    frame_id = None
    gettime = None
    height,width = img.shape[:2]
    #read box detect received
    for obj in objs:
        bbox = bbox_xywh_to_xyxy(obj['bbox'],width,height)
        dets.append([bbox[0],bbox[1],bbox[2],bbox[3],obj['prob'],obj['class_id']])
    np.set_printoptions(formatter={'float': lambda x: "{0:0.3f}".format(x)})
    dets = np.asarray(dets)
    if len(objs) > 0:
      frame_id = objs[0]['frame_id']
      gettime = objs[0]['time']
    for t,trk in enumerate(trks):
      data = list(self.trackers.values())
      # print (data, t, trk)
      pos = data[t].predict()[0]
      trk[:] = [pos[0], pos[1], pos[2], pos[3], 1]
      if(np.any(np.isnan(pos))):
        to_del.append(t)
    trks = np.ma.compress_rows(np.ma.masked_invalid(trks))

    #check t
    for t in reversed(to_del):
      del self.trackers[t]
    matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets,trks)
    #update matched trackers with assigned detections

    for t,trk in enumerate(self.trackers):
      if(t not in unmatched_trks):
        d = matched[np.where(matched[:,1]==t)[0],0]
        self.trackers[trk].update(dets[d,:][0])

    #create and initialise new trackers for unmatched detections
    for i in unmatched_dets:
        track_id = objs[i]['id']
        track_id = uuid.UUID(track_id)
        trk = KalmanBoxTracker(bbox=dets[i,:6],name=objs[i]['name'],track_id = track_id)
        # self.manage_group[trk.id] = [[trk.get_state().ravel(),frame_id,gettime]]
        self.trackers[trk.id] = trk

    #check id in trackers
    i = len(self.trackers)
    for trk in self.trackers:
      d_xyxy= self.trackers[trk].get_state()
      d = convert_xyxy_2_rxywh(d_xyxy[0],width,height)
      id = self.trackers[trk].id
      id = self.trackers[trk].id
      name= self.trackers[trk].name
      #edit code from here

      group = self.__get_member_group(trk)
      if not group:
        self.__new_object(trk, d, height, width)
      else:
        # check member still belong to group with new coordinates
        stay_in_group = self.__surviral_inGroup(group, trk, d[:4], height, width)
        if stay_in_group:
          self.manage_group[group].update_member(trk, d[:4])
          self.__mergeGroup_OR_create_new(trk, d[:4], width, height)
        else:
          self.__delete_member(group, trk)
          self.__new_object(trk, d, height, width)
      #end

      if((self.trackers[trk].time_since_update < 1) and (self.trackers[trk].hit_streak >= self.min_hits or self.frame_count <= self.min_hits)):
        ret.append(np.concatenate((d,[trk])).reshape(1,-1))
      i -= 1
      #remove dead tracklet
      if(self.trackers[trk].time_since_update > self.max_age):
        dead_id.append([trk])

    for dead in dead_id:
      try:
        group = self.__get_member_group(trk)
        self.__delete_member(group,dead[0])
        follow['group'] = self.manage_group
        # this try structure will solve in case object appear and disappear immediately on not track frame skip
        # follow['tracks'] = self.manage_group[dead[0]]
        # del self.manage_group[dead[0]]
        print(1)
      except:
        print("The object just appear in the moment")
        continue
      finally:
        del self.trackers[dead[0]]
    bbox_group = []
    for group in self.manage_group.keys():
      bbox = self.manage_group[group].get_bbox()
      bbox_group.append(bbox)
    if(len(ret)>0):
      return bbox_group,follow
    return bbox_group,follow

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='SORT demo')
    parser.add_argument('--display', dest='display', hetime_since_updatelp='Display online tracker output (slow) [False]',action='store_true')
    args = parser.parse_args()
    return args