import cv2
import requests
import numpy as np
import imutils
from datetime import datetime
import os
import time
import subprocess

'''
this artikel form
https://www.it-swarm.dev/id/python/bagaimana-cara-mem-parse-mjpeg-http-stream-dari-ip-camera/1045420897/
'''

while True:
    #request image from website
    r = requests.get('http://192.168.100.100/', auth=('user', 'password'), stream=True)

    #if status complete
    if(r.status_code == 200):
        #declaration
        bytes = bytes()
        firstFrame = None
        frameCount = 0
        imageCountInFolder = 0
        strTimeNow = 00
        pathToFile = ""
        emptyframe = 0
        #frame by frame
        for chunk in r.iter_content(chunk_size=1024):
            try:
                
                bytes += chunk
                #find text from bytes
                #first bytes
                a = bytes.find(b'\xff\xd8')
                #end bytes
                b = bytes.find(b'\xff\xd9')
                
                #if start and end bytes is found
                if a != -1 and b != -1:
                    jpg = bytes[a:b+2]
                    bytes = bytes[b+2:]
                    
                    #initiation cv
                    #decode image
                    i = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    frame = imutils.resize(i, width=720)
                    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray,(21,21),0)
                    
                    if firstFrame is None:
                        firstFrame = gray
                        continue
                    
                    frameDelta = cv2.absdiff(firstFrame, gray)
                    thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
                    
                    thresh = cv2.dilate(thresh, None, iterations=2)
                    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE)
                    cnts = imutils.grab_contours(cnts)
                    for c in cnts:
                        if frameCount == 30:
                            firstFrame = None
                            frameCount = 0
                        # if the contour is too small, ignore it
                        if cv2.contourArea(c) < 700:
                            continue
                        # compute the bounding box for the contour, draw it on the frame,
                        # and update the text
                        
                        (x, y, w, h) = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        text = "Object Detected"
                        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                        cv2.putText(frame, datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
                            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)    
                        if(strTimeNow != datetime.now().strftime("%M")):
                            
                            if(pathToFile != "") and (imageCountInFolder > 10):
                                bashCMD = ["ffmpeg","-r","5","-i",pathToFile+"/image-%00d.jpg","-vcodec","libx264","-y","-an","/home/pi/videosCapture/videos-"+datetime.now().strftime("%Y-%m-%d %H:%M")+".mp4"]
                                process = subprocess.Popen(bashCMD, stdout=subprocess.PIPE)
                                output,error = process.communicate()
                                print(output);
                            imageCountInFolder = 0 
                        minutenow = datetime.now().strftime("%M")
                        strTimeNow = minutenow
                        hournow = datetime.now().strftime("%H")
                        timenow = datetime.now().strftime("%H:%M:%S-%f")
                        imageCountInFolder+=1
                        datenow = datetime.now().strftime("%Y-%m-%d")
                        pathToFile = os.path.expanduser('~/captured') + "/" + datenow + "/" + hournow + "/" + minutenow
                        os.makedirs(pathToFile, exist_ok=True)
                        cv2.imwrite(pathToFile + "/image-"+ str(imageCountInFolder) + ".jpg", frame)
                                        
                        frameCount = frameCount+1
                  
                    

                    cv2.imshow('Video', frame)
                    #cv2.imshow('Diff',frameDelta)
                    
                    if cv2.waitKey(1) == 27:
                        exit(0)
            except:
                emptyframe += 1
                print("Error NEXT FRAME"+str(emptyframe))
                time.sleep(1)
    else:
        print("Received unexpected status code {}".format(r.status_code))
        time.sleep(10)
