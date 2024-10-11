
import os
import numpy as np
import cv2
import natsort
#import xlwt
#from skimage import exposure

from sceneRadianceCLAHE import RecoverCLAHE
from sceneRadianceHE import RecoverHE

np.seterr(over='ignore')
if __name__ == '__main__':
    pass
folder = "/home/kyapo/Desktop/sauvc_objectdetection"
folder = "C:/Users/June/Desktop/sauvc_objectdetection"

path = folder + "/InputImages_gate"
files = os.listdir(path)
files =  natsort.natsorted(files)

for i in range(len(files)):
    file = files[i]
    filepath = path + "/" + file
    prefix = file.split('.')[0]
    if os.path.isfile(filepath):
        print('********    file   ********',file)
        # img = cv2.imread('InputImages/' + file)
        img = cv2.imread(folder + '/InputImages_gate/' + file)
        sceneRadiance = RecoverHE(img)
        cv2.imwrite('OutputImages_gate/' + prefix + '_HE.jpg', sceneRadiance)
