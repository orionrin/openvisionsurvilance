################################################################
#                                                              #
# Split video #                                                #
# created and developped by Infinity Corporation #             #
# Developer : Ria Santra #                                     #
#                                                              #
#                                                              #
#                                                              #
################################################################



import cv2
import numpy as np
import datetime
import time
import argparse

verbose=False
def main():
    global verbose
    parser = argparse.ArgumentParser()
    parser.add_argument("videostream",help="The video input stream")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--advancedsplit",action="store_true", help="for this switch to work you have to input start split time and end split time")
    group.add_argument("-t", "--timedsplit", help="for this switch to work you have to input the time division in minitue")
    group.add_argument("-n", "--numberedsplit", help="for this switch to work you have to input number of output file")
    parser.add_argument("-s","--starttime",help="if you have used the switch [--advancedsplit] then --starttime sets the start time of the splited video  [ format: hour-min ] ")
    parser.add_argument("-e","--endtime",help="if you have used the switch [--advancedsplit] then --endtime sets the end time of the splited video [ format: hour-min ]  ")
    parser.add_argument("-v", "--verbose", action="store_true",help="use this switch for verbose mode")

    
    #video=input("Enter the path to video file : ")
    #print("How would you like to split the video file :")
    #print()
    #print("Press 1 to split by time division :")
    #print()
    #print("press 2 to split by number of output file : ")
    #print()
    #print("press 3 to split by date-time : ")
    #print()
    #selection=int(input("Enter Your Choice :"))

    args=parser.parse_args()

    if args.verbose:
        verbose=True
    print("verbose : ",verbose)

    video=args.videostream.strip()
    try:
        vstream=None

        ########################################################################3
        #if we are splitting video by time
        
        if args.timedsplit != None:
            temp=int(args.timedsplit.strip())
            if(temp<=0):
                temp=1
            ntime=temp*60
            outname=video.split('.')[0]
            cap=cv2.VideoCapture(video)
            if not cap.isOpened():
                cap.open()
            totalframes=cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps=int(cap.get(cv2.CAP_PROP_FPS))
            videolength=totalframes//fps
            nout=int(videolength//ntime)
            if videolength % ntime:
                nout+=1
            framespervideo=int(fps*ntime)
            if verbose==True:
                print("Total Frames : ",totalframes)
                print("Frames per output video file : ",framespervideo)
            vcount=0
            i=0
            while(vcount<nout):
                fps=int(cap.get(cv2.CAP_PROP_FPS))
                fourcc = cv2.VideoWriter_fourcc('D','I','V','X')
                vfile=outname+'_'+str(vcount)+'.avi'
                height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width=cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height=int(height)
                width=int(width)

                if verbose==True:
                    print("vfile : "+vfile)
                    print("fourcc : ",fourcc)
                    print("FPS : ",fps)
                    print("width : ",width)
                    print("height : ",height)
                    
                vstream=cv2.VideoWriter(vfile, fourcc, fps, (width, height), 1)
                while(i<framespervideo):
                    ret,frame=cap.read()
                    if not ret:
                        vstream.release()
                        cap.release()
                        print("video finished ")
                        return
                    vstream.write(frame)
                    i+=1
                i=0
                vcount+=1
                if vstream.isOpened():
                    vstream.release()
            if vstream.isOpened():
                vstream.release()
            if cap.isOpened():
                cap.release()
            return


        ########################################################################3
        #if we are splitting video by number of output file
        elif args.numberedsplit !=None:
            
            nout=int(args.numberedsplit.strip())
            if(nout<=0):
                nout=1
            outname=video.split('.')[0]
            cap=cv2.VideoCapture(video)
            if not cap.isOpened():
                cap.open()
            totalframes=cap.get(cv2.CAP_PROP_FRAME_COUNT)
            framespervideo=totalframes/nout
            verbose=True
            if verbose==True:
                print("Total Frames : ",totalframes)
                print("Frames per output video file : ",framespervideo)
            vcount=0
            i=0
            while(vcount<nout):
                fps=int(cap.get(cv2.CAP_PROP_FPS))
                fourcc = cv2.VideoWriter_fourcc('D','I','V','X')
                vfile=outname+'_'+str(vcount)+'.avi'
                height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width=cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height=int(height)
                width=int(width)

                
                verbose=True   ### for debugging purpose
                if verbose==True:
                    print("vfile : "+vfile)
                    print("fourcc : ",fourcc)
                    print("FPS : ",fps)
                    print("width : ",width)
                    print("height : ",height)
                vstream=cv2.VideoWriter(vfile, fourcc, fps, (width, height), 1)
                while(i<framespervideo):
                    ret,frame=cap.read()
                    if not ret:
                        vstream.release()
                        cap.release()
                        print("video finished ")
                        return
                    vstream.write(frame)
                    i+=1
                i=0
                vcount+=1
                if vstream.isOpened():
                    vstream.release()
            if vstream.isOpened():
                vstream.release()
            if cap.isOpened():
                cap.release()
            return

        ########################################################################3
        #if we are splitting video by advanced options
        elif args.advancedsplit:
            
            print("verbose : ",verbose)
            st=args.starttime
            et=args.endtime

            if verbose:
                print("input start time : ",st)
                print("input end time : ",et)
            cap=cv2.VideoCapture(video)
            
            if not cap.isOpened():
                cap.open()
            totalframes=cap.get(cv2.CAP_PROP_FRAME_COUNT)
            fps=int(cap.get(cv2.CAP_PROP_FPS))
            if verbose :
                print("total frames : ",totalframes)
                print("fps : ",fps)
            #videolength=totalframes//fps

            
            
            b=video.split('/')[-1].strip()
            if verbose:
                print("after spliting the video file path using'/'  : ",b)
                
            b=b.split('.')[0]

            if verbose:
                print("after extracting the video name with out extension : ",b)
            
            b=b.split('_')
            if verbose:
                print("after first split using'_' begining date time : ",b)
            on=b[2]
            bd=b[0]
            bt=b[1]
            if verbose :
                print("out name : ",on)
                print("begining date raw  : ",bd)
                print("begining time raw :",bt)
            bd=bd.split('-')
            bt=bt.split('-')
            if verbose:
                print("begining date splited : ",bd)
                print("begining time splited : ",bt)
            
            b=datetime.datetime(int(bd[0]),int(bd[1]),int(bd[2]),int(bt[0]),int(bt[1]))
            if verbose :
                print("begining date-time : ",b.__str__())
            st=st.split('-')
            if verbose:
                print("splited start-time : ",st)
                
            st=datetime.time(int(st[0]),int(st[1]))
            
            if st<b.time():
                sd=b.date()+datetime.timedelta(days=1)
                if verbose:
                    print("start time is less than begining time so video starts next day")
            else:
                sd=b.date()
                if verbose:
                    print("start time is greater than begining time so video starts same day")
            if verbose:
                print("start date : ",sd.__str__())
                print("start time : ",st.__str__())
            s=datetime.datetime.combine(sd,st)
            if verbose :
                print("start date-time : ",s.__str__())
            et=et.split('-')
            if verbose:
                print("splited end-time : ",et)
            et=datetime.time(int(et[0]),int(et[1]))
            if s.time()>et:
                ed=s.date()+datetime.timedelta(days=1)
                if verbose:
                    print("start time is less than end time so video ends next day")
            else:
                ed=s.date()
                if verbose:
                    print("start time is greater than end time so video ends the same day")
            if verbose:
                print("end date : ",ed.__str__())
                print("end time : ",et.__str__())
            e=datetime.datetime.combine(ed,et)
            if verbose :
                print("end date-time : ",e.__str__())
            
            o=s.__str__().replace(' ','_').replace(':','-')
            vfile=o+"_"+on+".avi"
            if verbose:
                print("video output file : ",vfile)

            
            fs=(s-b).total_seconds()
            fsf=int(fs*fps)

            ls = ((s+datetime.timedelta(days=1))-e).total_seconds()
            lsf=int(ls*fps)

            vcount=0
            while(vcount<fsf):
                ret,frame=cap.read()
                if not ret:
                    print("video finished")
                    cap.release()
                    return
                vcount+=1
            
            ws=(e-s).total_seconds()
            wf=int(ws*fps)

            
            vcount=0
            while(True):
                
                vcount=0
                fourcc = cv2.VideoWriter_fourcc('D','I','V','X')
                height=cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width=cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                height=int(height)
                width=int(width)
                vstream=cv2.VideoWriter(vfile, fourcc, fps, (width, height), 1)
                while(vcount<=wf):

                    ret,frame=cap.read()
                    if not ret:
                        vstream.release()
                        cap.release()
                        vstream.release()
                        print("video finished ")
                        return
                    vstream.write(frame)
                    vcount+=1

                vcount=0

                #if vstream.isOpened():
                #    vstream.release()

                while(vcount<=lsf):

                    ret,frame=cap.read()
                    if not ret:
                        vstream.release()
                        cap.release()
                        print("video finished ")
                        return
                    
                    vcount+=1

                s=s+datetime.timedelta(days=1)
                e=e+datetime.timedelta(days=1)
                o=s.__str__().replace(' ','_').replace(':','-')
                vfile=o+"_"+on+".avi"
                if verbose:
                    print("video output file : ",vfile)
                
                    

                

            
        else:
            print("Wrong choice")
            return
    except Exception as e:
        print("Fatal Error : ")
        print(e)
        if vstream != None:
            if vstream.isOpened():
                vstream.release()
        if cap.isOpened():
            cap.release()
        return
    #cap=cv2.VideoCapture(0)#Access default WebCam
    #width,height=640,480 #Aspect ratio of Video to be saved
    #fps=20 #required fps
    #fourcc = cv2.VideoWriter_fourcc('D','I','V','X')#FourCC code for AVI format
    #w = cv2.VideoWriter('out.AVI', fourcc, fps, (width, height), 1)#see blog
    #raw_input('Press Enter to start saving video ,and Esc to Stop and Quit')
    #while(True):
    #    f,frame=cap.read()
    #    frame=cv2.resize(frame,(width,height))
    #    w.write(frame)#write frame to video file
    #    ch=cv2.waitKey(1)
    #    if ch==27:
    #        cap.release()
    #        cv2.destroyAllWindows()
    #        break



if __name__ == '__main__' :
    main()
 
    #video = cv2.VideoCapture("video.mp4");
     
    # Find OpenCV version
    #(major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
     
    #if int(major_ver)  < 3 :
    #    fps = video.get(cv2.cv.CV_CAP_PROP_FPS)
    #    print "Frames per second using video.get(cv2.cv.CV_CAP_PROP_FPS): {0}".format(fps)
    #else :
    #    fps = video.get(cv2.CAP_PROP_FPS)
    #    print "Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps)
     
    #video.release(); 
