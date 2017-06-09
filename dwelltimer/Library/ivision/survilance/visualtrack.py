################################################################
#                                                              #
# count people #                                               #
# created and developped by Infinity Corporation #             #
# Developer : Pritam Samadder #                                #
#                                                              #
#                                                              #
#                                                              #
################################################################




from __future__ import print_function
import cv2
import imutils
from imutils import paths
from imutils import *
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import cvutil as cu
from collections import deque
import argparse
import json
import threading
from threading import Thread
import datetime
import time
import sys
import tkinter as tk
from tkinter import filedialog





def visualiseTracks(vfile):

    colors=[(255,0,0),(0,255,0),(0,0,255),(127,125,6),(225,6,8),(37,45,78),(127,127,127),(54,12,30)]

    try:

        f=open(vfile,"r",encoding="utf-8")

        d=json.load(f)

        shape=d[0]
        fwidth=shape[0]
        fheight=shape[1]
        stream=d[1]
        data=d[2]

        people=len(data)
        print("number of people : ",people)
        #print(data)

        cap=cv2.VideoCapture(stream)
        if not cap.isOpened():
            cap.open()

        ret,frame=cap.read()
        if not ret:

            print ("video finished")
            cv2.destroyAllWindows()
            cap.release()

            raise(Exception("Video Finished"))

        

        #frame=imutils.resize(frame,width=min(250,frame.shape[1])) #resize the frame
        #print(frame.shape)

        xratio=frame.shape[1]/fwidth
        yratio=frame.shape[0]/fheight

        i=0
        k=0
        l = 1
        for person in data:

            #print("type person : ",type(person))

            k=0

            print("plotting person {0}  data ".format(l))
            print("total track point for person {0} is {1} ".format(l,len(person[str(l)])))
            while(k<(len(person[str(l)])-1)):

                p0=(int(person[str(l)][k][0][0]*xratio),int(person[str(l)][k][0][1]*yratio))
                #print(p0)
                p1=(int(person[str(l)][k+1][0][0]*xratio),int(person[str(l)][k+1][0][1]*yratio))
                #print(p1)
                cv2.arrowedLine(frame,p0,p1,colors[i],2)
                k+=1

            '''for point in person:

                p=(point[0],point[1])
                r=colors[i][0]
                g=colors[i][1]
                b=colors[i][2]
                cv2.circle(frame, p, 3, colors[i], -1)'''
            i+=1
            l+=1
            if i>=len(colors):
                i=0

        cv2.imshow("track points",frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
            
    
    except Exception as e:

        print()
        print("Fatal Error in visualiseTracks()")
        print()
        print("Error Name : ",e)
        print()
        print("Error in Details :")
        print()

        err=sys.exc_info()
        print("Error Type : ",err[0])
        print("file name : ",err[-1].tb_frame.f_code.co_filename)
        print("Line Number : ",err[-1].tb_lineno)






if __name__=="__main__":
    jsonpath=vidpath=filedialog.askopenfilename()
    visualiseTracks(jsonpath)


        
