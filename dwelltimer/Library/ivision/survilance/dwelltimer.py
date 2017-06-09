################################################################
#                                                              #
# count people #                                               #
# created and developped by Infinity Corporation #             #
# Developer : Ria Santra and Pritam Samadder #                 #
#                                                              #
#                                                              #
#                                                              #
################################################################

from __future__ import print_function
import cv2
import imutils
from imutils.object_detection import non_max_suppression
import numpy as np
import cvutil as cu
import argparse
import json
from threading import Thread
import datetime
import sys
from multiprocessing import Pool
import csv
from pymongo import MongoClient

class DwellTimer:

    def __init__(self):

        self.conn=cu.connectDB()
        print("conn = : ",self.conn)
        #input()
        self.db=cu.selectDB(self.conn,"bufo")
        print("db = : ",self.db)
        #input()
    
    def calcDwellTime(self,parameters):

        # segregate different parameters from list
        #print("pppppppp    ",len(parameters))
        videostream = parameters[0]
        config = parameters[1]
        if not parameters[2]:
            livestream=False
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

        cleartime=100
        updatetime=1000

        if cleartime <= 0 :
            cleartime = 1000

        verbose=debug
        novideo=isnovideo

        totalframes=0
        fps=0
        videolength=0
        currentframetime=0
        remainingtime=0

        prevcentroids=[]
        centroids=[]
        currentflow=[]
        lk_params = dict( winSize  = (15,15),maxLevel = 2,criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

        database=[]

        first=True
        cap=None
        
        clearthreadtimer = 0    #use this variable as a timer to start the thread for clearing the in database
        updatethreadtimer=0

        incount = 0

        

        font = cv2.FONT_HERSHEY_SIMPLEX

        framenumber=0
        names=[]
        boxes=[]
        result=[None]
        dwelldatabase={}
        

        
        

        

        clearthread=Thread(target=self.garbageClear,args=(database,30,dwelldatabase,starttime),name="clear_thread")  # in database clear thread
        #updatethread=Thread(target=self.updateInMDB,args=(self.db,"dwell",dwelldatabase,result),name="update_thread")
        
        
        
        try:
            conf = []
            conf.append(config)     # bind the configuration dict obtained from function parameter into a List

            width=250

            if len(conf) > 0:

                for seg in conf:

                    names.append(seg['name'])       # segment name
                    boxes.append(seg['coordinates'])    # segment box coordinates (diagonally opposite vertices)

            else:
                print("No segment defined in the configuration file")
                return -1

            for n in names:
                dwelldatabase[n]=[]

            # initialise HOG descriptor for people detecting
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

                        first=False

                    currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)
                    remainingtime=videolength-currentframetime
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)

                totalframes=cap.get(cv2.CAP_PROP_FRAME_COUNT)
                print(totalframes)
                videolength=(totalframes/fps)*1000  # in seconds

            elif livestream:
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
                #print(ip_stream.read())

    # ========================================================================
            while True:
                ret = True
                if livestream:
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
                    (ret,frame)=cap.read()
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                    currentframetime=cap.get(cv2.CAP_PROP_POS_MSEC)


                if not ret:
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                    print ("video finished")
                    cv2.destroyAllWindows()
                    cap.release()
                    raise(Exception("Video Finished"))

                orig=frame.copy()   # make a copy of the current frame

                frame=imutils.resize(frame,width=min(width,frame.shape[1])) #resize the frame

                prevframe=imutils.resize(prevframe,width=min(width,prevframe.shape[1]))  #resize previous frame

                (prevrects,prevweights)=hog.detectMultiScale(prevframe,winStride=(4,4),padding=(4,4),scale=1.05)  #detect human in previous frame
                print(prevrects)
                print(prevweights)

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

                prevpick=non_max_suppression(prevrects,probs=None,overlapThresh=0.65)


                if len(prevpick) > 0 : #and len(pick) > 0:
                    if verbose:
                        print("seg 1")

                    for (xa,ya,xb,yb) in prevpick :

                        cen=cu.getCentroid([(xa,ya),(xb,yb)])
                        centroids.append(cen)

                    if verbose:
                        print("seg 2")



                    i=-1

                    for c in centroids:

                        i+=1
                        cx=int(c[0])
                        cy=int(c[1])
                        p0=np.array([[cx,cy]],np.float32)


                        p0x=int(p0[0][0])
                        p0y=int(p0[0][1])
                        p0=(p0x,p0y)



                        prevbox=[[prevpick[i][0],prevpick[i][1]],[prevpick[i][2],prevpick[i][3]]]

                        index=-1

                        index=cu.pointInWhichBox(p0,boxes)


                        if index !=-1:              #in the person is in any of the segments

                            name=names[index]
                            print(name)
                            print(dwelldatabase)
                            print(self.insertPerson(prevbox,cen,database,name,cap.get(cv2.CAP_PROP_POS_MSEC)/1000,len(dwelldatabase[name])))# insert person

                        elif index == -1:

                            status,data=self.removePerson(prevbox,cen,database)  #remove person

                            if status:

                                print(data)

                                segname=data[3][0]

                                if starttime != None and starttime!=0:

                                    print(starttime)

                                    personin=starttime+datetime.timedelta(seconds=data[4][0])
                                    personin=personin.__str__()

                                    personout=starttime+datetime.timedelta(seconds=data[5][0])
                                    personout=personout.__str__()

                                else:

                                    personin = str(data[4][0])

                                    personout = str(data[5][0])

                                personincount=data[7][0]
                                personoutcount=data[8][0]

                                partialdata=data[9][0]
                                totalsec=data[6][0]
                                #d=[segname,personin,personout,totalsec,personincount,personoutcount,partialdata]
                                d={"segname":segname,"personin":personin,"personout":personout,"totalsec":totalsec,"personincount":personincount,"personoutcount":personoutcount,"partialdata":partialdata}

                                dwelldatabase[segname].append(d)


                        cv2.circle(frame, p0, 5, (0, 0, 255), -1)

                    for (xa,ya,xb,yb) in prevpick :

                        cv2.rectangle(frame,(xa,ya),(xb,yb),(0,255,0),2)
                        cen=cu.getCentroid([(xa,ya),(xb,yb)])
                        cv2.circle(frame, cen, 5, (0,255,0), -1)

                for b in boxes:
                    cv2.rectangle(frame,(b[0][0],b[0][1]),(b[1][0],b[1][1]),(0,255,0),2)

                prevframe=orig.copy()

                prevcentroids=[]
                centroids=[]
                #print("dwelldatabase 1 : ",dwelldatabase)
                #input()
                print(clearthreadtimer ," / ",cleartime)
                #print("database : ",dwelldatabase)
                #input()
                if (clearthreadtimer >= cleartime) :
                    if(len(database)>0):
                        print(database)
                        #input()
                        clearthread=Thread(target=self.garbageClear,args=(database,30,dwelldatabase,starttime),name="clear_thread")  #  database clear thread
                        if verbose:
                            print("clear thread starting ")
                        clearthread.start()
                        clearthread.join()
                        if verbose:
                            print("clear thread finished")
                        del(clearthread)
                        clearthread=None
                    clearthreadtimer=0
                    
                #print("dwelldatabase 2 : ",dwelldatabase)
                #print(type(dwelldatabase))
                #input()
                print(updatethreadtimer ," / ",updatetime)
                if (updatethreadtimer >= updatetime) :
                    if len(dwelldatabase)>0:
                        #updatethread=Thread(target=self.updateInMDB,args=(self.db,"dwell",dwelldatabase,result),name="update_thread")
                        if verbose:
                            print("update thread starting ")
                        res=self.updateInMDB(self.db,"dwell",dwelldatabase)
                        #dwelldatabase.clear()
                        for k in dwelldatabase:
                            dwelldatabase[k]=[]
                        #dwelldatabase.pop('_id')
                        
                        #print (res)
                        #dwelldatabase.clear()
                        if verbose:
                            print("update thread finished")
                    updatethreadtimer=0
                print("dwelldatabase 3 : ",dwelldatabase)
                #input()
                #print(type(dwelldatabase))
                    

                    
                    
                    
                    
                    
                        

                    


                clearthreadtimer += 1    #use this variable as a timer to start the thread for clearing the database
                updatethreadtimer +=1
                if not novideo:
                    cv2.imshow(str(video),frame)
                    k=cv2.waitKey(1) & 0xFF
                    if k==ord("q"):
                        framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                        cv2.destroyAllWindows()
                        cap.release()

                        raise(Exception("Video Finished"))


        except Exception as e:
            print("Fatal Error in dwellTime()")
            print("Error Name : ",e)
            print("Error in Details :")

            if verbose:
                err=sys.exc_info()
                print("Error Type : ",err[0])
                print("file name : ",err[-1].tb_frame.f_code.co_filename)
                print("Line Number : ",err[-1].tb_lineno)


        finally:
            cv2.destroyAllWindows()
            if cap:
                if framenumber <= 0:
                    framenumber=cap.get(cv2.CAP_PROP_POS_FRAMES)
                print("exiting ",framenumber)
                cap.release()
            return dwelldatabase ,framenumber,fps


    #function for inserting data in database for only dwelltime script
    def insertPerson(self,person,cen,database,name,intime,count):
        try:

            verbose=True

            newperson = True
            i=-1
            for p in database:
                i+=1

                if cu.isNearCentroid(cen,p[0]):


                    database[i][0]=person

                    database[i][1]=cen

                    database[i][2]=[datetime.datetime.now()]
                    database[i][3]=[name]
                    database[i][5]=[intime]


                    personin = database[i][4][0]
                    personout = database[i][5][0]

                    insec=(personout-personin)
                    database[i][6]=[insec]
                    database[i][8]=[count]
                    if verbose:
                        print("insert in old")
                    newperson=False
                    return 1

            if newperson:


                personin = intime
                personout = intime
                insec=(personout-personin)

                pdata=[person,cen,[datetime.datetime.now()],[name],[intime],[intime],[insec],[count],[count],[False]]

                if verbose:
                    print("insert new")
                database.append(pdata)

                return 2

        except Exception as e:
            print("Fatal Error in insertPerson()")
            print("Error Name : ",e)
            print("Error in Details :")

            if verbose:
                err=sys.exc_info()
                print("Error Type : ",err[0])
                print("file name : ",err[-1].tb_frame.f_code.co_filename)
                print("Line Number : ",err[-1].tb_lineno)

    #try removing person from the database if successful return True if person not found return False
    def removePerson(self,person,cen,database):

        try:

            verbose=True

            i=-1
            for p in database:
                i+=1
                if verbose :
                    print("in remove : ")
                if cu.isNearCentroid(cen,p[0]):

                    database[i][9]=[True]
                    data=database[i].copy()
                    
                    database.pop(i)
                    if data[4][0]==data[5][0]:
                        return [False,[]]
                    if verbose :
                        print("removed")

                    return [True,data]
            return [False,[]]

        except Exception as e:
            print("Fatal Error in removePerson()")
            print("Error Name : ",e)
            print("Error in Details :")

            if verbose:
                err=sys.exc_info()
                print("Error Type : ",err[0])
                print("file name : ",err[-1].tb_frame.f_code.co_filename)
                print("Line Number : ",err[-1].tb_lineno)

    #clear the temporary database
    def garbageClear(self,db,ct,dwdb,starttime):

        try:

            verbose = True
            i=0
            g=0
            
            while i<len(db):

                pdt=db[i][2][0]
                ms=(datetime.datetime.now()-pdt).total_seconds()

                if ms>=ct:

                    data=db[i].copy()
                    db.pop(i)

                    if starttime != None and starttime!=0:

                        personin=starttime+datetime.timedelta(seconds=data[4][0])
                        personout=starttime+datetime.timedelta(seconds=data[5][0])

                        insec=(personout-personin).total_seconds()

                    else:

                        personin = data[4][0]
                        personout = data[5][0]

                        insec=(personout-personin)



                    if insec >= 3:

                        data[9]=[False]

                        #data[6]=[insec]
                        segname=data[3][0]

                        #if starttime != None and starttime!=0:

                            #personin=starttime+datetime.timedelta(seconds=data[4][0])
                            #personin=personin.__str__()

                            #personout=starttime+datetime.timedelta(seconds=data[5][0])
                            #personout=personout.__str__()

                        #else:

                            #personin = str(data[4][0])

                            #personout = str(data[5][0])

                        personin=personin.__str__()
                        personout=personout.__str__()


                        personincount=data[7][0]
                        #personoutcount=data[8][0]
                        personoutcount=len(dwdb[segname])

                        partialdata=data[9][0]

                        #d=[segname,personin,personout,insec,personincount,personoutcount,partialdata]

                        d={"segname":segname,"personin":personin,"personout":personout,"totalsec":totalsec,"personincount":personincount,"personoutcount":personoutcount,"partialdata":partialdata}
                        

                        dwdb[segname].append(d)
                    g+=1
                    i-=1

                i+=1
            if verbose:
                print("removed garbage : ",g)
            #return dwdb



        except Exception as e:
            print("Fatal Error in garbageClear()")
            print("Error Name : ",e)
            print("Error in Details :")

            
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)

    
    def updateInMDB(self,mdb,coln,dbo):

        try :
            print(type(dbo))
            for k in dbo:
                print(k)
            #dbo=[{"author": "Mike","text": "Another post!","tags": ["bulk", "insert"], "date": datetime.datetime(2009, 11, 12, 11, 14)},{"author": "Eliot", "title": "MongoDB is fun","text": "and pretty easy too!", "date": datetime.datetime(2009, 11, 10, 10, 45)}]
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
        


#write data to a json file
##def writeCountData(filename,data):
##    try:
##        f=open(filename,"w")
##        json.dump(data,f)
##        f.flush()
##        f.close()
##        return True
##    except Exception as e:
##        print("Error occured while writing data to file : ",filename)
##        print(e)
##        return False

# ======================================================================================== #
    #use this function to input parameters from arguments
    def CommandLineInput(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("videostream",help="The video input stream")
        parser.add_argument("-o","--outputfile",default=None, help="path to output json file")
        parser.add_argument("-l", "--livestream", action="store_true",help="use this option if you are reading livestream from a camera")
        parser.add_argument("-c","--configuration",required=True, help="path to configuration file")
        parser.add_argument("-n", "--novideo", action="store_true",help="use this switch to process without showing video")
        parser.add_argument("-v", "--verbose", action="store_true",help="use this switch for verbose mode")
        parser.add_argument("-f","--frameskip",default=0, help="skips number of frames")
        parser.add_argument("-g","--garbageclear",default=1000, help="time to flush the list")
        parser.add_argument("-s","--starttime",default=None, help="real start time of this video stream")

        try:
            args=parser.parse_args()
            if args.livestream:
                islivestream=True
                videostreams = str(args.videostream)
            else :
                islivestream=False
                videostreams = args.videostream
            output=args.outputfile
            confpath = args.configuration
            frameskip=int(args.frameskip)
            if args.novideo:
                isnovideo=True
            else:
                isnovideo=False
            if args.verbose:
                debug=True
            else:
                debug=False
            starttime=args.starttime

            flushtime=int(args.garbageclear)

            # split each videostreams seperated by comma
            import re
            videostream = []
            pattern = re.compile("^\s+|\s*,\s*|\s+$")
            videostream.extend([x for x in pattern.split(videostreams) if x])

            parameters = []
            parameters.extend((videostream,confpath,islivestream,isnovideo,starttime,frameskip,flushtime,output,debug))
            print(parameters)
            return parameters

        except Exception as e:
            print("fatal ERROR in calcDwellTime_CommandInput() : ")
            print("Error Name : ",e)
            print("Error in details : ")
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)
            return -1

# ================================================================================ #
    # function to read parameters from config file

    def InputFromConfigFile(self,configfile):
        try:
            # read parameters from configuration file
            f=open(configfile,"r")
            configuration=json.load(f)
            print(configuration)
            f.close()

            videostream = []
            conf = []
            output = 'out.json'
            # extract from configuration file
            for cameras in configuration["configuration"]["camera"]:
                ip_stream = cameras['stream']
                for modes in cameras["operation_mode"]:
                    if modes["name"] == "dwell":
                        # if operation mode is dwell time counter
                        for seg in modes['configuration']['segments']:
                            conf.append(seg)               # segment configuration
                        videostream.append(ip_stream)           # IP stream corresponding to camera_id

            parameters = []
            #parameters.extend((videostream,conf,True,False,None,None,1000,output,True))
            parameters.extend((videostream,conf,False,False,None,None,1000,output,True))
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

    def start(self,confile) :

            st=datetime.datetime.now()
            print("starting......")

            #CLIinput = CommandLineInput()      # get parameters from Command Line Interface
            #dt=DwellTimer()
            CLIinput = self.InputFromConfigFile(confile)       # get parameters from Config file

            print("cli input ... ",CLIinput)
            print()
            print()
            parameters=[]       # list containing lists of parameter to be sent to calcDwellTime function as input arguments
            videostreams = CLIinput[0]
            config = CLIinput[1]

            # if videostreams contains more than 1 item,
            if (videostreams):
                # iterate each items of videostream seperately with other parameters constant
                i = 0
                for video in videostreams:
                    if isinstance(CLIinput[1],list):
                        config = CLIinput[1][i]
                    parameters.append([video,config,CLIinput[2],CLIinput[3],CLIinput[4],CLIinput[5],CLIinput[6],CLIinput[7],CLIinput[8]])
                    i += 1
            else:
                # if input contains single videostream
                raise(Exception("No video stream found in input"))

            print(parameters)

            self.calcDwellTime(parameters[0])
            


# ========================= main ============================================== #

##if __name__=="__main__" :
##
##    st=datetime.datetime.now()
##
##    #CLIinput = CommandLineInput()      # get parameters from Command Line Interface
##    CLIinput = InputFromConfigFile('../config.json')       # get parameters from Config file
##    parameters=[]       # list containing lists of parameter to be sent to calcDwellTime function as input arguments
##    videostreams = CLIinput[0]
##    config = CLIinput[1]
##
##    # if videostreams contains more than 1 item,
##    if (videostreams):
##        # iterate each items of videostream seperately with other parameters constant
##        i = 0
##        for video in videostreams:
##            if isinstance(CLIinput[1],list):
##                config = CLIinput[1][i]
##            parameters.append([video,config,CLIinput[2],CLIinput[3],CLIinput[4],CLIinput[5],CLIinput[6],CLIinput[7],CLIinput[8]])
##            i += 1
##    else:
##        # if input contains single videostream
##        raise(Exception("No video stream found in input"))
##
##    print(parameters)

    # ==================================================================================== #
    # Multiprocessing script to allow multiple videostreams to operate parallely
##    core = 2  # input core
##    pool = Pool(core)
##    data,fn,fps=pool.map(calcDwellTime,parameters)
##    #close the pool and wait for the work to finish
##    pool.close()
##    pool.join()
##
##    et=datetime.datetime.now()
##    psec=(et-st).total_seconds()
##    pfps=fn/psec
##
##    print("processing started at : ",st.__str__())
##    print("processing ended at : ",et.__str__())
##    print("processed frames : ",fn)
##    print("processing seconds : ",psec)
##    print("video fps : ",vfps)
##
##    print("processing fps : ",pfps)
