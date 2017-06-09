################################################################
#                                                              #
# easy corp #                                                  #
# created and developped by Pritam Samadder #                  #
# Developer : Pritam Samadder AND Ria Santra #                 #
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
import datetime
import time
import math
from pymongo import MongoClient
import sys


verbose=False
######################################################################################
# DATABASE CONNECTIONPART
#################################################################################

def connectDB(host="localhost",port=27017):

    try:
        
        #client = MongoClient()
        client = MongoClient(host, port)
        #db = client.bufo
        return client
    except Exception as e:
            print("Fatal Error in connectdb()")
            print("Error Name : ",e)
            print("Error in Details :")

            
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)
        

def selectDB(client,database):
    try:
        
        db=client[database]
        return db
    except Exception as e:
            print("Fatal Error in selectdb()")
            print("Error Name : ",e)
            print("Error in Details :")

            
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)


def pushintoDB(mdatabase,collection,dataobject):

    try:

##      print(type(dataobject))
##      print(len(dataobject))
##      input()
        storeplace=mdatabase[collection]
        #result= storeplace.insert_many(dataobject)
        #result= storeplace.insert(dataobject)
        if type(dataobject) is dict:
            for k in dataobject:

                for v in dataobject[k]:
                    result= storeplace.insert(v)
        elif type (dataobject) is list:
            for d in dataobject:
                print("=================================================")
                print(type(d))
                print(d)
                result= storeplace.insert(d)
        
        return result
    except Exception as e:
            print("Fatal Error in pushintodb()")
            print("Error Name : ",e)
            print("Error in Details :")

            
            err=sys.exc_info()
            print("Error Type : ",err[0])
            print("file name : ",err[-1].tb_frame.f_code.co_filename)
            print("Line Number : ",err[-1].tb_lineno)


# get centroid of a box
def getCentroid(rect):
    
    x1=rect[0][0]
    y1=rect[0][1]
    x2=rect[1][0]
    y2=rect[1][1]

    midx=(x2-x1)//2
    midy=int(y2-y1)//2
    cx=x1+midx
    cy=y1+midy

    return (cx,cy)




#Mouse events for getting two points
clicked=False
point1=()
point2=()
points=[]
def onClikDrag(event,x,y,flags,param):
    global clicked
    global points
    global point1
    global point2
    global verbose
    if event==cv2.EVENT_LBUTTONDOWN:
        points=[(x,y)]
        point1=(x,y)
        point2=(x,y)
        clicked=True
        print("Clicked...",points)

    elif event == cv2.EVENT_MOUSEMOVE:
        if clicked==True:
            point2=(x,y)
        
    elif event==cv2.EVENT_LBUTTONUP:
        points.append((x,y))
        point2=(x,y)
        clicked=False
        #print(points)
        print("Released...",points)
            



#Get TOp-Left and Buttom-Right for rectangle points
def getTopLeftButtomRight(cpoints):
    x1=cpoints[0][0]
    x2=cpoints[1][0]
    y1=cpoints[0][1]
    y2=cpoints[1][1]

    if x2 > x1 and y2 > y1:         # Top-Left , Buttom-Right
        return cpoints

    elif x1 > x2 and y1 > y2:       # Buttom-Right , Top-Left  
        cpoints=[]
        cpoints=[(x2,y2),(x1,y1)]
        return cpoints
    
    elif x1 > x2 and y1 < y2:       # Top-Right , Buttom-Left
        cpoints=[]
        cpoints=[(x2,y1),(x1,y2)]
        return cpoints
    
    elif x2 > x1 and y2 < y1:       # Buttom-Left , Top-Right
        cpoints=[]
        cpoints=[(x1,y2),(x2,y1)]
        return cpoints
    elif x1 == x2 and y1 == y2:
        cpoints = -1
        return cpoints
    else :                          # Any Other Things
        cpoints=-1
        return cpoints

#get if the point is in range of X1 , X2
def isPointInX(p,line):

    lx1=line[0][0]
    lx2=line[1][0]

    mx1=p[0]-lx1
    mx2=lx2-p[0]

    if mx1>=0 and mx2>=0:
        return True
    else :
        return False


#get if the point is in range of Y1 , Y2
def isPointInY(p,line):

    ly1=line[0][1]
    ly2=line[1][1]

    my1=p[1]-ly1
    my2=ly2-p[1]

    if my1>=0 and my2>=0:
        return True
    else :
        return False

#Get tf the box is in range of x1 x2
def isInX(box,line):
    
    bx1=box[0][0]
    bx2=box[1][0]
    lx1=line[0][0]
    lx2=line[1][0]

    mx1=bx1-lx1
    mx2=lx2-bx2

    if mx1>=0 and mx2>=0:
        return True
    else :
        return False


def isInY(box,line):
    
    by1=box[0][1]
    by2=box[1][1]
    ly1=line[0][1]
    ly2=line[1][1]

    my1=by1-ly1
    my2=ly2-by2

    if my1>=0 and my2>=0:
        return True
    else :
        return False

    






def DrawRect(img,rectpoints):
    if len(rectpoints)==2:
        y1=rectpoints[0][1]
        y2=rectpoints[1][1]
        x1=rectpoints[0][0]
        x2=rectpoints[1][0]
        cv2.rectangle(img, (x1,y1), (x2,y2), (0,255,0),2)
        return img








#check if a point is located in the given box
def isPointInBox(point,box):
    global verbose
    if verbose:
        print("box : ",box)
        print("point  : ",point)
    px=point[0]
    py=point[1]

    
    bx1=box[0][0]
    by1=box[0][1]
    bx2=box[1][0]
    by2=box[1][1]


    mx1=px-bx1
    my1=py-by1
    mx2=px-bx2
    my2=py-by2

    if mx1 >= 0 and my1 >= 0 and mx2 <= 0 and my2 <= 0 :
        return True
    else:
        return False

#check if the point is in any box.if true return the box index
def pointInWhichBox(point,boxes):

    index=-1
    for i in range(0,len(boxes)):

        if isPointInBox(point,boxes[i]):
            index=i
            break

    return index
    


# checks if a point p1 is near to another point p2 [by near we mean in maximum range of pboundary in any diraction from p2]
def isNearPoint(p1,p2,pboundary):
    global verbose
    if verbose:
        print("is near point : ",p1," : ",p2)
    bx1 = p2[0]-pboundary
    by1 = p2[1]-pboundary
    bx2 = p2[0]+pboundary
    by2 = p2[1]+pboundary

    box=[(bx1,by1),(bx2,by2)]
    
    status = isPointInBox(p1,box)
    return status








#checks if a point is near the centroid of the box
def isNearCentroid(point,box):
    
    global verbose
    status=False
    if verbose:
        print("is near centroid arg ",point," : ",box)
    if isPointInBox(point,box):
        cen=getCentroid(box)

        status=isNearPoint(point,cen,13)
    else:
        status=False
    if verbose:
        print("is near centroid ",status)
    return status












#returns the movement of the point to opoint
def getToward(point ,opoint):
    
    mpx = opoint[0]-point[0]
    mpy = opoint[1]-point[1]

    if mpx > 0 :
        w2 = "east"
    elif mpx < 0 :
        w2 = "west"
    else:
        w2 = "="


    if mpy > 0 :
        w1 = "south"
    elif mpy < 0 :
        w1 = "north"
    else:
        w1 = "="

    return [(w1,mpy),(w2,mpx)]

    
#get status of a point

def getPointStatus(box,p,bs):

    ba=box[0][0]
    bb=box[1][1]
    bc=box[1][0]
    bd=box[1][1]

    px=p[0]
    py=p[1]

    if "horizontal" in bs :

        ml2 = int(py-bc[1])
        ml1=int(py-ba[1])

        if ml2 <= 0 :
            pposl2x="-"
        else:
            pposl2x="+"
        if ml1 <= 0:
            pposl1x="-"
        else:
            pposl1x="+"
        return(pposl1x,pposl2x)
    if "vertical" in bs :
        print("we have not implemented for vertical line yet")
        return -1

#get status of a point wher box can be placed anyhow
def getPointStatus2(box,p,bs):

    ba=box[0][0]
    bb=box[1][1]
    bc=box[1][0]
    bd=box[1][1]

    px=p[0]
    py=p[1]

    if "horizontal" in bs :

        l1y=getYGivenX(box[0],px)[1]
        l2y=getYGivenX(box[1],px)[1]

        
        difl1 = l1y-py
        difl2 = l2y-py
        #print("executing get point status 2 difl1,difl2 : ",(difl1,difl2))
        if difl2 < 0 :

            pposl2="+"
        elif difl2 >= 0 :
            
            pposl2 = "-"


        if difl1 < 0 :

            pposl1 = "+"

        elif difl1 >= 0 :

            pposl1 = "-"
        #print("finishing get point status 2 ")
        return (pposl1,pposl2)




        
    elif "vertical" in bs :

        l1x=getXGivenY(box[0],py)[0]
        l2x=getXGivenY(box[1],py)[0]


        difl1 = l1x-px
        difl2 = l2x-px
        

        if difl2 < 0 :

            pposl2="+"
        elif difl2 >= 0 :
            
            pposl2 = "-"


        if difl1 < 0 :

            pposl1 = "+"

        elif difl1 >= 0 :

            pposl1 = "-"

        return (pposl1,pposl2)

#get centroid status of a person
def getCentroidStatus2(box,person,bs):

    

    cx,cy=getCentroid(person)
    #print("getcentroid status 2 cx,cy : ",(cx,cy))
    #print("getcentroid status 2 bs: ",bs)
    pposl1,pposl2=getPointStatus2(box,[cx,cy],bs)

    return (pposl1,pposl2)
    

    


#get the status of the person 
def getPersonStatus(box,person,bs):

    
    ba=box[0][0]
    bb=box[1][1]
    bc=box[1][0]
    bd=box[1][1]

    ptl=person[0]
    pbr=person[1]

    if "horizontal" in bs :
        mtll2=ptl[1]-bc[1]
        mbrl2=pbr[1]-bc[1]
        mtll1=ptl[1]-ba[1]
        mbrl1=pbr[1]-ba[1]
        
        
        if mtll2 <= 0:                  #if top left point of the person is over the line 2
            ppostll2 = "-"
        else:
            ppostll2 = "+"

        if mbrl2 <= 0:                  #if buttom right point of the person is over the line 2
            pposbrl2 = "-"
        else:
            pposbrl2 = "+"


        if mtll1 <= 0:                 #if top left point of the person is over the line 1
            ppostll1 = "-"
        else:
            ppostll1 = "+"


        if mbrl1 <= 0:                #if buttom right point of the person is over the line 2
            pposbrl1 = "-"
        else:
            pposbrl1 = "+"


        return (ppostll1,pposbrl1,ppostll2,pposbrl2)



    if "vertical" in bs :
        print("we have not implemented for vertical line yet")
        return -1










#insert the data of the person in the proper place in database
def insertPerson(person,cen,database):
    global verbose
    
    newperson = True
    i=-1
    for p in database:
        i+=1
        
        if isNearCentroid(cen,p[0]):
            
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
def removePerson(person,cen,database):

    global verbose
    
    i=-1
    for p in database:
        i+=1
        if verbose :
            print("in remove : ")
        if isNearCentroid(cen,p[0]):
            
            #database[i][0].clear()
            #database[i][1].clear()
            #database[i][2].clear()
            database.pop(i)
            if verbose :
                print("removed")
            
            return True

    
    return False


def garbageClear(database,gt):

    global verbose
    
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

    



#get the distance between to points    argument ([x1,y1],[x2,y2])
def getDistance(p1,p2):

    x1=p1[0]
    y1=p1[1]
    
    x2=p2[0]
    y2=p2[1]


    mx=x2-x1
    my=y2-y1

    mxy=(mx**2)+my(**2)
    distance=math.sqrt(mx2)
    distance=math.ceil(d)

    return distance


#get y when x is given    argument ([[x1,y1],[x2,y2]],px)
def getYGivenX(line,px):

    global verose

    #verbose=True

    x1=line[0][0]
    y1=line[0][1]
    x2=line[1][0]
    y2=line[1][1]

    my=y1-y2
    mx=x1-x2
    m=my/mx

    c=y1-(m*x1)

    if verbose:
        print("line : ",line)
        print("slope M : ",m)
        print("C : ",c)

    py=(m*px)+c

    
    py=math.ceil(py)

    return (px,py)
    

#get x when y is given    argument ([[x1,y1],[x2,y2]],py)
def getXGivenY(line,py):

    
    
    global verose

    #verbose=True

    x1=line[0][0]
    y1=line[0][1]
    x2=line[1][0]
    y2=line[1][1]

    my=y1-y2
    mx=x1-x2
    m=my/mx

    c=y1-(m*x1)

    if verbose:
        print("line : ",line)
        print("slope M : ",m)
        print("C : ",c)
        

    px=(py-c)/m
    
    
    px=math.ceil(px)

    return (px,py)


   


#Get right and left points for line
def getBoxPointandStatus(cpoints):

    

    
    x1=int(cpoints[0][0])
    y1=int(cpoints[0][1])
    x2=int(cpoints[1][0])
    y2=int(cpoints[1][1])

    dx=x1-x2
    dy=y1-y2


    difx=abs(dx)
    dify=abs(dy)

    if(difx>dify):
        boxstatus="horizontal"

    elif(difx<dify):
        boxstatus="vertical"

    else:
        boxstatus="unknown"
        cpoints=-1
        return (-1,-1,-1,-1)

    if "horizontal" in boxstatus:
        if dx >= 0:  # if first point x is lower than the second point x swap the points
            tx=x1
            ty=y1
            x1=x2
            y1=y2
            x2=tx
            y2=ty
            
    elif "vertical" in boxstatus:
        if dy >= 0:  # if first point x is lower than the second point x swap the points
            tx=x1
            ty=y1
            x1=x2
            y1=y2
            x2=tx
            y2=ty
    else:
        return (-1,-1,-1,-1)
    
    line1=[[x1,y1],[x2,y2]]
    length=30
    line2=getParallelLine(line1,length,boxstatus)
    
    if line2==-1:
        return (-1,-1,-1,-1)
    
    box=[line1,line2]
    return (boxstatus,box,line1,line2)




# get the buttom left point of a rectangle given width  or length  arguments ([[x1,y1],[x2,y2]],int,boxstatus)
def getParallelLine(line,length,boxstatus):

    

    x1=line[0][0]
    y1=line[0][1]
    x2=line[1][0]
    y2=line[1][1]

    if "horizontal" in boxstatus:
        #print("executing horizontal")
        lx1=x1-((length*(y2-y1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        ly1=y1+((length*(x2-x1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        lx1=math.ceil(lx1)
        ly1=math.ceil(ly1)

        lx2=x2-((length*(y2-y1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        ly2=y2+((length*(x2-x1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        lx2=math.ceil(lx2)
        ly2=math.ceil(ly2)
        
    elif "vertical" in boxstatus:
        #print("executing vertical")
        lx1=x1+((length*(y2-y1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        ly1=y1-((length*(x2-x1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        lx1=math.ceil(lx1)
        ly1=math.ceil(ly1)

        lx2=x2+((length*(y2-y1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        ly2=y2-((length*(x2-x1))/(math.sqrt((((y2-y1)**2)+((x2-x1)**2)))))
        lx2=math.ceil(lx2)
        ly2=math.ceil(ly2)
    else:
        return -1
        

    return [[lx1,ly1],[lx2,ly2]]






#Get right and left points for line
def getLineStatus(cpoints):
    x1=int(cpoints[0][0])
    y1=int(cpoints[0][1])
    x2=int(cpoints[1][0])
    y2=int(cpoints[1][1])

    dx=x1-x2
    dy=y1-y2


    difx=abs(dx)
    dify=abs(dy)

    if(difx>dify):
        linestatus="horizontal"

    elif(difx<dify):
        linestatus="vertical"

    else:
        linestatus="unknown"

    return linestatus


#get the nearest line of a point p among two line l1 , l2 given line status [horizontal/vertical]
def getNearestLine(p,l1,l2,linestatus):

    px=p[0]
    py=p[1]


    if "horizontal" in linestatus:

        l1x=getXGivenY(l1,py)[0]
        l2x=getXGivenY(l2,py)[0]

        difl1x=int(abs(l1x-px))
        difl2x=int(abs(l2x-px))

        if difl1x > difl2x :
            nearestline="line2"
        elif difl2x > difl1x :
            nearestline="line1"
        else:
            nearestline="both"

        return nearestline
    
    elif "vertical" in linestatus:
        
        l1y=getYGivenX(l1,px)[1]
        l2y=getYGivenX(l2,px)[1]

        difl1y=int(abs(l1y-py))
        difl2y=int(abs(l2y-py))

        if difl1y > difl2y :
            nearestline="line2"
        elif difl2y > difl1y :
            nearestline="line1"
        else:
            nearestline="both"

        return nearestline
    
    else:
        return -1




def getWayStatus(wayline,box,boxstatus,linestatus):

    l1=box[0]
    l2=box[1]

    outpoint=wayline[0]
    inpoint=wayline[1]

    outline=getNearestLine(outpoint,l1,l2,linestatus)
    inline=getNearestLine(inpoint,l1,l2,linestatus)

    if "line1" in outline:
        
        wayoutline=l1.copy()
        wayinline=l2.copy()
    elif "line2" in outline :
        wayoutline=l2.copy()
        wayinline=l1.copy()
    else:
        return -1,-1,-1,-1,-1,-1

    if "horizontal" in boxstatus:
        
        if "line2" in outline:
            
            wayout = "+"
            wayin="-"
        elif "line1" in outline:
            
            wayout="-"
            wayin="+"
            
        else:
            
            return -1,-1,-1,-1,-1,-1
    elif "vertical" in boxstatus:

        if "line2" in outline:

            wayout="+"
            wayin="-"

        elif "line1" in outline:

            wayout="-"
            wayin="+"

        else:

            return -1,-1,-1,-1,-1,-1


    else :

        return -1,-1,-1,-1,-1,-1


    return (wayin,inline,wayinline,wayout,outline,wayoutline)


        
    


        
#==================================================================================================
# function to write data into a CSV
# This function be replaced in final version, which shall write into a mongoDB
##def writeData(filename,data):
##    try:
##        print(data)
##        with open(filename,"a") as csv_file:
##            writer = csv.writer(csv_file,delimiter = ',')
##            for line in data:
##                writer.writerow(line)
##            # replace the value of incount, outcount with current values
##            if len(data) != 0 and line[1] != 'incount':
##                inputs.incount = line[1]
##                inputs.outcount = line[2]
##        return True
##    except Exception as e:
##        print("Error occured while writing data to file : ",filename)
##        print(e)
##        return False            


    





#cp=[[256,63],[64,218]]
#bs,b,l1,l2=getBoxPointandStatus(cp)
#img=cv2.imread("/home/ria/WORKS/BUFO/detect_and_count BETA 1.0/tests/resources/i.png")
#cv2.line(img,(l1[0][0],l1[0][1]),(l1[1][0],l1[1][1]),(0,255,0),2)
#cv2.line(img,(l2[0][0],l2[0][1]),(l2[1][0],l2[1][1]),(0,0,255),2)
#cv2.imshow("i",img)
#cv2.waitKey(0)
#cv2.destroyAllWindows()


#if __name__=="__main__":
#    img=cv2.imread("/home/ria/WORKS/BUFO/detect_and_count BETA 1.0/tests/resources/i.png")
#    orig=img.copy()
#    cv2.imshow("i",img)
#    cv2.setMouseCallback("i",onClikDrag)
#   while True:
#
#        cv2.imshow("i",img)
#        s=cv2.waitKey(1) & 0xFF
#        if s== ord('s') and point1!=point2 and point1!=0 and point2 !=0:
#            break
#        if point1!=point2 and point1!=0 and point2 !=0:
#            img=orig.copy()
#            cv2.line(img,point1,point2,(0,0,255),2)
#
#    img=orig.copy()
#    if point1!=point2 and point1!=0 and point2 !=0:
#        bs,b,l1,l2=getBoxPointandStatus(points)
#        cv2.line(img,(l1[0][0],l1[0][1]),(l1[1][0],l1[1][1]),(0,0,255),2)
#        cv2.line(img,(l2[0][0],l2[0][1]),(l2[1][0],l2[1][1]),(0,255,0),2)
#        print(bs)
#        print(l1)
#
#
#   
#    point1=point2=0
#    points=[]
#    orig2=img.copy()
#    cv2.imshow("i",img)
#    print("drag and draw a line from out to in crossing the previously drawn line")

#    while(True):


#        cv2.imshow("i",img)
#        s=cv2.waitKey(1) & 0xFF
#        if s== ord('s') and point1!=point2 and point1!=0 and point2 !=0:
#            break
#        if point1!=point2 and point1!=0 and point2 !=0:
#            img=orig2.copy()
#            cv2.arrowedLine(img,point1,point2,(255,0,0),3)
#
#
#    if point1!=point2 and point1!=0 and point2 !=0:
#        wayline=[points[0],points[1]]
#        ls=getLineStatus(wayline)
#        wayin,inline,wayinline,wayout,outline,wayoutline=getWayStatus(wayline,b,bs,ls)
#
#        print("=================================================================")
#        print("way in ",wayin)
#        print("wayinline",wayinline)
#        print("wayout",wayout)
#        print("wayoutline",wayoutline)
#        print("=================================================================")
#
#
#
#    s=cv2.waitKey(0) & 0xFF
#    cv2.destroyAllWindows()
    
                 
