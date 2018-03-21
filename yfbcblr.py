#!/usr/bin/env python3
''' Python script to run the Graphical User Interface for member entry and payment tracking
at Yellow Feathers Badminton Club, Bengaluru '''
# Copyrights : Nakul Khadilkar, Vinod Khadilkar 2018
# Update - March 21 2018

import tkinter as tk
import time

class yfbcblr():
    # Note: A tkinter 'frame' is referred to as a screen throughtout this code
    def __init__(self):
        import calendar
        self.d,self.m,self.y = [list(range(1,32)),calendar.month_name[1:13],list(range(2017,2022,1))]
        self.csvFileLocation = '/home/pi/HomeProject/YFBC/
        self.startScreen(False) 
        
    def createDataFiles(self):
        import os
        print('creating directories')

        # create directory only if necessary
        if not(os.path.exists(self.csvFileLocation)):
            os.makedirs(self.csvFileLocation)
            # add rw permission to this owner
            command = 'chmod u+rw' + ' '+ self.csvFileLocation
            os.system(command);

            
        self.CSVOperation(['FirstName','LastName','Email','ContactNumber','MembershipType','UniqueCardID'], \
                          'YFBCMemberinfo.csv','write','w')
        self.CSVOperation(['UniqueCardID','Date','Time'],'YFBCEventLogs.csv','write','w')
        self.CSVOperation(['UniqueCardID','PaymentFor','PaymentDate'],'YFBCMemberPaymentData.csv','write','w')
        
    # Make window not resizable
    def setNotResizable(self,window):
        window.resizable(width=False, height=False)

    def removeScreen(self,screen):
        screen.place_forget()
        # reset main screen title
        self.rootWindow.title('Login Portal')
        
    def backToHomeScreen(self,prevFrame,delay,resetCardDetectionFlag):

        # Update members list on main screen
        self.loggedMembersFrame.destroy()
        self.createFrameAndAddLoggedMembers()
        self.monthlyMembersPayFrame.destroy()
        self.createFrameAndAddMonthlyMembers()

        time.sleep(delay)
        prevFrame.destroy()
        self.rootWindow.update()

        if(resetCardDetectionFlag == True):
            # reset the card detection flag
            self.cardDetected = False
        else:
            # call the card detection loop to trigger detection 
            self.detectRFIDCard()
        
    def deleteDir(self):
        result = tk.messagebox.askquestion('Delete files before quitting','Are you debugging? Delete data files?')
        import RPi.GPIO as GPIO
        if result == 'yes':
            import os
            command = 'rm -rf ' + self.csvFileLocation 
            os.system(command)

        GPIO.cleanup()
        self.rootWindow.destroy()

    def getRelativeSize(self,valueToConvert,dimension):
        # Convert the constant sizes to something that will work on a smaller screen too
        w,h = [1920,1008]
        if dimension == 'width':
            return int((valueToConvert * w)/w)
        elif dimension == 'height':
            return int((valueToConvert * h)/h)
        elif dimension == 'area':
            return int((valueToConvert * self.screenPixels)/1935360)
    
    # The first screen with options to login as admin or other user
    def startScreen(self,wantToolBar):
        import os
        if not(os.path.exists(self.csvFileLocation + 'YFBCMemberinfo.csv')) \
           or not(os.path.exists(self.csvFileLocation + 'YFBCEventLogs.csv')) \
           or not(os.path.exists(self.csvFileLocation + 'YFBCMemberPaymentData.csv')):
            self.createDataFiles()

        # Title, Club name and screen mode
        self.rootWindow = tk.Tk()
        self.rootWindow.title('Login Portal')
        self.rootWindow.configure(bg='lightblue')
        self.rootWindow.attributes('-fullscreen',not(wantToolBar),'-zoomed',True)
        self.mainScreen = tk.Frame(self.rootWindow).place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
        self.rootWindow.update()
        self.screenPixels = self.rootWindow.winfo_width() * self.rootWindow.winfo_height()
        self.memTypes = ['Monthly','Gold','Platinum', 'Guest']

        # Callback to debug or not : close button
        self.rootWindow.protocol('WM_DELETE_WINDOW',self.deleteDir)
        clubName = tk.Label(self.mainScreen, text='Yellow Feathers Badminton Club, Bengaluru 560110',bg='lightblue',font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.5, rely=0.05,anchor='center')

        # Add today's logged member lists to main screen on the right
        self.createFrameAndAddLoggedMembers()
        
        # Add list of monthly members to the main screen on the left
        self.createFrameAndAddMonthlyMembers()
        
        # Setup label, buttons
        waitLabel = tk.Label(self.mainScreen, text='Scan your tag to check-in.',bg='lightblue',width=self.getRelativeSize(40,'width'), \
                             font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.5, rely=0.9, anchor='center')

        # Force root window update 
        self.rootWindow.update()

    def writeEventLogsAfterCardDetection(self,uid):
        data = [uid, time.strftime('%d%b%Y'), time.strftime('%H:%M:%S')]
        memberData = self.memberDetails(uid,'read',[],[])

        # Do not write if the member has logged in once already in the last 4 hours
        if not(self.validate(data[0:2],'checkin')):
            # write to log file
            self.CSVOperation(data,'YFBCEventLogs.csv','write','a')
            
            # check that the entry is correct
            latestEntry = self.CSVOperation([],'YFBCEventLogs.csv','lastrow',[])
            if latestEntry == list(data):
                welcomeMessage = 'Hi '+memberData[0]+' '+memberData[1]+',\n Welcome to YFBC.\n  Have a great game.'
            else:
                welcomeMessage = 'Hi '+memberData[0]+' '+memberData[1]+',\n Welcome to YFBC.\n  Your card was detected, but entry was not logged. Please re-scan your card.'
        else:
            welcomeMessage = 'Hi '+memberData[0]+' '+memberData[1]+',\n You already logged in today.\n  Have a great game.'

        # Temporary frame to indicate successful check-in
        tempFrame = tk.Frame(self.rootWindow,takefocus=1)
        tempFrame.place(relx=0.5, rely=0.5, relheight=0.5,relwidth=0.5,anchor='center')
        tk.Message(tempFrame,text=welcomeMessage,bg='lightgreen',justify='center', font=("Bookman Old Style",20), \
                   ).place(relx=0.5, rely=0.5, relheight=1, relwidth=1,anchor='center')
        self.rootWindow.update()

        self.backToHomeScreen(tempFrame,5,True)

    def createFrameAndAddLoggedMembers(self):
        self.loggedMembersFrame = tk.Frame(self.mainScreen, bg='white')
        self.loggedMembersFrame.place(relx=0.98, rely=0.475, relheight=0.75, relwidth=0.475, anchor='e')
        tk.Label(self.loggedMembersFrame, text='Logged-in Members',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0, rely=0, relheight=0.05, relwidth=1, anchor='nw')
        tk.Label(self.loggedMembersFrame, text='Member Name',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0, rely=0.05, relheight=0.05, relwidth=1/2, anchor='nw')
        tk.Label(self.loggedMembersFrame, text='Login Time',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0.5, rely=0.05, relheight=0.05, relwidth=1/2, anchor='nw')
        self.addMemberDataToList(self.loggedMembersFrame,'logged')

    def createFrameAndAddMonthlyMembers(self):
        self.monthlyMembersPayFrame = tk.Frame(self.mainScreen, bg='white')
        self.monthlyMembersPayFrame.place(relx=0.02, rely=0.475, relheight=0.75, relwidth=0.475, anchor='w')
        tk.Label(self.monthlyMembersPayFrame, text=' Active Monthly Members',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0, rely=0, relheight=0.05, relwidth=1, anchor='nw')
        tk.Label(self.monthlyMembersPayFrame, text='Column 1',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0, rely=0.05, relheight=0.05, relwidth=1/2, anchor='nw')
        tk.Label(self.monthlyMembersPayFrame, text='Column 2',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0.5, rely=0.05, relheight=0.05, relwidth=1/2, anchor='nw')
        self.addMemberDataToList(self.monthlyMembersPayFrame,'monthly')
        
    def addMemberDataToList(self,frame,listType):
        import os,csv
        os.chdir(self.csvFileLocation)
        
        # logged member query
        if listType == 'logged':
            loggedMemberIDs = list()

            # get all unique card ID's from member list
            IDList = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberinfo.csv')
            IDList = [item[-1] for item in IDList]
            IDList.pop(0)

            with open('YFBCEventLogs.csv','r') as csvfile:
                rd = csv.reader(csvfile,delimiter=',')
                for row in rd:
                    # Add entries in the last four hours
                    if (time.strftime('%d%b%Y') in row) and not(self.pastFourHours(row[2])) and (row[0] in IDList):
                        loggedMemberIDs.append([row[0],row[2]])

            # make a grid and add to frame
            limit = len(loggedMemberIDs)
            for i in range(limit):
                memberData = self.memberDetails(loggedMemberIDs[i][0],'read',[],[])
                tk.Label(frame, text=(memberData[0]+' '+memberData[1]), bg='white', font=("Bookman Old Style",self.getRelativeSize(15,'area')), \
                         borderwidth=2, relief='groove').place(relx=0, rely=0.1+(i*(0.9/limit)), relheight=(0.9/limit), relwidth=1/2, anchor='nw')
                tk.Label(frame, text=loggedMemberIDs[i][1], bg='white', font=("Bookman Old Style",self.getRelativeSize(15,'area')), \
                         borderwidth=2, relief='groove').place(relx=0.5, rely=0.1+(i*(0.9/limit)), relheight=(0.9/limit), relwidth=1/2, anchor='nw')

        # monthly member query
        elif listType == 'monthly':
            monthlyMembers = list()
            activeMembers = list()
            with open('YFBCMemberinfo.csv','r') as csvfile:
                rd = csv.reader(csvfile,delimiter=',')
                for row in rd:
                    if 'Monthly' in row:
                        monthlyMembers.append(row[0]+' '+row[1])
            monthlyMembers.sort()
            # make a grid with active members and add to frame
            limit = len(monthlyMembers)
            for i in range(limit):
                # get payment details for member
                userCardID = self.getUserIDfromName(monthlyMembers[i])
                with open('YFBCMemberPaymentData.csv','r') as csvfile:
                    rd = csv.reader(csvfile,delimiter=',')
                    for row in rd:
                        if (userCardID in row[0]) and str(time.strftime('%B') in row[1]) and not(monthlyMembers[i] in activeMembers):
                            activeMembers.append(monthlyMembers[i])
            for n in range(len(activeMembers)):
                ypos = int(((n-1)%2)+((n-1)/2)) # need a series that goes like [0,0,1,1,2,2.....]
                tk.Label(frame, text=activeMembers[n], bg='white', font=("Bookman Old Style",self.getRelativeSize(10,'area')), \
                         borderwidth=2, relief='groove').place(relx=(n%2)*0.5, rely=0.1+(ypos*(0.9/limit)), relheight=(0.9/limit), relwidth=1/2, anchor='nw')
            
    def memberScreen(self,forAdmin,adminView):
        # member check-in screen
        userScreen = tk.Frame(self.rootWindow,bg='lightgreen')
        userScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
        clubName = tk.Label(userScreen, text='Yellow Feathers Badminton Club, Bengaluru 560110',bg='lightgreen',font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.5, rely=0.1,anchor='center')
        self.rootWindow.title('Member Portal')
        
        if not(forAdmin):
            validTag = False
            waitLabel = tk.Label(userScreen, text='Scan your tag to check-in.',bg='lightgreen',width=self.getRelativeSize(40,'width'), \
                                     font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.5, rely=0.5, anchor='center')
            
            # Back button
            backButton = tk.Button(userScreen, text='Back to Main Screen', width=self.getRelativeSize(30,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                   command=lambda: self.removeScreen(userScreen)).place(relx=0.5, rely=0.9, anchor='center')
            
        else:
            userid = tk.StringVar(None)
            allUsers = self.getAllUserNames()
            if allUsers == [] and adminView in ['view','edit','delete']:
                tk.messagebox.showinfo(parent=self.rootWindow,message='No members added yet. Please add one to get started.',title='Input Error')
            else:
                textLabel = tk.Label(userScreen, text='Select member :',bg='lightgreen',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.20, rely=0.4, anchor='center')
                selection = tk.Listbox(userScreen, width=self.getRelativeSize(40,'width'), height=self.getRelativeSize(8,'height'), font=("Bookman Old Style",self.getRelativeSize(20,'area')))
                selection.place(relx=0.6, rely=0.45, anchor='center')
                for names in allUsers:
                    selection.insert(tk.END,names)
                scrollbar = tk.Scrollbar(selection,orient=tk.VERTICAL, command=selection.yview)
                scrollbar.place(relx=1,rely=0.5,relheight=1,anchor='e')
                selection.config(yscrollcommand=scrollbar.set)
                selection.selection_set(0)
                memStatusButton = tk.Button(userScreen, text='View Membership Details And Payment History', font=("Bookman Old Style",self.getRelativeSize(20,'area')), width=self.getRelativeSize(40,'width'), \
                                            command=lambda: self.membershipDetailsScreen(self.getUserIDfromName(selection.selection_get()),True,userScreen,True,adminView), fg='black').place(relx=0.6, rely=0.7, anchor='center')

            # Back button
            backButton = tk.Button(userScreen, text='Back to Main Screen', width=self.getRelativeSize(30,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                   command=lambda: self.removeScreen(userScreen)).place(relx=0.5, rely=0.9, anchor='center')

    def getUserIDfromName(self,uid):
        if not(uid == []):
            fName,lName = str.split(uid,' ')
            rowData = self.memberDetails([fName,lName],'read',[],[])
            return rowData[len(rowData)-1]
        else:
            tk.messagebox.showerror(parent=self.rootWindow,message='Please select a user.',title='Input Error')
                
    def membershipDetailsScreen(self,uid,splitString,screenToDeleteAfter,forAdmin,adminMode):
        # Membership details screen
        if not(self.validate(uid,'userid')):
            tk.messagebox.showerror(parent=self.rootWindow,message='Invalid user ID specified. Please try again.',title='Input Error')
            
        else:
            if not(forAdmin):
                # Create a new screen
                self.removeScreen(screenToDeleteAfter)
                memberInfoScreen = tk.Frame(self.rootWindow)
                memberInfoScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
                self.rootWindow.title('Member Information')
                memberInfoScreen.configure(bg='lightblue')
                details = self.memberDetails(uid,'read',[],[])

                # Create entry boxes
                mdata = ['First Name :','Last Name :','Email ID :','Contact No : +91','Membership Type :']
                stringsToDisplay = ["%s %s" % t for t in zip(mdata, details)]
                
                if splitString == True:
                    for i in range(0,len(mdata)):
                        exec('textLabel%d = tk.Label(memberInfoScreen, text=mdata[%d], font=(%s,self.getRelativeSize(25,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightblue'),i,repr('w')))
                        exec('value%d = tk.Label(memberInfoScreen, text=details[%d], bg=%s, fg=%s,font=(%s,self.getRelativeSize(25,%s))).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr('white'),repr('darkred'),repr("Bookman Old Style"),repr('area'),i,repr('e')))
                elif splitString == False:
                    for i in range(0,len(mdata)):
                        exec('textLabel%d = tk.Label(memberInfoScreen, text=stringsToDisplay[%d], font=(%s,self.getRelativeSize(25,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightblue'),i,repr('w')))

            else:
                # Create a new screen
                self.removeScreen(screenToDeleteAfter)
                memberInfoScreen = tk.Frame(self.rootWindow)
                memberInfoScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
                self.rootWindow.title('Member Information')
                memberInfoScreen.configure(bg='lightblue')
                details = self.memberDetails(uid,'read',[],[])
                mdata = ['First Name :','Last Name :','Email ID :','Contact No : +91','Membership Type :']
                if adminMode == 'view':
                    for i in range(0,len(mdata)):
                        exec('textLabel%d = tk.Label(memberInfoScreen, text=mdata[%d], font=(%s,self.getRelativeSize(25,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightblue'),i,repr('w')))
                        exec('value%d = tk.Label(memberInfoScreen, text=details[%d], bg=%s, fg=%s,font=(%s,self.getRelativeSize(25,%s))).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr('white'),repr('darkred'),repr("Bookman Old Style"),repr('area'),i,repr('e')))
                    
                if adminMode == 'edit':
                    info = [tk.StringVar(None,value=details[0]),tk.StringVar(None,value=details[1]),tk.StringVar(None,value=details[2]), \
                            tk.StringVar(None,value=details[3]),tk.StringVar(None)]
                    info[4].set(details[4])
                    for i in range(0,len(mdata)):
                        exec('textLabel%d = tk.Label(memberInfoScreen, text=mdata[%d], font=(%s,self.getRelativeSize(20,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightblue'),i,repr('w')))
                        if i!= 4:
                            exec('value%d = tk.Entry(memberInfoScreen, textvariable=info[%d], bg=%s, fg=%s,font=(%s,self.getRelativeSize(20,%s))).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr('white'),repr('darkred'),repr("Bookman Old Style"),repr('area'),i,repr('e')))
                        else:
                            exec('entry%d = tk.OptionMenu(memberInfoScreen, info[%d],*self.memTypes).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,i,repr('center')))
                    tk.Button(memberInfoScreen, text='Update Member Details', width=self.getRelativeSize(25,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                       command=lambda: self.memberDetails(uid,'replace',info,memberInfoScreen)).place(relx=0.3, rely=0.85, anchor='center')

                if adminMode == 'delete':
                    for i in range(0,len(mdata)):
                        exec('textLabel%d = tk.Label(memberInfoScreen, text=mdata[%d], font=(%s,self.getRelativeSize(25,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightblue'),i,repr('w')))
                        exec('value%d = tk.Label(memberInfoScreen, text=details[%d], bg=%s, fg=%s,font=(%s,self.getRelativeSize(25,%s))).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr('white'),repr('darkred'),repr("Bookman Old Style"),repr('area'),i,repr('e')))
                    tk.Button(memberInfoScreen, text='Delete Member', width=self.getRelativeSize(15,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                       command=lambda: self.memberDetails(uid,adminMode,[],memberInfoScreen)).place(relx=0.5, rely=0.875, anchor='center')
                uidText = 'CardID : ' + details[5]
                userIDLabel = tk.Label(memberInfoScreen, text=uidText,bg='lightblue',fg='darkred',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(20,'area'))).place(relx=0.90, rely=0.1, anchor='ne')   

            # Payment status frame
            tk.Label(memberInfoScreen, text='Payment History',bg='lightblue',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(relx=0.60, rely=0.05, anchor='nw')
            paymentDetailsFrame = tk.Frame(memberInfoScreen,bg='white')
            paymentDetailsFrame.place(relx=0.75,rely=0.5,relheight=0.7,relwidth=0.45,anchor='center')
            self.addPaymentHistoryToFrame(uid,paymentDetailsFrame)

            # Back button
            backButton = tk.Button(memberInfoScreen, text='Back to Main Screen', width=self.getRelativeSize(30,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                       command=lambda: self.removeScreen(memberInfoScreen)).place(relx=0.5, rely=0.95, anchor='center')


    def addPaymentHistoryToFrame(self,uid,frame):
        # Collect payment history and show it on the frame
        payments = self.CSVOperation(uid,'YFBCMemberPaymentData.csv','read',[])

        # Get last 5 payment records for the user
        import os,csv,re
        os.chdir(self.csvFileLocation)
        matchedRows = []
        with open('YFBCMemberPaymentData.csv','r') as csvfile:
            rd = csv.reader(csvfile,delimiter=',')
            for row in rd:
                if uid in row:
                    matchedRows.append(row)
        lastFivePayments = matchedRows[-5:]
        tk.Label(frame, text='Month(s) Paid For',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0, rely=0, relheight=1/7, relwidth=1/2, anchor='nw')
        tk.Label(frame, text='Payment Date',font=("Bookman Old Style",self.getRelativeSize(20,'area')), borderwidth=2, relief='groove').place(relx=0.5, rely=0, relheight=1/7, relwidth=1/2, anchor='nw')
        for e in range(0,len(lastFivePayments)):
            tk.Label(frame, text="\n".join(re.findall("(?s).{,25}", lastFivePayments[e][1].replace('-',', ').replace(':',' of ')))[:-1],font=("Bookman Old Style",self.getRelativeSize(15,'area')), bg='white',borderwidth=2, relief='groove').place(relx=0, rely=(e+1)*(1/7), relheight=1/7, relwidth=1/2, anchor='nw')
            tk.Label(frame, text=lastFivePayments[e][2],font=("Bookman Old Style",self.getRelativeSize(15,'area')), bg='white',borderwidth=2, relief='groove').place(relx=0.5, rely=(e+1)*(1/7), relheight=1/7, relwidth=1/2, anchor='nw')
        if any(time.strftime('%B') in row[1] for row in lastFivePayments) and any(time.strftime('%Y') in row[1] for row in lastFivePayments):
            tk.Label(frame, text='Note: ' + time.strftime('%B') + ' membership fees are paid.',font=("Bookman Old Style",self.getRelativeSize(20,'area')), bg='white', fg='blue', relief='groove').place(relx=0, rely=6/7, relheight=1/7, relwidth=1, anchor='nw')
        else:
            tk.Label(frame, text='Note: ' + time.strftime('%B') + ' membership fees are due.',font=("Bookman Old Style",self.getRelativeSize(20,'area')), bg='white', fg='red', relief='groove').place(relx=0, rely=6/7, relheight=1/7, relwidth=1, anchor='nw')
            
        
    def memberDetails(self,uid,action,newData,screenToDelete):
        import os,csv
        # Change directory to where the data file will live
        os.chdir(self.csvFileLocation)
        matchedRow = []
        with open('YFBCMemberinfo.csv','r') as csvfile:
            rd = csv.reader(csvfile,delimiter=',')
            if not(len(uid) == 2):
                for row in rd:
                    if uid in row:
                        matchedRow = row
                        break
            else:
                for row in rd:
                    if (uid[0] in row) and (uid[1] in row):
                        matchedRow = row
                        break
        
        if action == 'read':
            return matchedRow
        elif action == 'replace':

            oldData = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberinfo.csv')
            
            # matchedRow is the one to be updated
            if not(self.validate(newData,'memberDetails')):
                tk.messagebox.showerror(parent=self.rootWindow,message='The data entered is invalid. Please reenter member details',title='Input Error')
            else:
                if not(oldData[oldData.index(matchedRow)][0:len(oldData[oldData.index(matchedRow)])-1] == [newData[0].get(),newData[1].get(),newData[2].get(),newData[3].get(),newData[4].get()]):
                    oldData[oldData.index(matchedRow)][0:len(oldData[oldData.index(matchedRow)])-1] = [newData[0].get(),newData[1].get(),newData[2].get(),newData[3].get(),newData[4].get()]
                    # Write data to the csv file
                    with open('YFBCMemberinfo.csv', 'w') as csvfile:
                        wrt = csv.writer(csvfile,delimiter=',')
                        for row in oldData:
                            wrt.writerow(row[0:len(row)])
                    tk.messagebox.showinfo(parent=self.rootWindow,message='Member details have been saved. An email has been sent for future reference.')
                    self.removeScreen(screenToDelete)
                else:
                    tk.messagebox.showinfo(parent=self.rootWindow,message='No changes made to member details. Update not needed.')
                    self.removeScreen(screenToDelete)
        elif action == 'delete':
            oldData = []

            # Read all data from the csv file.
            oldData = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberinfo.csv')
            
            # Pop up the row to delete
            oldData.pop(oldData.index(matchedRow))

            # Write to file without that popped row
            with open('YFBCMemberinfo.csv', 'w') as csvfile:
                wrt = csv.writer(csvfile,delimiter=',')
                for row in oldData:
                    wrt.writerow(row[0:len(row)])
            tk.messagebox.showinfo(parent=self.rootWindow,message='Member deleted!')
            self.removeScreen(screenToDelete)

            
    def adminScreen(self):
        admin_pw = tk.simpledialog.askstring("Admin Access","Enter Admin Password : ", show='*')
        if admin_pw == 'test':
            self.admScreen = tk.Frame(self.rootWindow)
            self.admScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
            self.rootWindow.title('Admin Screen')
            action = tk.Label(self.admScreen, text='What would you like to do now?',font=("Bookman Old Style",self.getRelativeSize(40,'area'))).place(relx=0.5, rely=0.1,anchor='center')
            
            # Options for admin to work with
            addNewMember = tk.Button(self.admScreen, text='Add New Member', command=lambda: self.newMemberRegistrationScreen(), \
                                    font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.025, rely=0.4, anchor='w')
            editMember = tk.Button(self.admScreen, text='Edit Member Details', command=lambda: self.memberScreen(True,'edit'), \
                                    font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.35, rely=0.4, anchor='w')
            deleteMember = tk.Button(self.admScreen, text='Delete Member', command=lambda: self.memberScreen(True,'delete'), \
                                    font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.675, rely=0.4, anchor='w')
            viewMember = tk.Button(self.admScreen, text='View Member', command=lambda: self.memberScreen(True,'view'), \
                                    font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.025, rely=0.6, anchor='w')
            dataBaseUpdate = tk.Button(self.admScreen, text='Update Online Database', command=lambda: self.uploadDataFilesToDrive(), \
                                             font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.35, rely=0.6, anchor='w')
            postPayment = tk.Button(self.admScreen, text='Record Member Payment', command=lambda: self.paymentEntryScreen(), \
                                             font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.675, rely=0.6, anchor='w')
            back = tk.Button(self.admScreen, text='Back to Main Screen', command=lambda: self.backToHomeScreen(self.admScreen,0.75,False), \
                             font=("Bookman Old Style",self.getRelativeSize(30,'area'))).place(width=self.getRelativeSize(600,'width'),height=self.getRelativeSize(100,'height'),relx=0.50, rely=0.9, anchor='center')
        else:
            tk.messagebox.showerror(parent=self.rootWindow, \
                                        message='Good luck trying to fake the admin!',title='Input Error')
            self.rootWindow.update()
            # call the card detection loop to trigger detection 
            self.detectRFIDCard()

    def newMemberRegistrationScreen(self):
        # Create a new ui screen at centre of screen for data entry and bring it into focus
        newUserScreen = tk.Frame(self.rootWindow)
        newUserScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
        self.rootWindow.title('New User Registration')
        newUserScreen.configure(bg='lightgreen')
        
        # Create entry boxes
        strings = ['First Name :','Last Name :','Email ID :','Contact No (exclude +91) :','Membership Type :']
        stringData = [tk.StringVar(None),tk.StringVar(None),tk.StringVar(None,value='<empty>'),tk.StringVar(None),tk.StringVar(None)]
            
        for i in range(0,len(strings)):
            exec('textLabel%d = tk.Label(newUserScreen, text=strings[%d], font=(%s,self.getRelativeSize(25,%s)), bg=%s).place(relx=0.05, rely=0.15*(%d+1), anchor=%s)' % (i,i,repr("Bookman Old Style"),repr('area'),repr('lightgreen'),i,repr('w')))
            if i != 4:
                exec('value%d = tk.Entry(newUserScreen, textvariable=stringData[%d]).place(relx=0.6, rely=0.15*(%d+1), relheight=0.04, relwidth=0.2, anchor=%s)' % (i,i,i,repr('e')))
            else:
                exec('entry%d = tk.OptionMenu(newUserScreen, stringData[%d],*self.memTypes).place(relx=0.4, rely=0.15*(%d+1), anchor=%s)' % (i,i,i,repr('center')))

        # Done button
        doneButton = tk.Button(newUserScreen, text='Submit Details and Scan RFID tag to register member', command=lambda: self.saveAndSendMemberDetails(stringData,newUserScreen), \
                               font=('Bookman Old Style',self.getRelativeSize(20,'area'))).place(relx=0.70, rely=0.8, relwidth=0.6, anchor='center')

        # Back button
        backButton = tk.Button(newUserScreen, text='Back to Main Screen', width=self.getRelativeSize(30,'width'), font=('Bookman Old Style',self.getRelativeSize(25,'area')), \
                               command=lambda: self.removeScreen(newUserScreen)).place(relx=0.5, rely=0.9, anchor='center')
        
    def paymentEntryScreen(self):
        if self.getAllUserNames() == []:
            tk.messagebox.showinfo(parent=self.rootWindow,message='No members added yet. Please add one to get started.',title='Input Error')
        else:
            import calendar
            paymentScreen = tk.Frame(self.rootWindow)
            paymentScreen.place(width=self.rootWindow.winfo_width(),height=self.rootWindow.winfo_height())
            self.rootWindow.title('Payment Portal')
            paymentScreen.configure(bg='gray')

            # Member choice
            textLabel = tk.Label(paymentScreen, text='Select member :',bg='gray',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(20,'area'))).place(relx=0.05, rely=0.15, anchor='nw')
            user = tk.Listbox(paymentScreen, width=self.getRelativeSize(40,'width'), height=self.getRelativeSize(8,'height'), font=("Bookman Old Style",self.getRelativeSize(17,'area')), exportselection=0)
            user.place(relx=0.3, rely=0.05, anchor='nw')
            for names in self.getAllUserNames():
                user.insert(tk.END,names)
            scrollbar = tk.Scrollbar(user,orient=tk.VERTICAL, command=user.yview)
            scrollbar.place(relx=1,rely=0.5,relheight=1,anchor='e')
            user.config(yscrollcommand=scrollbar.set)

            # Month choice
            textLabel1 = tk.Label(paymentScreen, text='Select Month :',bg='gray',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(20,'area'))).place(relx=0.05, rely=0.35, anchor='nw')
            month = tk.Listbox(paymentScreen, width=self.getRelativeSize(40,'width'), height=self.getRelativeSize(8,'height'), font=("Bookman Old Style",self.getRelativeSize(17,'area')),selectmode='multiple', exportselection=0)
            month.place(relx=0.3, rely=0.30, anchor='nw')
            for names in calendar.month_name[1:13]:
                month.insert(tk.END,names)
            scrollbar1 = tk.Scrollbar(month,orient=tk.VERTICAL, command=month.yview)
            scrollbar1.place(relx=1,rely=0.5,relheight=1,anchor='e')
            month.config(yscrollcommand=scrollbar1.set)

            # Year choice
            textLabel2 = tk.Label(paymentScreen, text='Select Year :',bg='gray',width=self.getRelativeSize(20,'width'), font=("Bookman Old Style",self.getRelativeSize(20,'area'))).place(relx=0.05, rely=0.60, anchor='nw')
            year = tk.Listbox(paymentScreen, width=self.getRelativeSize(40,'width'), height=self.getRelativeSize(8,'height'), font=("Bookman Old Style",self.getRelativeSize(17,'area')), exportselection=0)
            year.place(relx=0.3, rely=0.60, anchor='nw')
            for names in list(range(2017,2022,1)):
                year.insert(tk.END,names)
            scrollbar2 = tk.Scrollbar(year,orient=tk.VERTICAL, command=year.yview)
            scrollbar2.place(relx=1,rely=0.5,relheight=1,anchor='e')
            year.config(yscrollcommand=scrollbar2.set)

            # Payment Date Details
            pdScreen = tk.Frame(paymentScreen,bg='white')
            pdScreen.place(relx=0.85,rely=0.5,relwidth=0.25,relheight=0.2,anchor='center')
            label = tk.Label(pdScreen, text='Select Payment Date :',font=("Bookman Old Style",self.getRelativeSize(15,'area'))).place(relx=0,rely=0,relheight=0.6,relwidth=1,anchor='nw')
            # drop-down menus for payment date
            defaultValues = [tk.StringVar(),tk.StringVar(),tk.StringVar()]
            defaultValues[0].set('<Date>')
            defaultValues[1].set('<Month>')
            defaultValues[2].set('<Year>')
            dd = tk.OptionMenu(pdScreen, defaultValues[0], *list(range(1,32))).place(relx=0, rely=0.6, relheight=0.4, relwidth=1/3)
            mm = tk.OptionMenu(pdScreen, defaultValues[1], *calendar.month_name[1:13]).place(relx=1/3, rely=0.6, relheight=0.4, relwidth=1/3)
            yyyy = tk.OptionMenu(pdScreen, defaultValues[2], *list(range(2017,2022))).place(relx=2/3, rely=0.6, relheight=0.4, relwidth=1/3)
            
            # Done button
            doneButton = tk.Button(paymentScreen, text='Submit', width=self.getRelativeSize(20,'width'), \
                                   command=lambda: self.recordPayment([user.curselection(),month.curselection(),year.curselection()], \
                                                                      [defaultValues[0].get(),defaultValues[1].get(),defaultValues[2].get()],paymentScreen), \
                                   font=('Bookman Old Style',self.getRelativeSize(20,'area'))).place(relx=0.50, rely=0.85, relheight =0.05,anchor='center')

            # Back button
            backButton = tk.Button(paymentScreen, text='Back to Admin Screen', width=self.getRelativeSize(30,'width'), font=('Bookman Old Style',self.getRelativeSize(20,'area')), \
                                   command=lambda: self.removeScreen(paymentScreen)).place(relx=0.5, rely=0.95, anchor='center')


    def recordPayment(self,entries,payDate,screen):
        import datetime
        if not(all(entries)) or (payDate[0]=='<Date>') or (payDate[1]=='<Month>') or (payDate[2]=='<Year>'):
            # has empty selections
            tk.messagebox.showinfo(parent=self.rootWindow,message='One or more entries have not been selected. Try again!',title='Input Error')
        else:
            today = str(self.d[self.d.index(int(payDate[0]))]) + ' ' + self.m[self.m.index(payDate[1])] + ' ' + str(self.y[self.y.index(int(payDate[2]))])
            if not(self.validate(today,'date')):
                     tk.messagebox.showinfo(parent=self.rootWindow,message='Invalid date entered please retry!',title='Input Error')
            elif datetime.datetime.strptime(today,'%d %B %Y') > datetime.datetime.today():
                # future date
                tk.messagebox.showinfo(parent=self.rootWindow,message='Payment cannot be posted for a future date. Enter a present or a past date!',title='Input Error')
            else:
                # Add a new entry
                members = self.getAllUserNames()
                data = [self.getUserIDfromName(members[entries[0][0]]),entries[1],self.y[entries[2][0]]]
                # no empty selections
                # entries = [<userid>,<'mon1-mon2-mon:year'>]
                import calendar
                months = [calendar.month_name[x+1] for x in list(data[1])]
                monthString = '-'.join(months)+':'+str(data[2])
                dataToWrite = [data[0],monthString,today]

                # Check if payment has already been made
                PaymentData = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberPaymentData.csv')
                PaymentData.pop(0) # remove first line
                PaymentData = [item[:-1] for item in PaymentData] # remove payment date field
                PreviousPayment = False
                for d in PaymentData:
                    # If unique card ID, month, year combination is found in the same line
                    if (d[0] == str(data[0])) and (0 in [d[1].find(i) for i in months]) and (str(data[2]) in d[1]):
                        PreviousPayment = True
                        break                

                # write to file if not already paid
                if PreviousPayment == False:
                    self.CSVOperation(dataToWrite,'YFBCMemberPaymentData.csv','write','a')

                    # validate entry and exit current screen only on success
                    latestEntry = self.CSVOperation([],'YFBCMemberPaymentData.csv','lastrow',[])
                    if latestEntry == list(dataToWrite):
                        # success - convey message and go to admin screen
                        tk.messagebox.showinfo(parent=self.rootWindow,message='Payment successfully posted!')
                        self.monthlyMembersPayFrame.destroy()
                        self.createFrameAndAddMonthlyMembers()
                        self.admScreen.lift()
                        self.removeScreen(screen)
                    else:
                        # failure - Stay on current screen
                        tk.messagebox.showinfo(parent=self.rootWindow,message='Payment could not be posted. Please try again!')
                else:
                    # failure - Stay on current screen
                    tk.messagebox.showinfo(parent=self.rootWindow,message='A payment for the month has already been posted!')

    def setupScrollingListBox(self,parent,data,fontSize,positionData):
        # positionData = [relx,rely,relwidth,relheight]
        lb = tk.Listbox(parent, font=("Bookman Old Style",self.getRelativeSize(fontSize,'area')),exportselection=0)
        lb.place(relx=positionData[0],rely=positionData[1],relwidth=positionData[2],relheight=positionData[3],anchor='nw')
        for d in data:
            lb.insert(tk.END,d)
        scrollBar = tk.Scrollbar(lb,orient=tk.VERTICAL,command=lb.yview)
        scrollBar.place(relx=1,rely=0.5,relheight=1,anchor='e')
        lb.config(yscrollcommand=scrollBar.set)
        return lb

    def getAllUserNames(self):
        import os,csv
        os.chdir(self.csvFileLocation)
        ids = []
        with open('YFBCMemberinfo.csv') as f:
            rd = csv.reader(f, delimiter=',')
            for i in rd:
                ids.append('%s %s' % (i[0],i[1]))
        ids.pop(0)
        ids.sort() # sort alphabetically
        return ids
        
    def saveAndSendMemberDetails(self,data,screen):
        if not(self.validate(data,'memberDetails')):
            tk.messagebox.showerror(parent=self.rootWindow,message='The data entered is invalid. Please reenter member details',title='Input Error')
            # Remains in the member entry screen until correct details are entered
        else:
            # get unique ID from card, ignore other content. Only continue if card has not been assigned
            cardID,_ = self.readCard()
            if not(self.CSVOperation(str(cardID),'YFBCMemberinfo.csv','read',[])):
                fName,lName,email,contactNo,memType = data[0].get(),data[1].get(),data[2].get(),data[3].get(),data[4].get()
                
                # Write member data to file
                self.CSVOperation([fName,lName,email,contactNo,memType,cardID],'YFBCMemberinfo.csv','write','a')
                
                # read last entry and card data
                latestEntry = self.CSVOperation([],'YFBCMemberinfo.csv','lastrow',[])
                
                # Compare with expected
                if latestEntry == list([fName,lName,email,contactNo,memType,str(cardID)]):
                    # success - convey success message and remove screen          
                    if not(email=='<empty>'):
                        tk.messagebox.showinfo(parent=self.rootWindow,message='Member successfully registered! An email has been sent with your details.')
                        self.sendemailToMember([fName,lName,email,contactNo,memType],'YFBC Member Registration')
                    else:
                        tk.messagebox.showinfo(parent=self.rootWindow,message='Member successfully registered! No email sent as data is empty.')
                    self.removeScreen(screen)
                else:
                    # failure - convey retry message and stay on screen
                    tk.messagebox.showinfo(parent=self.rootWindow,message='The data entered was not saved correctly, please try again.')
            else:
                tk.messagebox.showinfo(parent=self.rootWindow,message='The RFID card/tag you are using is already been linked with a member''s account. Please try another.')
            
    def validate(self,data,toValidate):
        if toValidate == 'email':
            import re
            match = re.search(r"(^[a-zA-Z0-9_.-]+@[a-zA-Z0-9]+\.([a-zA-Z0-9-.]|([a-zA-Z0-9-.]+.[a-zA-Z]))$)",data)
            if match or data =='<empty>':
                return True
            else:
                return False
        elif toValidate == 'userid':
            import os,csv
            # Change directory to where the data file will live
            os.chdir(self.csvFileLocation)
            dataInCSV = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberinfo.csv')
            return any(data in subl for subl in dataInCSV)
        
        elif toValidate == 'uniqueCardID':
            import os,csv
            # Change directory to where the data file will live
            os.chdir(self.csvFileLocation)
            csvData = self.getFileDataAsAList(self.csvFileLocation + 'YFBCMemberinfo.csv')
            isIDPresent = any(data in ind for ind in csvData)
            return isIDPresent
        elif toValidate == 'checkin':
            import os,csv
            # Change directory to where the data file will live
            os.chdir(self.csvFileLocation)
            with open('YFBCEventLogs.csv','r') as csvfile:
                rd = csv.reader(csvfile,delimiter=',')
                isMemberCheckedIn = False
                for row in rd:
                    if (data[0] in row) and (data[1] in row):
                        isMemberCheckedIn = True
                        break
            return isMemberCheckedIn
            
        elif toValidate == 'memberDetails':
            fName,lName,email,contactNo,memType = data[0].get(),data[1].get(),data[2].get(),data[3].get(),data[4].get()
            if self.checkIfStringHas(fName,'Numbers') or self.checkIfStringHas(lName,'Numbers') or not(len(str(fName).split()) == 1) \
               or self.checkIfStringHas(contactNo,'Characters') or sum(c.isalpha() for c in fName) < 2 \
               or sum(c.isdigit() for c in contactNo) != 10 or (not(self.validate(email,'email'))) or memType not in self.memTypes:
                return False
            else:
                return True
        elif toValidate == 'date':
            import time
            try:
                time.strptime(data, '%d %B %Y')
            except ValueError:
                return False
            else:
                return True
                
    def checkIfStringHas(self,inputString,WhatToCheck):
        if WhatToCheck == 'Numbers':
            return any(char.isdigit() for char in inputString)
        elif WhatToCheck == 'Characters':
            return any(char.isalpha() for char in inputString)

    def pastFourHours(self,timeStamp):
        minutesPassed = 60*(int(time.strftime('%H'))-int(timeStamp[0:2])) + int(time.strftime('%M'))-int(timeStamp[3:5])
        return (minutesPassed > 240)
    
    def sendemailToMember(self,details,subject):
        """ Send email to member's ID with his registered details"""
        # details - [fName,lName,email,contactNo,memType]
        import smtplib
        from email.mime.text import MIMEText

        # Sending account Information
        gmail_user = 'khadilkar.nakul@gmail.com'
        gmail_password = 'Nakul1991'
        smtpserver = smtplib.SMTP('smtp.gmail.com', 587) # Server to use.

        smtpserver.ehlo()  # Says 'hello' to the server
        smtpserver.starttls()  # Start TLS encryption
        smtpserver.ehlo()
        smtpserver.login(gmail_user, gmail_password)  # Log in to server
        message = ('Hi %s,\n\nYour registration is complete. Here are the details stored in our database for future reference.\n' \
                  'First Name : %s\nLast Name : %s\nEmail ID : %s\nContact Number : +91%s\nMembership Type : %s\n\n\nThank' \
                   ' you,\nYellow Feathers Badminton Club\nBengaluru' % (details[0],details[0],details[1],details[2],details[3],details[4]))
        msg = MIMEText(message)
        club = 'Yellow Feather Badminton Club,  Bengaluru'
        cc = 'vinkhadilkar@gmail.com'
        msg['Subject'] = subject
        msg['From'] = club
        msg['To'] = details[2]
        msg['cc'] = cc
        # Sends the message
        smtpserver.sendmail(gmail_user, [details[2],cc], msg.as_string())
        # Closes the smtp server.
        smtpserver.quit()

    def CSVOperation(self,data,filename,mode,writeNewOrAppend):
        import os,csv
        # Change directory to where the data file will live
        os.chdir(self.csvFileLocation)

        if mode == 'write':
            with open(filename,writeNewOrAppend) as csvfile:
                wrt = csv.writer(csvfile,delimiter=',')
                wrt.writerow(data)
        elif mode == 'read':
            with open(filename,'r') as csvfile:
                rd = csv.reader(csvfile,delimiter=',')
                matchedRow = []
                for row in rd:
                    if data in row:
                        matchedRow = row
                        break
            return matchedRow
        elif mode == 'lastrow':
            data = self.getFileDataAsAList(filename)
            lastRow = data[len(data)-1]
            return lastRow
                    
    def getFileDataAsAList(self,filename):
        import csv
        with open(filename,'r') as csvfile:
                rd = csv.reader(csvfile,delimiter=',')
                data = list(rd)
        return data
    
    def uploadDataFilesToDrive(self):
        import os
        os.chdir(self.csvFileLocation)
        os.system('sudo python uploadFileToDrive.py')
        tk.messagebox.showinfo(parent=self.rootWindow,message='Update successful!')

    # RFID card read/write methods
    def RFIDInit(self):
        import RPi.GPIO as GPIO
        import SimpleMFRC522
        return SimpleMFRC522.SimpleMFRC522()
    
    def writeToCard(self,text):
        writer = self.RFIDInit()
        id, text = writer.write(text)
        return id,text
    
    def readCard(self):
        reader = self.RFIDInit()
        id, text = reader.read()
        return id,text

    def detectRFIDCard(self):
        self.cardDetected = False
        while(self.cardDetected == False):
            # get card details
            idFromCard,dataFromCard = self.readCard()
            # detect card content if admin and card ID if user
            if (str(dataFromCard[0:8]) == 'adminkey') or (self.validate(str(idFromCard),'uniqueCardID')):
                self.cardDetected = True 
                if str(dataFromCard[0:8]) == 'adminkey':
                    # Admin access
                    self.adminScreen()
                elif self.validate(str(idFromCard),'uniqueCardID'):
                    # User entry log
                    self.writeEventLogsAfterCardDetection(str(idFromCard))
        
# Routine
if __name__ == '__main__':
    import RPi.GPIO as GPIO
    GPIO.setwarnings(False)
    try:
        yfbc = yfbcblr()
        # Start card detection loop
        yfbc.detectRFIDCard()
    except e:
        print(e)
        GPIO.cleanup()
        print('Error encountered. Stopping program')
