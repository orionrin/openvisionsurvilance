################################################################
#                                                              #
# peoplecountconfig.py #                                       #
# created and developped by Infinity Corporation #             #
# Developer : Ria Santra #                                     #
#                                                              #
#                                                              #
#                                                              #
################################################################




from __future__ import print_function
import os
import cv2
import imutils
from imutils import paths
from imutils import *
from imutils.object_detection import non_max_suppression
import numpy as np
import cvutil as cu
import argparse
import json
from tkinter import filedialog


verbose = False

###################################################################################################################################

#Mouse events for getting two points
point1=()
point2=()
clicked=False
pcconfigpoints=[]

def onClikDrag(event,x,y,flags,param):
    global clicked
    global pcconfigpoints
    global point1
    global point2
    global verbose
    if event==cv2.EVENT_LBUTTONDOWN:
        pcconfigpoints=[(x,y)]
        point1=(x,y)
        point2=(x,y)
        clicked=True
        print("Clicked...",pcconfigpoints)

    elif event == cv2.EVENT_MOUSEMOVE:
        if clicked==True:
            point2=(x,y)
        
    elif event==cv2.EVENT_LBUTTONUP:
        pcconfigpoints.append((x,y))
        point2=(x,y)
        clicked=False
        #print(points)
        print("Released...",pcconfigpoints)
            


class inputs:
    width = 400
    livestream = False
    verbose = False

def PeopleCounterConfig(video_filename,confpath,livestream=False,width=250,debug=True):

    global verbose
    global point1
    global point2
    global pcconfigpoints

    verbose=debug

    configuration={}

    cap=None

    # video_filename = inputs.video_filename
    # activity_id = inputs.activity_id
    # camera_id = inputs.camera_id
    # livestream = inputs.livestream
    # debug = inputs.verbose
    # width = inputs.width


    
    try:
        #base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', '..'))
        video = video_filename #filedialog.askopenfilename() #(os.path.join(base_path,'runtime',camera_id, activity_id,video_filename))

        if not width >= 250 and width <= 640:
            width = 250
    
        if livestream:
            
            video=int(video)
        
        if debug:
            verbose=True
        
        #confpath = filedialog.asksaveasfilename() #(os.path.join(base_path,'runtime',camera_id,activity_id,"config.json"))

        cap=cv2.VideoCapture(video)
        
        if not cap.isOpened():
            cap.open()
            
        (ret,frame)=cap.read()
        if not ret:
            print("video finished ")
            return
        
        frame=imutils.resize(frame,width=min(width,frame.shape[1]))
        origframe=frame.copy()
        cv2.imshow("video",frame)
        cv2.setMouseCallback("video",onClikDrag)

        while True:

            cv2.imshow("video",frame)
            s=cv2.waitKey(1) & 0xFF
            if s== ord('s') and point1!=point2 and point1!=0 and point2 !=0:
                break

            elif s== ord ('q'):
                if cap:
                    if cap.isOpened():
                        cap.release()
                cv2.destroyAllWindows()
                return
            
            elif s==ord('n'):
                ret,frame=cap.read()
                if not ret:
                    print("video finished ")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
                
                frame=imutils.resize(frame,width=min(width,frame.shape[1]))
                origframe=frame.copy()
                
            if point1!=point2 and point1!=0 and point2 !=0:
                frame=origframe.copy()
                cv2.line(frame,point1,point2,(0,0,255),2)

        frame=origframe.copy()
        
        if point1!=point2 and point1!=0 and point2 !=0:
            
            boxstatus,box,line1,line2 = cu.getBoxPointandStatus(pcconfigpoints)
            
            cv2.line(frame,(line1[0][0],line1[0][1]),(line1[1][0],line1[1][1]),(0,0,255),2)
            cv2.line(frame,(line2[0][0],line2[0][1]),(line2[1][0],line2[1][1]),(0,255,0),2)
        
        point1=point2=0
        pcconfigpoints=[]
        origframe2=frame.copy()
        
        cv2.imshow("video",frame)

        while (True):


            cv2.imshow("video",frame)

            s=cv2.waitKey(1) & 0xFF
            
            if s== ord('s') and point1!=point2 and point1!=0 and point2 !=0:
                break

            elif s== ord ('q'):
                if cap:
                    if cap.isOpened():
                        cap.release()
                cv2.destroyAllWindows()
                return
            if point1!=point2 and point1!=0 and point2 !=0:

                frame = origframe2.copy()
                cv2.arrowedLine(frame,point1,point2,(255,0,0),3)
                



        if point1!=point2 and point1!=0 and point2 !=0:

            wayline=[pcconfigpoints[0],pcconfigpoints[1]]
            linestatus = cu.getLineStatus(wayline)
            
            wayin,inline,wayinline,wayout,outline,wayoutline = cu.getWayStatus(wayline,box,boxstatus,linestatus)
            


        configuration["width"]=width
        configuration["linestatus"]=linestatus
        configuration["boxstatus"]=boxstatus
        configuration["box"]=box
        configuration["line1"]=line1
        configuration["line2"]=line2
        configuration["wayin"]=wayin
        configuration["inline"]=inline
        configuration["wayinline"]=wayinline
        configuration["wayout"]=wayout
        configuration["outline"]=outline
        configuration["wayoutline"]=wayoutline

        f=open(confpath,"w")
        json.dump(configuration,f)
        f.flush()
        f.close()


        if verbose:
            print("=================================================================")
            print("video width : ",width)
            print("boxstatus : ",boxstatus)
            print("box : ",box)
            print("line1 : ",line1)
            print("line2 : ",line2)
            print("way of moving : ",linestatus)
            print("way in : ",wayin)
            print("in line : ",inline)
            print("wayinline : ",wayinline)
            print("wayout : ",wayout)
            print("out line : ",outline)
            print("wayoutline : ",wayoutline)
            print("=================================================================")
        print("cleanning up..")
        cv2.destroyWindow("video")

            
    except Exception as e:
        
        print("Fatal ERROR  ")
        print(e)
        # activity_id = False
        video_filename = False

    finally:
        print("cleanning up..")
        if cap != None:
            if cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
        return (video_filename)
#
# #call PeopleCounterConfig_CommandInput() function if you are passing the parameter as command line arguments
# def PeopleCounterConfig_CommandInput():
#
#
#     parser = argparse.ArgumentParser()
#     parser.add_argument("videostream",help="The video input stream")
#     parser.add_argument("-l", "--livestream", action="store_true",help="use this option if you are reading livestream from a camera")
#     parser.add_argument("-w","--width",default=250, help="set the width of the video")
#     parser.add_argument("-c","--configuration", help="path to configuration file")
#     parser.add_argument("-v", "--verbose", action="store_true",help="use this switch for verbose mode")
#
#     try:
#
#
#
#         args=parser.parse_args()
#
#         livestream=False
#         video = args.videostream
#         if args.livestream:
#
#             video = int(args.videostream)
#
#             livestream=True
#
#             if not video>=0:
#                 video = 0
#
#
#         width = int(args.width)
#         if not width >= 250 and width<=640:
#             width = 250
#
#         confpath = args.configuration
#
#         if args.verbose:
#             debug=True
#             print("Verbose mode Activated..")
#         else:
#             debug=False
#
#         inputs.video_filename = args.videostream
#         inputs.activity_id = "100"
#         activity_id, video_filename = PeopleCounterConfig()
#         print(activity_id)
#
#     except Exception as e:
#
#         print("Fatal ERROR  ")
#         print(e)
#

def PeopleCounterConfig_CommandInput():
    parser = argparse.ArgumentParser()
    parser.add_argument("videostream", help="The video input stream")
    parser.add_argument("-l", "--livestream", action="store_true",help="use this option if you are reading livestream from a camera")
    parser.add_argument("-w", "--width", default=250, help="set the width of the video")
    parser.add_argument("-c", "--configuration", help="path to configuration file")
    parser.add_argument("-v", "--verbose", action="store_true", help="use this switch for verbose mode")

    try:

        args = parser.parse_args()

        livestream = False
        video = args.videostream
        if args.livestream:

            video = int(args.videostream)

            livestream = True

            if not video >= 0:
                video = 0

        width = int(args.width)
        if not width >= 250 and width <= 640:
            width = 250

        confpath = args.configuration

        if args.verbose:
            debug = True
            print("Verbose mode Activated..")
        else:
            debug = False

        # inputs.video_filename = args.videostream
        # inputs.activity_id = "100"
        # activity_id, video_filename = PeopleCounterConfig()
        # print(activity_id)

        PeopleCounterConfig(video_filename=video, confpath=confpath, livestream=livestream, width=width, debug=debug)

    except Exception as e:

        print("Fatal ERROR  ")
        print(e)


def PeopleCounterConfig_GUIInput():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--livestream", action="store_true",default=False,help="use this option if you are reading livestream from a camera")
    parser.add_argument("-w", "--width", default=250, help="set the width of the video")
    parser.add_argument("-v", "--verbose", action="store_true",default=True, help="use this switch for verbose mode")

    try:

        args = parser.parse_args()

        livestream = False

        if args.livestream:

            video = int(input("enter the camera id : "))

            livestream = True

            if not video >= 0:
                video = 0

        else:
            video = filedialog.askopenfilename()

        width = int(args.width)
        if not width >= 250 and width <= 640:
            width = 250

        confpath = filedialog.asksaveasfilename()

        if args.verbose:
            debug = True
            print("Verbose mode Activated..")
        else:
            debug = False

        # inputs.video_filename = args.videostream
        # inputs.activity_id = "100"
        # activity_id, video_filename = PeopleCounterConfig()
        # print(activity_id)

        PeopleCounterConfig(video_filename=video,confpath=confpath,livestream=livestream,width=width,debug=debug)

    except Exception as e:

        print("Fatal ERROR  ")
        print(e)



if __name__=="__main__":

    #PeopleCounterConfig_CommandInput()
    PeopleCounterConfig_GUIInput()
    
                    
                    
                
