# Program interfaces the machine vision library with other applications like web
# On executing, it hosts a server on localhost, creating an operational interface for the user

import sys
import argparse
import json
from pymongo import MongoClient
import multiprocessing
import lib.dwelltimer as visioner
import lib.counter as counter
from wsgiref.simple_server import make_server
import cgi

def prepareFromConfig():
    try:
        # parse configuration details from database 'bufo' under collection 'configuration'
        print("Trying to read configuration from database")
        host = 'localhost'
        db_name = 'bufo'

        client = MongoClient(host,27017)                # set up Mongo client
        db = client[db_name]                                # select database
        conf_collection = db['configuration']           # select collection for configuration
        print("Connected to database successfully. Fetching configuration details")
        dwell_segments = []
        count_segments = []
        parameters = []
        output = 'output.json'

        for camera in conf_collection.find():
            ip_stream = camera['stream']
            for modes in camera["operation_mode"]:
                if modes["name"] == "dwell":
                    # if operation mode is dwell time counter
                    width = modes['configuration']['width']
                    for seg in modes['configuration']['segments']:
                        seg['width'] = width
                        dwell_segments.append(seg)                    # segment configuration
                elif modes['name'] == "count":
                            # if operation mode is dwell time counter
                            width = modes['configuration']['width']
                            for seg in modes['configuration']['segments']:
                                seg['width'] = width
                                count_segments.append(seg)                    # segment configuration

            if len(dwell_segments) > 0:
                # [mode, videostream,[{configuration}],bool livestream, bool novideo, int starttime, int frameskip, int flushtime, output, bool debug]
                parameters.extend(([['dwell',ip_stream,dwell_segments,True,True,None,None,1000,output,False]]))
                dwell_segments = []
            if len(count_segments) > 0:
                # [mode, videostream,[{configuration}],bool livestream, int frameskip, int flushtime, int starttime, bool novideo, bool debug]
                parameters.extend(([['count',ip_stream,count_segments,True,0,0,0,True,False]]))
                count_segments = []

        print("Configuration loaded successfully")
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


def start():
    try:
        # check if program is already running
        if len(multiprocessing.active_children()) is not 0:
            print("System already running. Try python app.py --terminate to halt the system and restart with --begin")
            return "fail","system already running"
        param_input = prepareFromConfig()      # get parameters from Config file

        # brew multiprocessing processes to run dwelltimer function in multiple core simultaneously
        for param in param_input:
            if param[0] == 'dwell':
                param.pop(0)
                p = multiprocessing.Process(name="visioner_dwell",target=visioner.calcDwellTime, args=([param]))
                p.daemon = True
                p.start()
                print("Running dwell timer operation on ", param[0], " with process ID ", p.pid)
            elif param[0] == 'count':
                param.pop(0)
                p = multiprocessing.Process(name="visioner_count",target=counter.CountPeople, args=([param]))
                p.daemon = True
                p.start()
                print("Running counter operation on ", param[0], "with process ID ", p.pid)

        print("Number of processes running : ", len(multiprocessing.active_children()))
        print("System running in background (daemon mode)... \nTry app.py --terminate to halt the system")
        return "success","system started successfully"
    except Exception as e:
        print("fatal ERROR in CommandInputInput() : ")
        print("Error Name : ",e)
        print("Error in details : ")
        err=sys.exc_info()
        print("Error Type : ",err[0])
        print("file name : ",err[-1].tb_frame.f_code.co_filename)
        print("Line Number : ",err[-1].tb_lineno)
        return -1


def stop():
    try:
        # check if program is already running
        if len(multiprocessing.active_children()) is not 0:
            print("Terminating the system.")
            return "success","system terminated successfully"
        else:
            print("System already running.")
            return "fail","system already running"
    except Exception as e:
        print("fatal ERROR in stop() : ")
        print("Error Name : ",e)
        print("Error in details : ")
        err=sys.exc_info()
        print("Error Type : ",err[0])
        print("file name : ",err[-1].tb_frame.f_code.co_filename)
        print("Line Number : ",err[-1].tb_lineno)
        return -1

# ==================== Web Service ===========================

# WSGI to interface with web template
def app(environ, start_response):
    content = ""

    if environ['REQUEST_METHOD'] == 'POST':
        post_env = environ.copy()
        post_env['QUERY_STRING'] = ''
        post = cgi.FieldStorage(
            fp=environ['wsgi.input'],
            environ=post_env,
            keep_blank_values=True
        )
        response = {}
        if 'action' in post:
            if post['action'].value == 'begin':
                # start the system
                status, status_text = start()
                response['status'] = status
                response['status_text'] = status_text
            elif post['action'].value == 'terminate':
                status, status_text = stop()
                response['status'] = status
                response['status_text'] = status_text
            else:
                response['status'] = 'fail'
                response['status_text'] = 'invalid request'


            content = [(json.dumps(response)).encode("utf-8")]

        else:
            content = [(json.dumps("{'status_text':'invalid input'}")).encode("utf-8")]
    start_response('200 OK', [('Content-Type', 'text/plain'),('Access-Control-Allow-Origin','*')])
    return content


# ====================== Command Line Interface ================================
#use this function to input parameters from CLI
def CommandLineInput():
    parser = argparse.ArgumentParser()
    # parser.add_argument("-w","--web",action="store_true",default=False, help="use this to enable web interface")
    parser.add_argument("-b","--begin",action="store_true",default=False, help="use this to begin")
    parser.add_argument("-t","--terminate",action="store_true",default=False, help="use this to terminate")

    try:
        isWeb = True
        args=parser.parse_args()
        return isWeb,args.begin,args.terminate

    except Exception as e:
        print("fatal ERROR in CommandInputInput() : ")
        print("Error Name : ",e)
        print("Error in details : ")
        err=sys.exc_info()
        print("Error Type : ",err[0])
        print("file name : ",err[-1].tb_frame.f_code.co_filename)
        print("Line Number : ",err[-1].tb_lineno)
        return -1



if __name__ == '__main__':
    options = {}
    try:
        isWeb, begin, terminate = CommandLineInput()
        if begin and not terminate:
            start()
        elif terminate and not begin:
            stop()
        else:
            print('Invalid request recieved from command line interface. Try again')

        if isWeb:
            httpd = make_server('localhost', 8080, app)
            print('Launching server on port 8080...')
            httpd.serve_forever()


    except KeyboardInterrupt:
        # Shut down the system
        # close the
        print('Shutting down the server. Goodbye!')