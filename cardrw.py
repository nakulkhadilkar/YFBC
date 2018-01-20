#!/usr/bin/env python
# Read member tags or add information to tag
# Stop at one valid read/write

import RPi.GPIO as GPIO
import SimpleMFRC522

reader = SimpleMFRC522.SimpleMFRC522()

def readCard():
    id, text = reader.read()
    if id != []:
        print('Card Detected with ID = ',id,' with information - ',text)
        return True,text

def writeToCard():
    text = input('Enter information to be written:')
    print("Now scan a tag to write")
    id, text = reader.write(text) 
    print("written")            

def validate(data):
        import os,csv,time
        # Change directory to where the data file will live
        os.chdir('/home/pi/HomeProject/YFBC/')
        with open('YFBCMemberinfo.csv','r') as csvfile:
            rd = csv.reader(csvfile,delimiter=',')
            dataInCSV = list(rd)
            uidColumn = [i[len(dataInCSV[0])-1] for i in dataInCSV]
        print(len(uidColumn[2]))
        print(len(data))
        return uidColumn.count(data[0:8])
# Routine
if __name__ == '__main__':
    try:
        while True:
            operation = input('Read or write (press r or w):')
            if operation == 'r':
                print('Waiting for tag...');
                cardDetected = False
                while (cardDetected == False):
                    cardDetected,uid = readCard()
                    cardDetected = True
                    print(validate(str(uid)))
            elif operation == 'w':
                writeToCard()

    except KeyboardInterrupt:
        print("cleaning up")
        GPIO.cleanup()
