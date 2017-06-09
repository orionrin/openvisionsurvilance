################################################################
#                                                              #
# count people #                                               #
# created and developped by Infinity Corporation #             #
# Developer : Pritam Samadder And Ria Santra #                 #
#                                                              #
#                                                              #
#                                                              #
################################################################




from __future__ import print_function
import os
import cv2
import imutils
from imutils.object_detection import non_max_suppression
import numpy as np
import cvutil as cu
import json
from multiprocessing import Pool
from threading import Thread
import datetime
import sys
import csv
from pymongo import MongoClient
from tkinter import filedialog
import argparse


class inputs:
    islivestream = False
    frameskip = 2
    novideo = False
    verbose = True
    flushtime = 1000
    starttime=0
    incount = 0
    outcount = 0

class PeopleCount:

    def __init__(self,ismongodb=False):

        self.ismongodb=ismongodb

        if ismongodb:

            self.conn=cu.connectDB()
            print("conn = : ",self.conn)
            #input()
            self.db=cu.selectDB(self.conn,"bufo")
            print("db = : ",self.db)
        else:
            self.db=None

    def CountPeople(self,parameters):

        
        # function takes in single parameter in form of list, which binds multiple parameters
        # [parameter] takes the form of [videostream,[{configuration}],bool livestream, int frameskip, int flushtime, int starttime, bool novideo, bool debug]
        # videostream shall be am IP stream (if livestream) or videofile (if NOT livestream)
        videostream = parameters[0]
        # configuration parameter shall be a list which contains configuration dict
        # configuration dict can be extracted from main config file
        configuration = parameters[1]
        print("CONFIGURATION AT PARAM :", configuration)
        if not parameters[2]:
            livestream = False
        else:
            #livestream = parameters[2]
            livestream = False
        if not livestream:
            frameskip = parameters[3]
            starttime = parameters[5]
        else:
            frameskip = 0
            starttime = datetime.datetime.now()
        print("livestream : ",livestream)
        
        isnovideo = parameters[6]
        debug = parameters[7]
        flushtime = parameters[4]
        width = 250

        countdata={}
        countdata["in"]=0
        countdata["out"]=0
        countdata["intime"]=[]
        countdata["outtime"]=[]
        eventlist=[]

        incount = inputs.incount
        outcount = inputs.outcount
        print("IN count: " + str(incount))
        print("OUT count: " + str(outcount))
        print("Processing video file :" + videostream)
        print("ls : ",livestream)
        if not livestream:
            #base_path = os.path.abspath(os.path.join(os.path.dirname(__file__),'..', '..'))
            #video= os.path.join(base_path,"runtime", inputs.camera_id, inputs.activity_id,'temp', videostream)
            video=videostream
        cleartime=int(flushtime)

        cleartime=100
        updatetime=1000
        updatethreadtimer=0
        
        if cleartime <= 0 :
            cleartime = 1000
            
        verbose=debug
        novideo=isnovideo
        prevcentroids=[]
        centroids=[]
        currentflow=[]
        lk_params = dict( winSize  = (15,15),maxLevel = 2,criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        
        first=True
        cap=None
        
        indatabase=[]
        outdatabase=[]
        
        inclearthread=Thread(target=self.garbageClear,args=(indatabase,30),name="in_clear_thread")  # in database clear thread
        outclearthread=Thread(target=self.garbageClear,args=(outdatabase,30),name="out_clear_thread") # out database clear thread

        inclearthreadtimer = 0    #use this variable as a timer to start the thread for clearing the in database
        outclearthreadtimer = 0   #use this variable as a timer to start the thread for clearing the out database
        
        incount = 0
        outcount = 0
        font = cv2.FONT_HERSHEY_SIMPLEX

        framenumber=0
        if verbose:
            print()
            print("====================================================================================")
            print()
            if livestream:
                print("videostream :", videostream)
            else:
                print("video : ",video)
            # print("configuration file : ",configfile)
            print("live stream : ",livestream)
            print("no video : ",novideo)
            # print("video start time : ",starttime)
            print("skip frames : ",frameskip)
            print("flush time : ",flushtime)
            # print("output : ",output)
            print("verbose : ",verbose)
            print()
            print("====================================================================================")
            print()


        try:

            # Read configuration from parameter configuration
##            configuration = json.dumps(configuration)

            print("conf len ",len(configuration))
            print(configuration)
            conf=configuration

            width=conf["width"]
            print("WIDTH :", width)
            linestatus=conf["linestatus"]
            boxstatus=conf["boxstatus"]
            box=conf["box"]
            line1=conf["line1"]
            line2=conf["line2"]
            wayin=conf["wayin"]
            inline=conf["inline"]
            wayinline=conf["wayinline"]
            wayout=conf["wayout"]
            outline=conf["outline"]
            wayoutline=conf["wayoutline"]
            
            if verbose:
                print()
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                print("boxstatus : ",boxstatus)
                print("box : ",box)
                print("line1 : ",line1)
                print("line2 : ",line2)
                print("wayin : ",wayin)
                print("inline : ",inline)
                print("wayinline : ",wayinline)
                print("wayout : ",wayout)
                print("outline : ",outline)
                print("wayoutline : ",wayoutline)
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                print()

            # set up hog
            hog=cv2.HOGDescriptor()
            hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

            if not livestream:
                cap=cv2.VideoCapture(video)
                fps=cap.get(cv2.CAP_PROP_FPS)
                if first==True:
                    r,prevframe=cap.read()
                    if not r:
                        print("video finished ")
                        raise(Exception("Video Finished"))
                        print("executed 1")
                    first=False

##                    currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)
##                    remainingtime=videolength-currentframetime
##                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)

                totalframes=cap.get(cv2.CAP_PROP_FRAME_COUNT)
                print(totalframes)
                videolength=(totalframes/fps)*1000  # in seconds
                fps=cap.get(cv2.CAP_PROP_FPS)
                currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)
                remainingtime=videolength-currentframetime
                framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)


            elif livestream:

                if("http" in videostream):
                    # read the stream from IP camera
                    import urllib.request
                    ip_stream = urllib.request.urlopen(videostream)        # videostream corresponds to http URI
                    print(ip_stream.headers['Content-Length'])
                    if ip_stream.status != 200:
                        raise(Exception("Unable to fetch video from the IP"))
                    totalframes=0
                    videolength=0
                    global bytes
                    bytes = bytes()

                else:

                    cap = cv2.VideoCapture(int(videostream))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    if first == True:
                        r, prevframe = cap.read()
                        if not r:
                            print("video finished ")
                            raise (Exception("Video Finished"))
                            print("executed 1")
                        first = False


            print("first ", first)
            if first==False or livestream:


                while True:

                    ret = True
                    if livestream and "http" in videostream:
                        # read individual frame from ip_stream
                        bytes += ip_stream.read(65536)

                        a = bytes.find(b'\xff\xd8')
                        b = bytes.find(b'\xff\xd9')
                        print(b)
                        if a != -1 and b != -1:
                            jpg = bytes[a:b+2]
                            bytes = bytes[b+2:]
                            frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if first:
                                prevframe = frame.copy()
                                first = False
                        else:
                            raise(Exception("Cannot load stream from IP"))
                    else:
                        # if NOT livestream
                        print("not live")
                        (ret,frame)=cap.read()
                        framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                        currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)
                        remainingtime=videolength-currentframetime
                    
                    if not ret:
                        framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                        print ("video finished")
                        cv2.destroyAllWindows()
                        cap.release()
                        raise(Exception("Video Finished"))

                    orig=frame.copy()   # make a copy of the current frame
                    frame=imutils.resize(frame,width=min(width,frame.shape[1])) #resize the frame
                    gframe=cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  #convert the color frame to grayscale
                    #(rects,weights)=hog.detectMultiScale(frame,winStride=(4,4),padding=(4,4),scale=1.05)  #detect human in current frame

                    prevframe=imutils.resize(prevframe,width=min(width,prevframe.shape[1]))  #resize previous frame
                    gprevframe=cv2.cvtColor(prevframe, cv2.COLOR_BGR2GRAY)  # grayscale previous frame

                    (prevrects,prevweights)=hog.detectMultiScale(prevframe,winStride=(4,4),padding=(4,4),scale=1.05)  #detect human in previous frame

                    if verbose:
                        print("===================================")
                        print()
                        print("before filtering ")
                        print("rects :")
                        #print(rects)
                        print("Weights : ")
                        # print(weights)
                        print()
                        print("prev rects :")
                        print(prevrects)
                        print("prev Weights : ")
                        print(prevweights)
                        print()
                        print("===================================")
                        print()
                        #input()

                    i=0
                    if len(prevrects)>0 and len(prevweights)>0:

                        prevweights=prevweights.tolist()
                        prevrects=prevrects.tolist()

                        while(i<len(prevweights)):
                            
                            if prevweights[i][0]<float(1):
                                
                                prevweights.pop(i)
                                prevrects.pop(i)
                                i-=1
                            i+=1

                        prevrects=np.array([[x,y,x+w,y+h] for (x,y,w,h) in prevrects])
                        prevweights=np.array(prevweights)
                    i=0

                    if verbose:
                        print("***********************************")
                        print()
                        print("after filtering")
                        print("rects :")
                        # print(rects)
                        print("Weights : ")
                        # print(weights)
                        print()
                        print("prev rects :")
                        print(prevrects)
                        print("prev Weights : ")
                        print(prevweights)
                        print()
                        print("***********************************")
                        print()
                        #input()
                            
                    prevpick=non_max_suppression(prevrects,probs=None,overlapThresh=0.65)
                    # pick=non_max_suppression(rects,probs=None,overlapThresh=0.65)

                    #print(prevpick)
                    #print(pick)
                    if len(prevpick) > 0:
                        if verbose:
                            print("seg 1")

                        for (xa,ya,xb,yb) in prevpick :

                            cen=cu.getCentroid([(xa,ya),(xb,yb)])
                            centroids.append(cen)

                        if verbose:
                            print("seg 2")
                        i=0
                        
                        if "vertical" in linestatus:
                            for c in centroids:

                                if not cu.isPointInX(c,line2):
                                    centroids.pop(i)
                                    i-=1
                                i+=1
                        elif "horizontal" in linestatus:
                            
                                for c in centroids:

                                    if not cu.isPointInY(c,line2):
                                        centroids.pop(i)
                                        i-=1
                                    i+=1
                        i=-1
                        
                        for c in centroids:
                            
                            i+=1
                            cx=int(c[0])
                            cy=int(c[1])
                            p0=np.array([[cx,cy]],np.float32)

                            if verbose:
                                #print(type(cx))
                                #print(type(c))
                                print(c)
                                print(p0)

                            
                            p1, st, err = cv2.calcOpticalFlowPyrLK(gprevframe, gframe,p0, None, **lk_params)

                            if verbose:
                                print("after calcopticalflow :")
                                print(p0)
                                print(p1)


                            p1x=int(p1[0][0])
                            p1y=int(p1[0][1])
                            p1=(p1x,p1y)
                            p0x=int(p0[0][0])
                            p0y=int(p0[0][1])
                            p0=(p0x,p0y)

                            #print(i)
                            #print(prevpick)
                            #print(prevpick[i])
                            prevbox=[[prevpick[i][0],prevpick[i][1]],[prevpick[i][2],prevpick[i][3]]]

                            if verbose :
                                print("successful...")
                                print(prevpick[i][0],type(prevpick[i]))
                                print(box)
                                print(boxstatus)
                                print(prevbox)

                            toward = cu.getToward(p0,p1)
                            if verbose:
                                print("toward : ",toward)
                            if ("horizontal" in boxstatus and "vertical" in linestatus) or ("horizontal" in boxstatus and "horizontal" in linestatus) :
                                
                                pposl1,pposl2 = cu.getCentroidStatus2(box,prevbox,boxstatus)
                                
                                if verbose:
                                    print("pposl1  : ",pposl1)
                                    print("pposl2  : ",pposl2)

                                if "north" in toward[0][0]:

                                    if "+" in pposl2 :

                                        if "-" in wayin:
                                            
                                            self.insertPerson(prevbox,c,indatabase)

                                        elif "-" in wayout:

                                            self.insertPerson(prevbox,c,outdatabase)

                                    elif "-" in pposl2 and "+" in pposl1:

                                        if "-" in wayin:
                                            
                                            if self.removePerson(prevbox,c,indatabase):

                                                tdata={}
                                                tdata["event"]="in"

                                                incount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()
                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                    
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)

                                        elif "-" in wayout:

                                            if self.removePerson(prevbox,c,outdatabase):

                                                tdata={}
                                                tdata["event"]="out"

                                                outcount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)



                                if "south" in toward[0][0]:

                                    if "-" in pposl1 :

                                        if "+" in wayin:
                                            
                                            self.insertPerson(prevbox,c,indatabase)

                                        elif "+" in wayout:

                                            self.insertPerson(prevbox,c,outdatabase)

                                    elif "-" in pposl2 and "+" in pposl1:

                                        if "+" in wayin:
                                            
                                            if self.removePerson(prevbox,c,indatabase):

                                                
                                                tdata={}
                                                tdata["event"]="in"

                                                incount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()
                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)

                                        elif "+" in wayout:

                                            if self.removePerson(prevbox,c,outdatabase):

                                                tdata={}
                                                tdata["event"]="out"

                                                outcount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)
                                                
    ###############################################################################################################################################################

                            elif ("vertical" in boxstatus and "horizontal" in linestatus) or ("vertical" in boxstatus and "vertical" in linestatus) :
                                
                                pposl1,pposl2 = cu.getCentroidStatus2(box,prevbox,boxstatus)
                                
                                if verbose:
                                    print("pposl1  : ",pposl1)
                                    print("pposl2  : ",pposl2)

                                if "west" in toward[1][0]:

                                    if "+" in pposl2 :

                                        if "-" in wayin:
                                            
                                            self.insertPerson(prevbox,c,indatabase)

                                        elif "-" in wayout:

                                            self.insertPerson(prevbox,c,outdatabase)

                                    elif "-" in pposl2 and "+" in pposl1:

                                        if "-" in wayin:
                                            
                                            if self.removePerson(prevbox,c,indatabase):

                                                
                                                tdata={}
                                                tdata["event"]="in"

                                                incount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)

                                        elif "-" in wayout:

                                            if self.removePerson(prevbox,c,outdatabase):

                                                tdata={}
                                                tdata["event"]="out"

                                                outcount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)


                                                    
                                if "east" in toward[1][0]:

                                    if "-" in pposl1 :

                                        if "+" in wayin:
                                            
                                            self.insertPerson(prevbox,c,indatabase)

                                        elif "+" in wayout:

                                            self.insertPerson(prevbox,c,outdatabase)

                                    elif "-" in pposl2 and "+" in pposl1:

                                        if "+" in wayin:
                                            
                                            if self.removePerson(prevbox,c,indatabase):

                                                
                                                tdata={}
                                                tdata["event"]="in"

                                                incount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)

                                        elif "+" in wayout:

                                            if self.removePerson(prevbox,c,outdatabase):

                                                tdata={}
                                                tdata["event"]="out"

                                                outcount += 1
                                                
                                                if starttime != None and starttime != 0:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)
                                                    tm=starttime+datetime.timedelta(seconds=tm/1000)
                                                    inputs.starttime = tm
                                                    tm=tm.__str__()

                                                else:

                                                    tm=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                                                    tm=str(tm)
                                                tdata["incount"]=str(incount)
                                                tdata["outcount"]=str(outcount)
                                                tdata["time"]=str(tm)
                                                eventlist.append(tdata)
                                                                                                    

                            else:
                                
                                print()
                                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                print()
                                print ("for this configuration this application is unable to count people")
                                print()
                                print("but this application will detect and mark people ")
                                print()
                                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                print()

                            cv2.circle(frame, p1, 5, (0, 0, 255), -1)                    

                    for (xa,ya,xb,yb) in prevpick :

                        cv2.rectangle(frame,(xa,ya),(xb,yb),(0,255,0),2)
                        cen=cu.getCentroid([(xa,ya),(xb,yb)])
                        cv2.circle(frame, cen, 5, (0,255,0), -1)



                    prevframe=orig.copy()

                    prevcentroids=[]
                    centroids=[]
                    
                        
                    cv2.line(frame,(line1[0][0],line1[0][1]),(line1[1][0],line1[1][1]),(0,0,255),2)
                    cv2.line(frame,(line2[0][0],line2[0][1]),(line2[1][0],line2[1][1]),255,2)

                    intext="IN : "+str(incount)
                    outtext="OUT : "+str(outcount)
                    cv2.putText(frame,intext,(30,30), font, 1,(0,0,255),2)
                    cv2.putText(frame,outtext,(30,73), font, 1,(0,0,255),2)



                    if verbose :
                        print("######################################################")
                        print("indatabase => : ",indatabase)
                        print("outdatabase => : ",outdatabase)
                        print("indatabase length => : ",len(indatabase))
                        print("outdatabase length => : ",len(outdatabase))
                        print("incount : ",intext)
                        print("outcount : ",outtext)
                        print("total time : ",str(videolength))
                        print("current frame number : ",framenumber)
                        print("######################################################")

                    if verbose:
                        print("inclearthreadtimer : ",inclearthreadtimer)
                        print("outclearthreadtimer : ",outclearthreadtimer)
                            
                    if (inclearthreadtimer >= cleartime) :
                        if(len(indatabase)>0):
                            inclearthread=Thread(target=self.garbageClear,args=(indatabase,30),name="in_clear_thread")  # in database clear thread
                            if verbose:
                                print("in clear thread starting ")
                            inclearthread.start()
                            inclearthread.join()
                            if verbose:
                                print("in clear thread finished")
                            del(inclearthread)
                            inclearthread=None
                                
                            inclearthreadtimer=0
                    if (outclearthreadtimer >= cleartime) :
                        if(len(outdatabase)>0):
                            outclearthread=Thread(target=self.garbageClear,args=(outdatabase,30),name="out_clear_thread") # out database clear thread
                            if verbose:
                                print("out clear thread starting ")
                            outclearthread.start()
                            outclearthread.join()
                            if verbose:
                                print("out clear thread finished ")
                            del(outclearthread)
                            outclearthread=None
                        outclearthreadtimer=0
                    print(updatetime," / " , updatethreadtimer)
                    if (updatethreadtimer >= updatetime) :
                        if len(eventlist)>0:
                            #updatethread=Thread(target=self.updateInMDB,args=(self.db,"dwell",dwelldatabase,result),name="update_thread")
                            if verbose:
                                print("update thread starting ")
                            if self.ismongodb:
                                res=self.updateInMDB(self.db,"count",eventlist)
                            
                            #eventlist=[]
                        
                        updatethreadtimer =0   
                       

                    inclearthreadtimer += 1    #use this variable as a timer to start the thread for clearing the in database
                        
                    outclearthreadtimer += 1   #use this variable as a timer to start the thread for clearing the out database

                    updatethreadtimer +=1

                    if not novideo:
                        cv2.imshow("video",frame)
                        k=cv2.waitKey(1) & 0xFF
                        if k==ord("q"):
                            framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                            cv2.destroyAllWindows()
                            cap.release()
                            
                            raise(Exception("Video Finished"))
                            #return eventlist,framenumber
                    skip = 0
                    if not livestream and frameskip > 0:

                        while skip < frameskip:

                            r,prevframe=cap.read()
                            if not r:
                                print("video finished ")
                                raise(Exception("Video Finished"))
                            skip+=1

        except Exception as e:
            print()
            print("Fatal Error in CountPeople()")
            print()
            print("Error Name : ",e)
            print()
            print("Error in Details :")
            print()

            if verbose:
                err=sys.exc_info()
                print("Error Type : ",err[0])
                print("file name : ",err[-1].tb_frame.f_code.co_filename)
                print("Line Number : ",err[-1].tb_lineno)
            
            #countdata["in"]=incount
            #countdata["out"]=outcount
        finally:
            cv2.destroyAllWindows()
            if cap:
                if framenumber <= 0:
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                print("exiting ",framenumber)
                cap.release()
            print("Exitting from process of counting people")
            return eventlist ,framenumber




# ================================================================================ #
# function to read parameters from config file

    def InputFromConfigFile(self,configfile):
        try:
            # read parameters from configuration file
            f=open(configfile,"r")
            configuration=json.load(f)
            f.close()

            videostream = []
            conf = []
            # extract from configuration file
            for cameras in configuration["configuration"]["camera"]:
                ip_stream = cameras['stream']
                for modes in cameras["operation_mode"]:
                    if modes["name"] == "count":
                        # if operation mode is counter
                        conf = modes['configuration']
                                          # segment configuration

            parameters = []
            parameters.extend((ip_stream,conf,True,0,0,0,False,True))
            return parameters

        except Exception as e:
            print("fatal ERROR in InputFromConfigFile() : ")
            print("Error Name : ",e)
            print("Error in details : ")
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)
            return -1

    def start(self):

        params=self.InputFromGUI()
        data,fn=self.CountPeople(params)
        return (data,fn)


    #insert the data of the person in the proper place in database
    def insertPerson(self,person,cen,database):
        verbose=False
        
        newperson = True
        i=-1
        for p in database:
            i+=1
            
            if cu.isNearCentroid(cen,p[0]):
                
                #database[i][0].clear()
                database[i][0]=person
                #database[i][1].clear()
                database[i][1]=cen
                #database[i][2].clear()
                database[i][2]=[datetime.datetime.now()]
                if verbose:
                    print("insert in old")
                newperson=False
                return 1

        if newperson:

            pdata=[person,cen,[datetime.datetime.now()]]
            #pdata=[person,cen,[]]
            #print(pdata)
            if verbose:
                print("insert new")
            database.append(pdata)
            
            return 2



    #try removing person from the database if successful return True if person not found return False
    def removePerson(self,person,cen,database):

        verbose=False
        
        i=-1
        for p in database:
            i+=1
            if verbose :
                print("in remove : ")
            if cu.isNearCentroid(cen,p[0]):
                
                #database[i][0].clear()
                #database[i][1].clear()
                #database[i][2].clear()
                database.pop(i)
                if verbose :
                    print("removed")
                
                return True

        
        return False



    def garbageClear(database,gt):

        verbose=False
        
        #m=gt//60
        #s=gt%60
        #h=m//60
        #m=m%60
        #gt=datetime.time(h,m,s)

        i=0
        g=0
        while i<len(database):
            
            pdt=database[i][2][0]
            ms=(datetime.datetime.now()-pdt).total_seconds()
            if ms>=gt:
                database.pop(i)
                g+=1
                i-=1
                if verbose:
                    print("removed garbage : ",g)
            i+=1
        return database


    def updateInMDB(self,mdb,coln,dbo):

        try :
            
            result=cu.pushintoDB(mdb,coln,dbo)
            #dbo.clear()

            return result
            

        except Exception as e:
            print("Fatal Error in dwellTime()")
            print("Error Name : ",e)
            print("Error in Details :")
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)

    # [parameter] takes the form of [videostream,[{configuration}],bool livestream, int frameskip, int flushtime, int starttime, bool novideo, bool debug]
    def InputFromGUI(self):

        parser = argparse.ArgumentParser()
        parser.add_argument("-l", "--livestream", action="store_true", default=False,help="use this option if you are reading livestream from a camera")
        parser.add_argument("-w", "--width", default=250, help="set the width of the video")
        parser.add_argument("-s", "--frameskip", default=0, help="skip the number of frames in each iteration")
        parser.add_argument("-f", "--flushtime", default=1000, help="flush time")
        parser.add_argument("-v", "--verbose", action="store_true", default=True,help="use this switch for verbose mode")
        parser.add_argument("-n", "--novideo", action="store_true", default=False,help="show video footage")

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

            if args.novideo:
                novideo=True
            else:
                novideo=False
            if args.verbose:
                debug=True
            else:
                debug=False
            width=args.width
            if width<=0 or width>450 :
                width=250
            # read parameters from configuration file
            configfile=filedialog.askopenfilename()
            f = open(configfile, "r")
            configuration = json.load(f)
            f.close()

            videostream = []
            conf = configuration

            parameters = []
            parameters.extend((video, conf, True, 0, 0, 0, False, True))
            return parameters

        except Exception as e:
            print("fatal ERROR in InputFromConfigFile() : ")
            print("Error Name : ", e)
            print("Error in details : ")
            err = sys.exc_info()
            print("Error Type : ", err[0])
            print("file name : ", err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ", err[-1].tb_lineno)
            return -1

# =================================================================================================

if __name__=="__main__":

   pst=datetime.datetime.now()
   print()
   print("Program started at : ",pst.__str__())
   print()
   #configfile = "config.json"
   #params = InputFromConfigFile(configfile)
   #print("PARAM : ", params)
   #print(params)
   #data,fn=CountPeople(params)

   pc=PeopleCount()
   data,fn=pc.start()
   print()
   print()
   print(data)
   if(data):
       try:
           outjson=filedialog.asksaveasfilename()
           f=open(outjson,"w")
           json.dump(data,f)
           f.flush()
           f.close()
       except Exception as e:
           print("error occured while trying to write data to file")

   pet=datetime.datetime.now()

   totaltime=(pet-pst).total_seconds()
   print()
   print("Program started at : ",pst.__str__())
   print("Program ended at : ",pet.__str__())
   print("processed frame : ",fn)
   print()
   print("total processing time [in seconds]  : ",totaltime)

    









