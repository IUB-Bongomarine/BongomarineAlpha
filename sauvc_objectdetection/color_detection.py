# The color space used is LAB
# This program is used to find the more accurate value for color filtering

# Btw, after run the program, place your corsor on the place where the color you want to keep and get the color valuee
# Then press 'esc' code and type the values in the terminal 
# For LAB color space: [Light, A, B]

import cv2
from cv2 import resize
import numpy as np

show = False

def RecoverHE(sceneRadiance):
    clahe = cv2.createCLAHE(clipLimit=2, tileGridSize=(4, 4))
    for i in range(3):
        #sceneRadiance[:, :, i] =  cv2.equalizeHist(sceneRadiance[:, :, i])
        sceneRadiance[:, :, i] = clahe.apply((sceneRadiance[:, :, i]))
    return sceneRadiance

def onTrackbarActivity(x):
    global show
    show = True
    pass

# mouse callback function
def showPixelValue(event,x,y,flags,param):
    global frame, bgr, combinedResult, placeholder
    
    if event == cv2.EVENT_MOUSEMOVE:
        # get the value of pixel from the location of mouse in (x,y)
         bgr = frame[y, x]

         # Convert the BGR pixel into other colro formats
         ycb = cv2.cvtColor(np.uint8([[bgr]]),cv2.COLOR_BGR2YCrCb)[0][0]
         lab = cv2.cvtColor(np.uint8([[bgr]]),cv2.COLOR_BGR2Lab)[0][0]
         hsv = cv2.cvtColor(np.uint8([[bgr]]),cv2.COLOR_BGR2HSV)[0][0]

         print(hsv)
        
         # Create an empty placeholder for displaying the values
         placeholder = np.zeros((frame.shape[0],400,3),dtype=np.uint8)

         # fill the placeholder with the values of color spaces
         cv2.putText(placeholder, "BGR {}".format(bgr), (20, 70), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
         cv2.putText(placeholder, "HSV {}".format(hsv), (20, 140), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
         cv2.putText(placeholder, "YCrCb {}".format(ycb), (20, 210), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
         cv2.putText(placeholder, "LAB {}".format(lab), (20, 280), cv2.FONT_HERSHEY_COMPLEX, .9, (255,255,255), 1, cv2.LINE_AA)
        
         # Combine the two results to show side by side in a single image
         combinedResult = np.hstack([frame,placeholder])
        
         cv2.imshow('Color detection',combinedResult)



if __name__ == '__main__' :
    
    cap = cv2.VideoCapture(0)

    # Color detection
    while(1):
         processed_frame, frame = cap.read()
         frame = cv2.resize(frame, (1280, 720)) 
         frame = RecoverHE(frame)
         #path = '.\\OutputImages_gate\\513_HE.jpg'
         #frame = cv2.imread(path)
         scale_percent = 50 # percent of original size
         width = int(frame.shape[1] * scale_percent / 100)
         height = int(frame.shape[0] * scale_percent / 100)
         frame = cv2.resize(frame, (width, height))
         cv2.imshow('Color detection',frame)
         cv2.namedWindow('Color detection')
         cv2.setMouseCallback('Color detection',showPixelValue)
         
         key = cv2.waitKey(0)
         if key == 27 : #press 'esc' key to leave
            break
    
    cv2.destroyWindow('Color detection')

    # Color filtering
    thresh = int(40)
    
    #input the initial value of the LAB
    light = int(input('Input the light you want:'))
    A = int(input('Input the A value you want:'))
    B = int(input('Input the B value you want:'))

    cv2.namedWindow('SelectLAB',cv2.WINDOW_AUTOSIZE)

    #creating trackbars to get values for LAB
    cv2.createTrackbar('LABLMin','SelectLAB',light-thresh,255,onTrackbarActivity)
    cv2.createTrackbar('LABLMax','SelectLAB',light+thresh,255,onTrackbarActivity)
    cv2.createTrackbar('LABAMin','SelectLAB',A-thresh,255,onTrackbarActivity)
    cv2.createTrackbar('LABAMax','SelectLAB',A+thresh,255,onTrackbarActivity)
    cv2.createTrackbar('LABBMin','SelectLAB',B-thresh,255,onTrackbarActivity)
    cv2.createTrackbar('LABBMax','SelectLAB',B+thresh,255,onTrackbarActivity)

    # show image initially
    cv2.imshow('SelectLAB',frame)
    
    while (1) :
        
        if show: # If there is any event on the trackbar
            show = False

            # Get values from the LAB trackbar
            LMin = cv2.getTrackbarPos('LABLMin','SelectLAB')
            AMin = cv2.getTrackbarPos('LABAMin','SelectLAB')
            BMin = cv2.getTrackbarPos('LABBMin','SelectLAB')
            LMax = cv2.getTrackbarPos('LABLMax','SelectLAB')
            AMax = cv2.getTrackbarPos('LABAMax','SelectLAB')
            BMax = cv2.getTrackbarPos('LABBMax','SelectLAB')
            minLAB = np.array([LMin, AMin, BMin])
            maxLAB = np.array([LMax, AMax, BMax])

            print(minLAB)     #plz check the terminal
            print(maxLAB)

            img = cv2.cvtColor(frame,cv2.COLOR_BGR2LAB)

            # Create the mask using the min and max values obtained from trackbar and apply bitwise and operation to get the results         
            maskLAB = cv2.inRange(img,minLAB,maxLAB)
            resultLAB = cv2.bitwise_and(img, img, mask = maskLAB)
            
            # Show the results
            cv2.imshow('SelectLAB',resultLAB)
        
        key = cv2.waitKey(1)
        if key == 27:
            break


    cv2.destroyWindow('SelectLAB')
    cv2.imwrite('color_filter_rgb2.jpg', resultLAB)

