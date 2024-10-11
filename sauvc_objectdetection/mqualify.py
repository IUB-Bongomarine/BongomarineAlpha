from cmath import rect
from lib2to3.pgen2.pgen import generate_grammar
from queue import Empty
import re
from reprlib import recursive_repr
from turtle import pos
import cv2
import numpy as np
import array as arr
import os
import natsort
from flask import Flask, render_template, request, jsonify, Response
from multiprocessing import Process, Value, Pipe
import threading
import cv2
import serial
import sys
import csv
from datetime import datetime


# Initialize Flask app
#app = Flask(__name__)


#AUTONOMOUS CODE
# Image preprocessing
def RecoverHE(sceneRadiance):
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(4, 4))
    for i in range(3):
        #sceneRadiance[:, :, i] =  cv2.equalizeHist(sceneRadiance[:, :, i])
        sceneRadiance[:, :, i] = clahe.apply((sceneRadiance[:, :, i]))
    return sceneRadiance

def img_preprocessing(img):
    frame = RecoverHE(img)
    
    #scale_percent = 100 # percent of original size
    #width = int(frame.shape[1] * scale_percent / 100)
    #height = int(frame.shape[0] * scale_percent / 100)
    #frame = cv2.resize(frame, (width, height))

    #cv2.imshow('Original',frame)
    #cv2.waitKey(0)

    # Convert color space
    #frame = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)

    # Color filtering
    Min = np.array([  113, 120, 144])
    Max = np.array([ 141, 255, 255])
    mask = cv2.inRange(frame, Min, Max)
    result = cv2.bitwise_and(frame, frame, mask=mask)

    #cv2.imshow('Color filtering', result)
    #cv2.waitKey(0)

    # Thresholding
    #result = cv2.cvtColor(result, cv2.COLOR_HSV2BGR)
    #result = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
    thresh = 0
    maxValue = 255
    processed_frame, thresholding_image = cv2.threshold(result, thresh, maxValue, cv2.THRESH_BINARY)

    thresholding_image = cv2.cvtColor(thresholding_image, cv2.COLOR_BGR2GRAY)
    thresholding_image= cv2.dilate(thresholding_image,(9,9), iterations=10)

    cv2.imshow('Thresholding',thresholding_image )
    cv2.waitKey(0)

    return thresholding_image

def order_points(pts):
    ''' sort rectangle points by clockwise '''
    sort_x = pts[np.argsort(pts[:, 0]), :]
    
    Left = sort_x[:2, :]
    Right = sort_x[2:, :]
    # Left sort
    Left = Left[np.argsort(Left[:,1])[::-1], :]
    # Right sort
    Right = Right[np.argsort(Right[:,1]), :]
    
    return np.concatenate((Left, Right), axis=0)

class Rectangle():
    def __init__(self, contours) -> None:
        self.rect = cv2.minAreaRect(contours)
        self.box = cv2.boxPoints(self.rect)
        self.box = np.int0(self.box)
        #self.box = order_points(box)

        self.left_top_pt = self.box[1]
        self.right_bottom_pt = self.box[3]
        self.line_length = []
        self.max_length = {"length": 0, "coordinate" : [0,0,0,0]}
        
        for point in range(4):
            if point < 3:
                x1 = self.box[point][0]
                y1 = self.box[point][1]
                x2 = self.box[point+1][0]
                y2 = self.box[point+1][1]
                
            else :
                x1 = self.box[point][0]
                y1 = self.box[point][1]
                x2 = self.box[0][0]
                y2 = self.box[0][1]

            length = ((x1 - x2)**2 + (y1 - y2)**2) ** (1/2)
            self.line_length.append(length)
            if length > self.max_length["length"]:
                    self.max_length["length"] = length
                    self.max_length["coordinate"] = [x1, y1, x2, y2]

        

        self.area = max(self.line_length) * min(self.line_length)

        if self.max_length["coordinate"][0] -  self.max_length["coordinate"][2] == 0:
            self.slope = -1 
        else:
            self.slope = abs((self.max_length["coordinate"][1] -  self.max_length["coordinate"][3]) / (self.max_length["coordinate"][0] -  self.max_length["coordinate"][2]) )

        
    def drawing(self,img):
        for point in range(4):
            if point < 3:
                x1 = self.box[point][0]
                y1 = self.box[point][1]
                x2 = self.box[point+1][0]
                y2 = self.box[point+1][1]
            else :
                x1 = self.box[point][0]
                y1 = self.box[point][1]
                x2 = self.box[0][0]
                y2 = self.box[0][1]

            cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)
        return img


def find_rectangle(thres_img, l_r_frame, w,h):

    original = l_r_frame.copy()
    indepent = False

    contours, _hierarchy = cv2.findContours(thres_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #print("number of countours: %d" % len(contours))

    rectangle_list = []
    for cnt in contours:
        rectangle_list += [Rectangle(cnt)]

    # Filtering : the slope of the triangles should more than 11 (almost vertical) , the area should not be too small
    possible_gate = []
    for i in range(len(rectangle_list))  :
        if (rectangle_list[i].slope == -1 or rectangle_list[i].slope > 11) and rectangle_list[i].area > 2000:               #tan(85) = 11  
            possible_gate += [rectangle_list[i]]
    
    # Validation check : possible_gate is empty
    if len(possible_gate) == 0:
        print("Validation check failed : Cannot find any retangle ")
        return None

    # Validation check : Not enough rectangle
    if len(possible_gate) == 1:
        print("Validation check failed : Not enought rectangle")
        #for  rectangle in possible_gate:
        #    original = rectangle.drawing(original) 
        #cv2.imshow('rectangle',original)
        #cv2.waitKey(0)
        indepent = True
        gate_info = (indepent, possible_gate[0].left_top_pt, possible_gate[0].right_bottom_pt, None, None)
        return gate_info

    # Sorting by their area.
    possible_gate.sort(key=lambda a : a.area, reverse = True)

    # Validation check : the difference of area of two largest rectangle are too large
    if possible_gate[0].area / possible_gate[1].area >= 4 :
        print("Validation check failed : the difference of area of two largest rectangle are too large")
        indepent = True
        gate_info = (indepent, possible_gate[0].left_top_pt, possible_gate[0].right_bottom_pt, None, None)
        return gate_info

    # Only consider the largest 4 rectangles
    more_possible_gate = []
    if len(possible_gate) < 4:
        more_possible_gate = possible_gate
    else :
        for i in range(4):
            more_possible_gate += [possible_gate[i]]

    # The lower/larger, the foremost (the possibility that it is underwater is higher)
    #more_possible_gate.sort(key=lambda y : y.left_top_pt[1], reverse=True)    
    more_possible_gate.sort(key=lambda y : y.right_bottom_pt[1], reverse=True)     
    #print("number of possible recantagle for gate: ", len(more_possible_gate))

    # Validation check : Prevent that one rectangle is on the top (shadow) and one rectangle is  underwater
    if abs(more_possible_gate[0].left_top_pt[1] - more_possible_gate[1].left_top_pt[1]) > 150  and abs(more_possible_gate[0].right_bottom_pt[1] - more_possible_gate[1].right_bottom_pt[1]) > 300 :
        #for  rectangle in more_possible_gate:
        #    original = rectangle.drawing(original)  
        #    cv2.imshow('Validation check',original)
        #    cv2.waitKey(0)
        print("Validation check failed : one rectangle is on the top (shadow) and one rectangle is  underwater :", more_possible_gate[0].left_top_pt, more_possible_gate[1].left_top_pt, more_possible_gate[0].right_bottom_pt,more_possible_gate[1].right_bottom_pt)
        indepent = True
        gate_info = (indepent, more_possible_gate[0].left_top_pt, more_possible_gate[0].right_bottom_pt, None, None)
        return gate_info

    
    
    most_possible_gate = []
    for i in range(2):
        print("Rectangle area:", more_possible_gate[i].area)
        most_possible_gate += [more_possible_gate[i]]

    # Sorting them accoring to x coordinate
    most_possible_gate.sort(key=lambda x : x.left_top_pt[0]) 
    
    # Validation check : whether the gate area is too small
    length = (most_possible_gate[1].right_bottom_pt[0] - most_possible_gate[0].left_top_pt[0]) #x
    width = (most_possible_gate[1].right_bottom_pt[1] - most_possible_gate[0].left_top_pt[1]) #y
    gate_area = length * width 
    if gate_area <= 50000:
        print("Validation check failed : The gate area is too small ")
        return None

    gate_mid_pt = (most_possible_gate[0].left_top_pt[0] + int(length / 2), most_possible_gate[0].left_top_pt[1] + int(width / 2))
    gate_info = (indepent, most_possible_gate[0].left_top_pt, most_possible_gate[1].right_bottom_pt, gate_area, gate_mid_pt)
    
    # Drawing the rectangles and point
    middle_w = int(w/2)
    middle_h = int(h/2)
    for  rectangle in most_possible_gate:
        original = rectangle.drawing(original) 
    original = cv2.circle(original, gate_mid_pt, radius=0, color=(255, 0, 255), thickness=6)
    original = cv2.circle(original, (middle_w, middle_h), radius=0, color=(125, 0, 125), thickness=6)
    cv2.imshow('rectangle',original)
    cv2.waitKey(0)

    return gate_info


class Gate():
    def __init__(self, gate_l, gate_r, w, h) -> None:
        self.gate_left = gate_l
        self.gate_right = gate_r

        # w = 1280  h = 720
        self.width = w
        self.hight = h
        self.middle_w = w/2      #640
        self.middle_h = h/2
        '''
        8 : Both are none gate  : cannot see any gate
        7 : Left is none gate, right is a single gate on the right
        6 : Left is a single gate, right is none gate on the left
        5 : Both are single gate, but dont know it is going to turn left or not.
        4 : Both are single gate, but one is on the most left, but one is on the most right
        3 : Left is single gate, right is full gate
        2 : Left is full gate, right is single gate
        1 : Both are full gate
        0 : Bad detection
        '''
        if (gate_l is None and gate_r is None) :
            self.status = 8
        elif (gate_l is None and gate_r[0] == False):
            self.status = 0
        elif (gate_l is None and gate_r[0] == True):
            if gate_r[1][0] > w-self.middle_w/4:
                self.status = 7
            else :
                self.status = 0
        elif (gate_l[0] == False and gate_r is None):
            self.status = 0
        elif (gate_l[0] == True and gate_r is None):
            if gate_l[1][0] < self.middle_w/4:
                self.status = 6
            else :
                self.status = 0
        elif (gate_l[0] == True and gate_r[0] == True):
            if (gate_l[1][0] > gate_r[1][0]) and abs(gate_l[1][1] - gate_r[1][1]) < 50:
                self.status = 5
            elif (gate_l[1][0] < gate_r[1][0]) and ((w - gate_l[1][0]) + gate_r[1][0])  > 2200:
                self.status = 4
            else :
                self.status = 0
        elif (gate_l[0] == True and gate_r[0] == False):
            if gate_l[1][0] > gate_r[1][0] and abs(gate_l[1][1] - gate_r[1][1]) < 50 and abs(gate_r[4][0]-self.middle_w)>30 :
                self.status = 3
            else :
                self.status = 0
        elif (gate_l[0] == False and gate_r[0] == True):
            if gate_l[2][0] > gate_r[2][0] and abs(gate_l[2][1] - gate_r[2][1]) < 50 and abs(gate_l[4][0]-self.middle_w)>30 :
                self.status = 2
            else : 
                self.status = 0
        else :
            self.status = 1
    
        self.behaviour = None
        self.distance = None


    def set_behaviour(self, dir):
        self.behaviour = dir
        if (dir == 'left'):
            self.turn_left()
        elif (dir == 'right'):
            self.turn_right()
        elif (dir == 'front'):
            self.front()
        elif (dir == 'center_front'):
            self.center_front()
        elif (dir == 'stop'):
            self.stop()
    
    def turn_left(self):
        if self.status == 2:
            self.distance = abs(self.middle_w - self.gate_left[4][0])
        elif self.status == 6:
            self.distance = abs(self.width - self.gate_left[1][0] * 2 )     # 總寬 - 左上角坐標 x 2 
        elif self.status == 7:
            self.distance = abs(self.width - self.gate_right[1][0])  # 總寬 - 左上角坐標
        elif self.status == 5:
            self.distance = abs(self.width - self.gate_left[1][0])
        print("turn_left: ", - self.distance)
        return self.distance

    def turn_right(self):
        if self.status == 3:
            self.distance = abs(self.gate_right[4][0] - self.middle_w)
        elif self.status == 6 :
            self.distance = abs(self.gate_left[1][0])
        elif self.status == 7:
            self.distance = abs(self.width - (self.width - self.gate_right[1][0])*2 )     
        elif self.status == 5:
            self.distance = abs(self.gate_left[1][0])
        print("turn_right: ", self.distance)
        return self.distance

    def front(self):
        if self.status == 1:
            self.distance = self.middle_w - self.gate_left[4][0]
            self.distance = -self.distance      # -(+) : left  -(-) : right
        print("front: ", self.distance)
        return self.distance

    def center_front(self):
        self.distance = 0
        print("center_front: ", self.distance)
        return self.distance

    def stop(self):
        print("stop")


def check_global_status(gate_object: Gate,  w : int):
    global gate_count,  gate_dataset, ready_pass, frame, c_gate, detec_err_count

    detection_err = False
    s = gate_object.status
    middle_w = w/2

    if gate_count != 0:
        ps = gate_dataset[-1].status
        print("precious status: ", ps)
        print("status: ", s )
    else:
         ps = -1

    if s != 0 :
        if gate_count == 0:     
            print("The first valid image detected")
            if s == 8:
                gate_object.set_behaviour('center_front')
            else:
                print("You hv seen a gate")
                if s == 2 :
                    gate_object.set_behaviour('left')
                elif s == 3 :
                    gate_object.set_behaviour('right')
                elif s == 5:      # Not sure status , from previous experience, the auv always drifts to the right.
                    gate_object.set_behaviour('left')
                elif s == 1:
                    gate_object.set_behaviour('front')
                if s != 7 or s != 6:
                    c_gate = True
            
        if ready_pass == True:     
            print("You r ready to pass the gate")
            if s == 8 :         
                count = 0
                for i in range(1, 6):   # -1 to -5
                    if gate_dataset[-i].status == 8 :
                        count += 1
                    else :
                        gate_object.set_behaviour('front')         
                        break
                if count == 10:   
                    gate_object.set_behaviour('stop')

            elif ps == s:       # 4 == 4  6 == 6  7 ==7
                gate_object.set_behaviour(gate_dataset[-1].behaviour)
            
            elif s == 6 :
                gate_object.set_behaviour('right')
            elif s == 7 :
                gate_object.set_behaviour('left')
            elif s == 4 :
                gate_object.set_behaviour('center_front') 
            elif s == 5:
                if gate_object.gate_right[1][0] < middle_w/4:
                    gate_object.set_behaviour('right')
                elif gate_object.gate_left[1][0] > (w -  middle_w/4 ):
                    gate_object.set_behaviour('left')

            #else:
            #    detection_err = True


        if ready_pass == False and gate_count != 0 :
            print("Detecting")

            if ps == 8 and c_gate == False and s != 8 :
                if s == 1:
                    gate_object.set_behaviour('front')
                elif s == 2 or s == 5:        
                    gate_object.set_behaviour('left')       
                elif s == 3 :
                    gate_object.set_behaviour('right')
                if s == 6 or s == 7:
                    detection_err = True
                else :
                    print("You hv seen a gate")
                    c_gate = True

            elif ps == 1 and s == 1:
                gate_object.set_behaviour("front")
            elif (ps == 2 and s == 2) :
                gate_object.set_behaviour("left")
            elif (ps == 6 and s == 6):
                gate_object.set_behaviour("left")
            elif (ps == 3 and s == 3) :
                gate_object.set_behaviour("right")
            elif (ps == 7 and s == 7):
                gate_object.set_behaviour("right")
            elif (ps == 5 and s == 5):
                gate_object.set_behaviour(gate_dataset[-1].behaviour)     
            elif (ps == 8 and ps == 8):
                gate_object.set_behaviour('center_front') 

            # 1, 2 ,3
            elif ps == 1 and s == 2:
                gate_object.set_behaviour('left')    
            elif ps == 1 and s == 3:
                gate_object.set_behaviour('right')   
            elif (ps == 2 or ps == 3) and s == 1:
                gate_object.set_behaviour('front')   
            elif ps == 2 and s == 3:
                gate_object.set_behaviour('right')   
            elif ps == 3 and s == 2:
                gate_object.set_behaviour('left')    

            # 5
            elif (ps == 6 or ps == 7 or ps == 5 or ps == 4) and s == 1:
                gate_object.set_behaviour('front')   
                gate_dataset.remove(gate_dataset[-1])
            elif ps == 5 and gate_dataset[-1].behaviour == 'left'and  s == 2:
                gate_object.set_behaviour('left')      
            elif ps == 5 and gate_dataset[-1].behaviour == 'right' and s == 3:
                gate_object.set_behaviour("right")
            elif ps == 5 and gate_dataset[-1].behaviour == 'left'and s == 7:
                gate_object.set_behaviour('right')
            elif ps == 6 and s == 5:
                gate_object.set_behaviour("left")   
            elif ps == 7 and s == 5:
                gate_object.set_behaviour("right")  

            # Ready to pass gate case
            elif (gate_count> 20) and ( ps == 4 and gate_dataset[-2].status == 4 )and s == 4  :
                gate_object.set_behaviour('center_front')
                print ("Ready to pass gate")      
                ready_pass = True

            else :
                if c_gate == True :
                    c_full_gate_count = 0
                    for i in range (3):
                        if gate_dataset[-i].status == 1:
                            c_full_gate_count += 1
                    if c_full_gate_count == 3 and ( s == 8  or s == 4) :
                        gate_object.set_behaviour('center_front')
                        print ("Ready to pass gate")      
                        ready_pass = True

                    elif c_full_gate_count == 3 and s == 6  :
                        gate_object.set_behaviour('right')      
                        print ("Ready to pass gate")
                        ready_pass = True
                    
                    elif c_full_gate_count == 3 and s == 7 :
                        gate_object.set_behaviour('left')       
                        print ("Ready to pass gate")
                        ready_pass = True
                    
                    elif c_full_gate_count == 3 and s == 5:
                        if gate_object.gate_right[1][0] < middle_w/4:
                            gate_object.set_behaviour('right')
                            ready_pass = True
                        elif gate_object.gate_left[1][0] > (w -  middle_w/4 ):
                            gate_object.set_behaviour('left')
                            ready_pass = True

            '''
            # Detection error case
            elif (ps == 2 or ps == 3) and (s == 5 or s == 6 or s == 7):         
                detection_err = True                        
                print("Detection error : (ps == 2 or ps == 3) and (s == 5 or s == 6 or s == 7)")
            elif (ps == 6 or ps == 7) and (s == 2 or s == 3):        
                detection_err = True                        
                print("Detection error : (ps == 6 or ps == 7) and (s == 2 or a == 3)")
            elif (ps == 1 and s == 5) :
                detection_err = True                         
                print("Detection error : (ps == 1 and s == 5)") 
            elif ps == 5 and  gate_dataset[-1].behaviour == 'left' and s == 6:
                #gate_object.set_behaviour('left')          
                print("Detection error : ps == 5 and  gate_dataset[-1].behaviour == 'left' and s == 6")
                detection_err = True
            elif ps == 5  and s == 4:   
                detection_err = True    
                print("You have Detection error : ps == 5  and s == 4 ")                    
            elif ps == 4 and (s == 5 or s == 3 or s == 2) :
                detection_err = True
                print("You have Detection error : ps == 4 and (s == 5 or s == 3 or s == 2) ")
            '''

        #if detection_err:
        #    detec_err_count += 1            # Accumulate number of detection error 

        if detection_err == False and gate_object.behaviour is not None:
            detec_err_count = 0
            gate_dataset += [gate_object]
            gate_count += 1

    
    print("behaviour: ", gate_object.behaviour)
    print("distance:", gate_object.distance)
    print()

    # Create an empty placeholder for displaying the values
    placeholder = np.zeros((frame.shape[0],500,3),dtype=np.uint8)
    print(frame.shape[0])
    # fill the placeholder with the values of color spaces
    cv2.putText(placeholder, "previous status:  {}".format(ps), (20, 70), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(placeholder, "status: {} ".format(gate_object.status), (20, 140), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(placeholder, "behaviour:  {}".format(gate_object.behaviour), (20, 210), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(placeholder, "distance:  {}".format(gate_object.distance), (20, 280), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 3, cv2.LINE_AA)
    cv2.putText(placeholder, "detection error:  {}".format(detection_err), (20, 350), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(placeholder, "ready to pass gate:  {}".format(ready_pass), (20, 420), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    cv2.putText(placeholder, "Have seen gate:  {}".format(c_gate), (20, 490), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
    combinedResult = np.hstack([frame,placeholder])
    combinedResult = np.hstack([frame,placeholder])
    cv2.imshow('frame',combinedResult)
    cv2.waitKey(0)


#MANUAL CODE
def serial_process(arduino_port, parent_conn):
    try:
        ser = serial.Serial(arduino_port, 115200, timeout=1)
        print(f"Connected to serial port {arduino_port}")
    except Exception as e:
        print(f"Error establishing serial connection: {e}")
        return

    filename = f'test_data_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Timestamp', 'Data'])

        if parent_conn.poll():  # Check if there's a message from the main process
            direction = parent_conn.recv()
            #if direction in ['l', 'f', 'r', 'u', 'b', 'd', 's', 'p', 'o']:
            #    ser.write(direction.encode())
            if direction:
                #print("behaviour: ", gate_object.behaviour)
                #print("distance:", gate_object.distance)
                sw = gate_object.behaviour + "," + gate_object.distance + "\n"
                ser.write(sw)
                
        data = ser.readline().decode().strip()
        print(data)
        if data:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, data])
            csvfile.flush()

def video_process(recording_flag, child_conn):
    #camera = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    #camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set the width to 1280 pixels
    #camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # Set the height to 720 pixels
    camera = cv2.VideoCapture(0)
    camera.set(3, 1280)
    camera.set(3, 720)
    #camera.set(cv2.CAP_PROP_FPS, 30)  # Set the frame rate to 30 fps

    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    video_out = None

    def capture_frames():
        nonlocal video_out
        while True:
            ret, frame = camera.read()
            if not ret:
                continue

            if recording_flag.value and frame is not None:
                if video_out is None:
                    video_out = cv2.VideoWriter(f'test_video_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.mp4', fourcc, 12, (int(camera.get(3)), int(camera.get(4))))
                video_out.write(frame)

    threading.Thread(target=capture_frames, daemon=True).start()

    @app.route('/video_feed')
    def video_feed():
        def generate():
            while True:
                ret, frame = camera.read()
                if not ret:
                    continue
                ret, buffer = cv2.imencode('.jpg', frame)
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

    @app.route('/control', methods=['POST'])
    def control():
        nonlocal video_out, camera
        direction = request.form.get('direction')

        child_conn.send(direction)  # Send direction to the serial process

        if direction == 'start':
            recording_flag.value = 1
            return jsonify({'status': 'Recording started'})
        elif direction == 'stop':
            recording_flag.value = 0
            if video_out:
                video_out.release()
                video_out = None
                #camera.release()  # Releasing camera here for clean-up, consider managing resource more appropriately based on actual use case
            return jsonify({'status': 'Recording stopped'})

        return jsonify({'status': 'Command not recognized'})

    @app.route('/')
    def index():
        return render_template('gamepad.html')

    app.run(debug=False, host='0.0.0.0', port=5000)
    


#path = "/home/fabmarine/sauvc_objectdetection/q_gate1/"
#path = '.\\q_gate3\\'
#path = '.\\q_gate1\\q_gate1\\'
#files = os.listdir(path)
#files =  natsort.natsorted(files)

height = 720
middle = 1280
width = 2560

gate_count = 0
ready_pass = False
c_gate = False
detec_err_count = False
gate_dataset = []

cv2.namedWindow("frame", cv2.WINDOW_NORMAL )
cv2.resizeWindow("frame", 1280, 360)

cv2.namedWindow('rectangle', cv2.WINDOW_NORMAL )
cv2.resizeWindow('rectangle', 640, 180)

cv2.namedWindow('Thresholding',cv2.WINDOW_NORMAL )
cv2.resizeWindow("Thresholding", 1280, 360)

# Camera stream handling
cap = cv2.VideoCapture(0)  # Use the correct camera index

if not cap.isOpened():
    raise IOError("Cannot open webcam")

while True:
    #AUTONOMOUS
    #file = files[i]
    #frame = cv2.imread(path+file)
    #cv2.imshow('frame', frame)
    #n cv2.waitKey(0)
    #print("Now processing :", file)
    ret, frame1 = cap.read()
    frame1 = cv2.resize(frame1, (1280, 720)) 
    #cap.set(3,1280)
    #cap.set(4,720)
    print(frame1.shape[0],frame1.shape[1])
    frame2 = frame1.copy()

    # Merge the two frames side by side (horizontally)
    frame = np.hstack((frame1, frame2))
    
    if not ret:
        continue

    thresholding_image = img_preprocessing(frame)

    left_frame = frame[0:height, 0: middle]
    thresholding_left = thresholding_image[0:height, 0: middle]
    right_frame = frame[0:height, middle:width]
    thresholding_right = thresholding_image[0:height, middle:width]


    #gate = find_rectangle(thresholding_image, frame)
    gate_left = find_rectangle(thresholding_left, left_frame, middle, height)
    gate_right = find_rectangle(thresholding_right, right_frame, middle, height)


    #if gate_left is not None:
    #    left_frame = cv2.rectangle(left_frame, gate_left[1], gate_left[2], (255, 0,0), 2)
    #    cv2.imshow('gate_left', left_frame)
    #    cv2.waitKey(0)

    #if gate_right is not None:
    #    right_frame = cv2.rectangle(right_frame, gate_right[1], gate_right[2], (255, 0,0), 2)
    #    cv2.imshow('gate_right', right_frame)
    #    cv2.waitKey(0)

    
    print("gate_info_left :", gate_left)
    print("gate_infor_right :", gate_right)
    gate = Gate(gate_left, gate_right, middle, height)
    
    check_global_status(gate, middle)
    
    #MANUAL
        # Determine the correct serial port
    arduino_port = '' 
    # Set the Arduino serial port based on the operating system
    if sys.platform.startswith('win'):
        arduino_port = 'COM18'  # Replace with the appropriate port on Windows
    elif sys.platform.startswith('linux'):
        arduino_port = '/dev/ttyUSB0'  # Replace with the appropriate port on Linux
    elif sys.platform.startswith('darwin'):
        arduino_port = '/dev/cu.usbmodem14201'  # Replace with the appropriate port on macOS

    # Set up shared memory and pipe for inter-process communication
    recording_flag = Value('i', 0)  # Shared memory integer
    parent_conn, child_conn = Pipe()  # Communication pipe between processes

    # Create and start the processes
    serial_proc = Process(target=serial_process, args=(arduino_port, parent_conn))
    #video_proc = Process(target=video_process, args=(recording_flag, child_conn))

    serial_proc.start()
    serial_proc.join()
    
    #video_proc.start()
    #video_proc.join()
    
cap.release()
cv2.destroyAllWindows()
    


