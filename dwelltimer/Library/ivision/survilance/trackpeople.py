################################################################
#                                                              #
# count people #                                               #
# created and developped by Infinity Corporation #             #
# Developer : Pritam Samadder & Ria Santra #                   #
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
from pymongo import MongoClient
import tkinter as tk
from tkinter import filedialog




class TrackingPeople:


    def __init__(self,ismongodb=False):

        self.ismongodb=ismongodb

        if ismongodb:

            self.conn=cu.connectDB()
            print("conn = : ",self.conn)
            #input()
            self.db=cu.selectDB(self.conn,"bufo")
            print("db = : ",self.db)
        self.personcount=1

    #videostream = parameters[0] , width = parameters[1] , islivestream = parameters[2] , isnovideo = parameters[3] , starttime= parameters[4]
    #frameskip=parameters[5],flushtime=parameters[6],output=parameters[7],debug=parameters[8]
    def TrackPeoples(self,parameters):
        
        
       # segregate different parameters from list
        videostream = parameters[0]
        width = parameters[1]
        if not parameters[2]:
            islivestream=False
        else:
            livestream = parameters[2]
        if not parameters[3]:
            isnovideo=False
        else:
            isnovideo = parameters[3]
        if not parameters[4]:
            starttime=None
        else:
            starttime = parameters[4]
        if not parameters[5]:
            frameskip=0
        else:
            frameskip = parameters[5]
        if not parameters[6]:
            flushtime=1000
        else:
            flushtime=parameters[6]
        if not parameters[7]:
            output=None
        else:
            output = parameters[7]
        if not parameters[8]:
            debug=False
        else:
            debug=parameters[8]
        
        
        video=videostream
        livestream=islivestream

        if livestream:
            try :
                video = int(video)
                if video < 0:
                    video = 0
            except:
                pass
        
        cleartime=int(flushtime)
        
        if cleartime <= 0 :
            cleartime = 1000
            
        verbose=debug
        novideo=isnovideo
        
        totalframes=0
        fps=0
        videolength=0
        currentframetime=0
        remainingtime=0


        first = True
        cap=None

        centroids=[]
        pick=[]

        database=[]
        finaldatabase=[]
        fulldatabase=[]

        locked=[False]
        updatethreadtimer = 0
        
        
        #updatethread=Thread(target=updateData,args=(database,db,locked),name="update_thread")  # thread for updating the data
        storethread=Thread(target=self.storeData,args=(database,finaldatabase,30,locked),name="store_thread")  # thread for storing the data
        errorstatus=0

        

        
        

        try:


            hog=cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

            cap=cv2.VideoCapture(video)

            if not cap.isOpened():
                cap.open()
            if not cap.isOpened():
                raise(Exception("can not open the video stream"))



            #if first==True:
            #    
            #    r,prevframe=cap.read()
            #    if not r:

            #        print("video finished ")
            #        raise(Exception("Video Finished"))

            #    first=False

            
            while(cap.isOpened()):

                (ret,frame)=cap.read()
                print("read frame status : ",ret)
                framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)

                if not ret:
                    
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                    print ("video finished")
                    cv2.destroyAllWindows()
                    cap.release()

                    raise(Exception("Video Finished"))

                currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)
                remainingtime=videolength-currentframetime

                frame=imutils.resize(frame,width=min(width,frame.shape[1])) #resize the frame
                if first==True:

                    fwidth=frame.shape[1]
                    fheight=frame.shape[0]
                    first=False
                


                (rects,weights)=hog.detectMultiScale(frame,winStride=(4,4),padding=(4,4),scale=1.05)  #detect human in previous
                print("rects : ",rects)
                print("weights : ",weights)
                
                i=0
                if len(rects)>0 and len(weights)>0:

                    weights=weights.tolist()
                    rects=rects.tolist()

                    while(i<len(weights)):
                        
                        if weights[i][0]<float(1):
                            
                            weights.pop(i)
                            rects.pop(i)
                            i-=1
                        i+=1

                    rects=np.array([[x,y,x+w,y+h] for (x,y,w,h) in rects])
                    weights=np.array(weights)


                i=0

                pick=non_max_suppression(rects,probs=None,overlapThresh=0.65)

                if len(pick) > 0 :

                    for (xa,ya,xb,yb) in pick :

                        cen=cu.getCentroid([(xa,ya),(xb,yb)])
                        centroids.append(cen)

                print("pick : ",pick)

                if len(centroids)>0:

                    i=-1

                    for c in centroids:

                        i+=1

                        cx=int(c[0])
                        cy=int(c[1])

                        p0=np.array([[cx,cy]],np.float32)
                        print("len pick : ",len(pick))
                        print("i : ",i)
                        print("pick [i] : ",pick[i])
                        crntbox=[[pick[i][0],pick[i][1]],[pick[i][2],pick[i][3]]]
                        print("crnt box : ",crntbox)

                        insertstatus=self.insertPerson(crntbox,c,database)
                        print("insert status : ",insertstatus)


                centroids=[]
                pick=[]


                if not locked[0]:

                    print(" updatethreadtimer : ",updatethreadtimer)
                    print(" cleartime : ",cleartime)

                    if updatethreadtimer>=cleartime :

                        locked=[True]
                        updatethreadtimer=0

                        storethread=Thread(target=self.storeData,args=(database,finaldatabase,30,locked),name="store_thread")  # thread for storing the data
                        storethread.start()
                        storethread.join()
                        if len(finaldatabase)>0:
                            if(self.ismongodb):
                                self.updateData(self.db,"track",finaldatabase)
                            fulldatabase.extend(finaldatabase)
                            finaldatabase.clear()
                        print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                        #input()

                    else:
                        
                        updatethreadtimer += 1
                        

                    
                    
                

        except Exception as e:

            errorstatus=1
            
            print()
            print("Fatal Error in CountPeople()")
            print()
            print("Error Name : ",e)
            print()
            print("Error in Details :")
            print()

            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)

        finally:

            return (errorstatus,fulldatabase,(fwidth,fheight),video)







    def insertPerson(self,person,cen,database):
        
        newperson = True
        i=-1
        for p in database:
            i+=1
            
            if cu.isNearCentroid(cen,p[0]):
                
                database[i][0]=person
                database[i][1].append([list(cen),datetime.datetime.now().ctime()])
                database[i][2]=[datetime.datetime.now()]
                newperson=False
                return 1

        if newperson:

            pdata=[[],[],[]]
            pdata[0]=person
            pdata[0]=person
            pdata[1]=[]
            pdata[1].append([list(cen),datetime.datetime.now().ctime()])
            pdata[2]=[datetime.datetime.now()]
            
            
            
            database.append(pdata)
            
            return 2


    def updateData(self,mdb,coln,dbo):

        try:

            result=cu.pushintoDB(mdb,coln,dbo)

        except Exception as e:
            print("Fatal Error in dwellTime()")
            print("Error Name : ",e)
            print("Error in Details :")
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)

        
            
    def storeData(self,tdatabase,fdatabase,ct,lockstatus):

        try:

            i=0

            while i<len (tdatabase):

                dt=tdatabase[i][2][0]
                ms=(datetime.datetime.now()-dt).total_seconds()
                if ms >= ct:
                    dt={str(self.personcount):tdatabase[i][1]}
                    
                    fdatabase.append(dt)
                    tdatabase.pop(i)
                    self.personcount+=1
                    i-=1
                i+=1
        except Exception as e:
            print()
            print("Fatal Error in CountPeople()")
            print()
            print("Error Name : ",e)
            print()
            print("Error in Details :")
            print()

            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)

        finally:
            lockstatus[0]=False


if __name__=="__main__":

    print("press 1 to track from video file")
    print("press 2 to track from webcam")
    ans=int(input())
    if ans!=1:
        vidpath=int(input("enter the webcam number you want to process : "))
        param=[vidpath,250,True,False,None,0,1000,None,False]
    else:
        vidpath=filedialog.askopenfilename()
        param = [vidpath, 250, False, False, None, 0, 1000, None, True]
    tp=TrackingPeople()
    print("enter path to the output file : ")
    outfilepath=filedialog.askopenfilename()

    r,data,shape,vid=tp.TrackPeoples(param)
    f = open(outfilepath, "w", encoding="utf-8")


    print(data)
    data=repr(data)
    print(type(data))
    #print(len(data))
    data=eval(data)

    json.dump([shape,vid,data],f)
    #json.dump(data,f)
    f.flush()
    f.close()
