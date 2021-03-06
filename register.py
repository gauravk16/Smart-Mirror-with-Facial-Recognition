import sys
import os
import cv2

from PyQt4.QtCore import QSize, Qt
import PyQt4.QtCore as QtCore 
from PyQt4.QtGui import *

import locale
import threading
import time
import requests
import json
import traceback
import feedparser
import MySQLdb

from PIL import Image, ImageTk
from contextlib import contextmanager

import imageUpload as imup
import MSFaceAPI as msface
import numpy as np

LOCALE_LOCK = threading.Lock()

window_width = 700
window_height = 460
window_x = 400
window_y = 150
ip = '192.168.0.102'
ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = "hh:mm:ss" # 12 or 24
date_format = "dd-MM-YYYY" # check python doc for strftime() for options
large_text_size = 28
medium_text_size = 18
small_text_size = 10

base_path = os.path.dirname(os.path.realpath(__file__))
dataset_path = os.path.join(base_path,'dataset')
tmp_path = os.path.join(base_path,'tmp')
cloudinary_dataset = 'https://res.cloudinary.com/dca3t5mhf/image/upload/v1551287002/SmartMirror/dataset'
cloudinary_tmp = 'https://res.cloudinary.com/dca3t5mhf/image/upload/v1551287002/SmartMirror/tmp'


camera_port = 1
user={
    'uname':'',
    'fname':'',
    'lname':'',
    'email':'',
    'gender':'',
    'dob':'',
    'personId':''

}


reminder={
    'userid':'',
    'username':'',
    'rem':'',
    'dt':'',

}


event={
    'userid':'',
    'username':'',
    'title':'',
    'date':'',
    'time':'',

}

conn = MySQLdb.connect("localhost","pi","thor","mydb" )

TABLE_NAME="users"
cursor = conn.cursor()

def query(comm,params):
    cursor.execute(comm,params)
    conn.commit()
    return cursor    

new_user_added = False
new_reminder_added = False
new_event_added = False

class SignUpForm(QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(SignUpForm, self).__init__()
        self.initUI()
        self.verified = False


    def initUI(self):

        self.top = QFrame()
        self.bottom = QFrame()
        #self.top.setFrameShape(QFrame.StyledPanel)
        self.top.setObjectName("gframe")
        self.bottom.setObjectName("gframe")
        #self.bottom.setFrameShape(QFrame.StyledPanel)
        self.vbox = QVBoxLayout()
        self.uname = ''
        self.unameLbl = QLabel('User Name')
        self.fnameLbl = QLabel('First Name')
        self.lnameLbl = QLabel('Last Name')
        self.emailLbl = QLabel('Email')
        self.genderLbl = QLabel('Gender')
        self.dobLbl = QLabel('DOB')

        self.unameEdt = QLineEdit()
        self.fnameEdt = QLineEdit()
        self.lnameEdt = QLineEdit()
        self.genderEdt = QComboBox()
        self.dobEdt = QDateEdit()
        self.dobEdt.setDisplayFormat('dd/MM/yyyy')
        self.emailEdt = QLineEdit()
        self.dobEdt.setCalendarPopup(True)
        self.genderEdt.addItems(["Male", "Female","Other"])
        self.unameEdt.textChanged.connect(self.__handleTextChanged)
        self.fnameEdt.textChanged.connect(self.__handleTextChanged)
        self.lnameEdt.textChanged.connect(self.__handleTextChanged)
        self.dobEdt.dateChanged.connect(self.__handleTextChanged)
        self.emailEdt.textChanged.connect(self.__handleTextChanged)
        self.genderEdt.currentIndexChanged.connect(self.__handleTextChanged)
        
        self.fbox=QFormLayout()
        self.fbox.setContentsMargins(100, 20, 100, 20)
        self.fbox.setSpacing(10)
        self.fbox.addRow(self.unameLbl,self.unameEdt)
        self.fbox.addRow(self.fnameLbl,self.fnameEdt)
        self.fbox.addRow(self.lnameLbl,self.lnameEdt)
        self.fbox.addRow(self.dobLbl,self.dobEdt)
        self.fbox.addRow(self.emailLbl,self.emailEdt)
        self.fbox.addRow(self.genderLbl,self.genderEdt)
        
        font1 = QFont('Helvetica', small_text_size)
        self.messageLbl = QLabel('')
        self.messageLbl.setFont(font1)
        self.verifyButton = QPushButton('Verify Data', self)
        self.verifyButton.clicked.connect(self.verifyData)
        self.createButton = QPushButton('Create User', self)
        self.createButton.clicked.connect(self.createUser)
        
        self.vbox1 = QVBoxLayout()
        self.hbox1 = QHBoxLayout() 
        self.hbox = QHBoxLayout()
        
        self.hbox.setAlignment(Qt.AlignCenter)
        self.hbox1.setAlignment(Qt.AlignCenter)
        self.vbox1.setAlignment(Qt.AlignCenter)
        
        
        self.hbox.addWidget(self.messageLbl)
        self.hbox1.addStretch(2)
        self.hbox1.addWidget(self.verifyButton)
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.createButton)
        self.hbox1.addStretch(2)
        #self.hbox1.addWidget(self.nextButton)
        self.vbox1.addLayout(self.hbox)
        self.vbox1.addLayout(self.hbox1)
        self.hbox1.setSpacing(10)
        #self.vbox1.setContentsMargins(250, 10, 250, 20)

        self.topvBox = QVBoxLayout()
        self.topvBox.setAlignment(Qt.AlignCenter)
        self.topvBox.addLayout(self.fbox)
        self.top.setLayout(self.topvBox)
        self.bottom.setLayout(self.vbox1)
        
        self.splitter1 = QSplitter(Qt.Vertical)
        self.splitter1.addWidget(self.top)
        self.splitter1.addWidget(self.bottom)
        self.splitter1.setSizes([550,150])

        self.vbox.addWidget(self.splitter1)
        self.setLayout(self.vbox)



    def __handleTextChanged(self, text):
        self.verified = False

    def verifyData(self):
        self.verified=False
        global new_user_added
        new_user_added = False
        if (not self.unameEdt.text()) or (not self.fnameEdt.text()) or (not self.lnameEdt.text()) or (not self.emailEdt.text()) :
            self.messageLbl.setText('Error: One or more required fields empty! verification failed')
            print 'One or more required fields empty ! fill them all'
            print 'Verification failed'
            return
        user['uname']=str(self.unameEdt.text())
        user['fname']=str(self.fnameEdt.text())
        user['lname']=str(self.lnameEdt.text())
        user['email']=str(self.emailEdt.text())
        print user['email']
        user['dob']=str(self.dobEdt.date().toString('dd-MM-yyyy'))
        user['gender']=str(self.genderEdt.currentText())
        
        sql_command = """SELECT * FROM users WHERE uname = '%s' """ % (user['uname'])
        cursor.execute(sql_command)
        
        if cursor.fetchone():
            self.messageLbl.setText('Error: Username already exist! try something new')
            print 'Username already exist'
            print 'Verification failed'
        else:
            self.messageLbl.setText('Success: Verification Successful!')
            print 'verification successful'
            self.verified = True


    def createUser(self):
        if self.verified == True:
            user['personid'] = msface.create_person(user['uname'],user['fname']+' '+ user['lname'])
            
            if not user['personid']:
                self.messageLbl.setText('Error: Error while creating person! try again')
                return

            self.messageLbl.setText('Success: User created: %s!' % user['uname'])    
            print "User created ... " + user['uname']
            print "PersonID = " + user['personid']
            
            format_str = """INSERT INTO users (id,uname,fname,lname,dob,email,gender,personid) 
                     VALUES (NULL,%s,%s,%s,%s,%s,%s,%s);"""
            params = (user['uname'], user['fname'], user['lname'],user['dob'],user['email'],user['gender'],user['personid'])         
            cursor.execute(format_str,params)
            self.messageLbl.setText('Success: User added to database sucessfully! Generate Face Dataset now')
            
            print "User added to database sucessfully!"
            conn.commit()
            global new_user_added
            new_user_added = True
            
        else:
            self.messageLbl.setText('Warning: Verification not done! first verify')
            print "Verification not done! first verify"



class RemindersForm(QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(RemindersForm, self).__init__()
        self.initUI()
        self.verified = False


    def initUI(self):

        self.top = QFrame()
        self.bottom = QFrame()
        #self.top.setFrameShape(QFrame.StyledPanel)
        self.top.setObjectName("gframe")
        self.bottom.setObjectName("gframe")
        #self.bottom.setFrameShape(QFrame.StyledPanel)
        self.vbox = QVBoxLayout()
        #self.uname = ''
        self.usernameLbl = QLabel('Username')
        self.remLbl = QLabel('Reminder')
        self.dtLbl = QLabel('Date')
        #self.stockexchangeLbl = QLabel('Stock Exchange')
        #self.genderLbl = QLabel('Gender')
        #self.dobLbl = QLabel('DOB')

        self.usernameEdt = QLineEdit()
        self.remEdt = QLineEdit()
        self.dtEdt = QDateEdit()
        self.dtEdt.setDisplayFormat('dd/MM/yyyy')
        #self.stockexchangeEdt = QLineEdit()
        #self.dobEdt = QDateEdit()
        #self.dobEdt.setDisplayFormat('dd/MM/yyyy')
        #self.emailEdt = QLineEdit()
        #self.dobEdt.setCalendarPopup(True)
        #self.genderEdt.addItems(["Male", "Female","Other"])
        #self.unameEdt.textChanged.connect(self.__handleTextChanged)
        self.usernameEdt.textChanged.connect(self.__handleTextChanged)
        self.remEdt.textChanged.connect(self.__handleTextChanged)
        self.dtEdt.dateChanged.connect(self.__handleTextChanged)
        #self.stockexchangeEdt.textChanged.connect(self.__handleTextChanged)
        #self.genderEdt.currentIndexChanged.connect(self.__handleTextChanged)
        
        self.fbox=QFormLayout()
        self.fbox.setContentsMargins(100, 20, 100, 20)
        self.fbox.setSpacing(10)
        self.fbox.addRow(self.usernameLbl,self.usernameEdt)
        self.fbox.addRow(self.remLbl,self.remEdt)
        self.fbox.addRow(self.dtLbl,self.dtEdt)
        #self.fbox.addRow(self.stockexchangeLbl,self.stockexchangeEdt)
        #self.fbox.addRow(self.emailLbl,self.emailEdt)
        #self.fbox.addRow(self.genderLbl,self.genderEdt)
        
        font1 = QFont('Helvetica', small_text_size)
        self.messageLbl = QLabel('')
        self.messageLbl.setFont(font1)
        self.verifyButton = QPushButton('Verify Data', self)
        self.verifyButton.clicked.connect(self.verifyData)
        self.createButton = QPushButton('Create Reminder', self)
        self.createButton.clicked.connect(self.createReminder)
        
        self.vbox1 = QVBoxLayout()
        self.hbox1 = QHBoxLayout() 
        self.hbox = QHBoxLayout()
        
        self.hbox.setAlignment(Qt.AlignCenter)
        self.hbox1.setAlignment(Qt.AlignCenter)
        self.vbox1.setAlignment(Qt.AlignCenter)
        
        
        self.hbox.addWidget(self.messageLbl)
        self.hbox1.addStretch(2)
        self.hbox1.addWidget(self.verifyButton)
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.createButton)
        self.hbox1.addStretch(2)
        #self.hbox1.addWidget(self.nextButton)
        self.vbox1.addLayout(self.hbox)
        self.vbox1.addLayout(self.hbox1)
        self.hbox1.setSpacing(10)
        #self.vbox1.setContentsMargins(250, 10, 250, 20)

        self.topvBox = QVBoxLayout()
        self.topvBox.setAlignment(Qt.AlignCenter)
        self.topvBox.addLayout(self.fbox)
        self.top.setLayout(self.topvBox)
        self.bottom.setLayout(self.vbox1)
        
        self.splitter1 = QSplitter(Qt.Vertical)
        self.splitter1.addWidget(self.top)
        self.splitter1.addWidget(self.bottom)
        self.splitter1.setSizes([550,150])

        self.vbox.addWidget(self.splitter1)
        self.setLayout(self.vbox)



    def __handleTextChanged(self, text):
        self.verified = False

    def verifyData(self):
        self.verified=False
        global new_reminder_added
        new_reminder_added = False
        if (not self.usernameEdt.text()) or (not self.remEdt.text()) :
            self.messageLbl.setText('Error: One or more required fields empty! verification failed')
            print 'One or more required fields empty ! fill them all'
            print 'Verification failed'
            return
        reminder['username']=str(self.usernameEdt.text())
        reminder['rem']=str(self.remEdt.text())
        reminder['dt']=str(self.dtEdt.date().toString('dd-MM-yyyy'))
        #stock['stock_exchange']=str(self.stockexchangeEdt.text())
        #print user['email']
        #user['dob']=str(self.dobEdt.date().toString('dd-MM-yyyy'))
        #user['gender']=str(self.genderEdt.currentText())
        
        sql_command = """SELECT * FROM users WHERE uname = '%s' """ % (reminder['username'])
        cursor.execute(sql_command)
        
        if (not cursor.fetchone()):
            self.messageLbl.setText('Error: The given username does not exist! Please register yourself...')
            print 'User name does not exist'
            print 'Verification failed'
        else:
            cursor.execute(sql_command)
            reminder['userid']=cursor.fetchone()[0]
            self.messageLbl.setText('Success: Verification Successful!')
            print 'verification successful'
            self.verified = True


    def createReminder(self):
        if self.verified == True:

            self.messageLbl.setText('Success: Reminder created: %s!' % reminder['rem'])    
            print "Reminder created ... " + reminder['rem']
            print "On Date = " + reminder['dt']
            
            format_str = """INSERT INTO reminders (id, userid, rem, dt) 
                     VALUES (NULL,%s,%s,%s);"""
            params = (reminder['userid'], reminder['rem'], reminder['dt'])         
            cursor.execute(format_str,params)
            self.messageLbl.setText('Success: Reminder added to database sucessfully!')
            
            print "Reminder added to database sucessfully!"
            conn.commit()
            global new_reminder_added
            new_reminder_added = True
            
        else:
            self.messageLbl.setText('Warning: Verification not done! first verify')
            print "Verification not done! first verify"

class EventsForm(QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(EventsForm, self).__init__()
        self.initUI()
        self.verified = False


    def initUI(self):

        self.top = QFrame()
        self.bottom = QFrame()
        #self.top.setFrameShape(QFrame.StyledPanel)
        self.top.setObjectName("gframe")
        self.bottom.setObjectName("gframe")
        #self.bottom.setFrameShape(QFrame.StyledPanel)
        self.vbox = QVBoxLayout()
        #self.uname = ''
        self.usernameLbl = QLabel('Username')
        self.titleLbl = QLabel('Event Title')
        self.dateLbl = QLabel('Event Date')
        self.timeLbl = QLabel('Event Time')
        #self.genderLbl = QLabel('Gender')
        #self.dobLbl = QLabel('DOB')

        self.usernameEdt = QLineEdit()
        self.titleEdt = QLineEdit()
        self.dateEdt = QDateEdit()
        self.timeEdt = QTimeEdit()
        #self.dobEdt = QDateEdit()
        self.dateEdt.setDisplayFormat('dd/MM/yyyy')
        self.timeEdt.setDisplayFormat('hh:mm:ss')
        #self.emailEdt = QLineEdit()
        #self.dobEdt.setCalendarPopup(True)
        #self.genderEdt.addItems(["Male", "Female","Other"])
        #self.unameEdt.textChanged.connect(self.__handleTextChanged)
        self.usernameEdt.textChanged.connect(self.__handleTextChanged)
        self.titleEdt.textChanged.connect(self.__handleTextChanged)
        self.dateEdt.dateChanged.connect(self.__handleTextChanged)
        self.timeEdt.timeChanged.connect(self.__handleTextChanged)
        #self.genderEdt.currentIndexChanged.connect(self.__handleTextChanged)
        
        self.fbox=QFormLayout()
        self.fbox.setContentsMargins(100, 20, 100, 20)
        self.fbox.setSpacing(10)
        self.fbox.addRow(self.usernameLbl,self.usernameEdt)
        self.fbox.addRow(self.titleLbl,self.titleEdt)
        self.fbox.addRow(self.dateLbl,self.dateEdt)
        self.fbox.addRow(self.timeLbl,self.timeEdt)
        #self.fbox.addRow(self.emailLbl,self.emailEdt)
        #self.fbox.addRow(self.genderLbl,self.genderEdt)
        
        font1 = QFont('Helvetica', small_text_size)
        self.messageLbl = QLabel('')
        self.messageLbl.setFont(font1)
        self.verifyButton = QPushButton('Verify Data', self)
        self.verifyButton.clicked.connect(self.verifyData)
        self.createButton = QPushButton('Create Event', self)
        self.createButton.clicked.connect(self.createEvent)
        
        self.vbox1 = QVBoxLayout()
        self.hbox1 = QHBoxLayout() 
        self.hbox = QHBoxLayout()
        
        self.hbox.setAlignment(Qt.AlignCenter)
        self.hbox1.setAlignment(Qt.AlignCenter)
        self.vbox1.setAlignment(Qt.AlignCenter)
        
        
        self.hbox.addWidget(self.messageLbl)
        self.hbox1.addStretch(2)
        self.hbox1.addWidget(self.verifyButton)
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.createButton)
        self.hbox1.addStretch(2)
        #self.hbox1.addWidget(self.nextButton)
        self.vbox1.addLayout(self.hbox)
        self.vbox1.addLayout(self.hbox1)
        self.hbox1.setSpacing(10)
        #self.vbox1.setContentsMargins(250, 10, 250, 20)

        self.topvBox = QVBoxLayout()
        self.topvBox.setAlignment(Qt.AlignCenter)
        self.topvBox.addLayout(self.fbox)
        self.top.setLayout(self.topvBox)
        self.bottom.setLayout(self.vbox1)
        
        self.splitter1 = QSplitter(Qt.Vertical)
        self.splitter1.addWidget(self.top)
        self.splitter1.addWidget(self.bottom)
        self.splitter1.setSizes([550,150])

        self.vbox.addWidget(self.splitter1)
        self.setLayout(self.vbox)



    def __handleTextChanged(self, text):
        self.verified = False

    def verifyData(self):
        self.verified=False
        global new_event_added
        new_event_added = False
        if (not self.usernameEdt.text()) or (not self.titleEdt.text()) :
            self.messageLbl.setText('Error: One or more required fields empty! verification failed')
            print 'One or more required fields empty ! fill them all'
            print 'Verification failed'
            return
        event['username']=str(self.usernameEdt.text())
        event['title']=str(self.titleEdt.text())
        event['date']=str(self.dateEdt.date().toString('dd-MM-yyyy'))
        event['time']=str(self.timeEdt.text())
        #print user['email']
        #user['dob']=str(self.dobEdt.date().toString('dd-MM-yyyy'))
        #user['gender']=str(self.genderEdt.currentText())
        
        sql_command = """SELECT * FROM users WHERE uname = '%s' """ % (event['username'])
        cursor.execute(sql_command)
        
        if (not cursor.fetchone()):
            self.messageLbl.setText('Error: The given userid does not exist! Please register yourself...')
            print 'User id does not exist'
            print 'Verification failed'
        else:
            cursor.execute(sql_command)
            event['userid'] = cursor.fetchone()[0]
            self.messageLbl.setText('Success: Verification Successful!')
            print 'verification successful'
            self.verified = True


    def createEvent(self):
        if self.verified == True:

            self.messageLbl.setText('Success: Event created: %s!' % event['title'])    
            print "Event created ... " + event['title']
            print "Date and time : " + event['date'] + " " + event['time']
            
            format_str = """INSERT INTO events (id, userid, title, date, time) 
                     VALUES (NULL,%s,%s,%s,%s);"""
            params = (event['userid'], event['title'], event['date'], event['time'])         
            cursor.execute(format_str,params)
            self.messageLbl.setText('Success: Event added to database sucessfully!')
            
            print "Event added to database sucessfully!"
            conn.commit()
            global new_event_added
            new_event_added = True
            
        else:
            self.messageLbl.setText('Warning: Verification not done! first verify')
            print "Verification not done! first verify"



class AddDetailsTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AddDetailsTab, self).__init__()
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout()
        self.SignUpFrame = QFrame()
        self.SignUpForm = SignUpForm(self.SignUpFrame)
        self.hbox.addWidget(self.SignUpForm)
        self.vbox  = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)



class AddRemindersTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AddRemindersTab, self).__init__()
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout()
        self.CreateFrame = QFrame()
        self.RemindersForm = RemindersForm(self.CreateFrame)
        self.hbox.addWidget(self.RemindersForm)
        self.vbox  = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)

class AddEventsTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(AddEventsTab, self).__init__()
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout()
        self.CreateFrame = QFrame()
        self.EventsForm = EventsForm(self.CreateFrame)
        self.hbox.addWidget(self.EventsForm)
        self.vbox  = QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)


class GenerateDatasetTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(GenerateDatasetTab, self).__init__()
        self.capturing=False
        self.video_size = QSize(400, 300)
        self.snapshot_size = QSize(100, 100)
        self.store_dir= os.path.join(dataset_path,user['uname'])
        self.cascPath = 'haarcascade_frontalface_default.xml'
        self.faceCascade = cv2.CascadeClassifier(self.cascPath)
        self.snapshotCnt=0
        self.maxSnapshotCnt=8
        self.captureCompleted = False
        self.uploadCompleted = False
        self.trained = False
        self.initUI()



    def initUI(self):
        self.topleft = QFrame()        
        self.imageLabel=QLabel()
        self.imageLabel.setScaledContents(True)
        self.topleft.setObjectName('gframe')
        self.topleft.setContentsMargins(50,10,50,10)
        self.imageLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.vbox1 = QVBoxLayout()
        self.vbox1.addWidget(self.imageLabel)
        self.topleft.setLayout(self.vbox1)

        self.topright = QFrame()
        self.snpGrid = QGridLayout()
        
        self.snpGrid.setSpacing(2)
        self.snpGrid.setContentsMargins(2,2,2,2)
        
        self.topright.setLayout(self.snpGrid)
        self.hbox = QHBoxLayout()
        self.startButton = QPushButton('Start')
        self.stopButton = QPushButton('Stop')
        self.takeSnapshotButton = QPushButton('Take Snapshot')
        self.uploadDatasetButton = QPushButton('Upload Dataset')
        self.trainModelButton = QPushButton('Train Model')
        self.messageLbl = QLabel('')
        font1 = QFont('Helvetica', small_text_size)
        self.messageLbl.setFont(font1)

        self.startButton.clicked.connect(self.startCapture)
        self.stopButton.clicked.connect(self.stopCapture)
        self.takeSnapshotButton.clicked.connect(self.takeSnapshot)
        self.uploadDatasetButton.clicked.connect(self.uploadDataset)
        self.trainModelButton.clicked.connect(self.trainModel)

        self.hbox.addWidget(self.startButton)
        self.hbox.addWidget(self.stopButton)
        self.hbox.addWidget(self.takeSnapshotButton)
        self.hbox.addWidget(self.uploadDatasetButton)
        self.hbox.addWidget(self.trainModelButton)
        
        self.mhbox = QHBoxLayout()
        self.mhbox.setAlignment(Qt.AlignCenter)
        self.mhbox.addWidget(self.messageLbl)

        self.bvbox = QVBoxLayout()
        self.bvbox.addLayout(self.mhbox)
        self.bvbox.addLayout(self.hbox)
        self.bvbox.setSpacing(10)
        
        self.bottom = QFrame()
        self.bottom.setLayout(self.bvbox)
        self.bottom.setObjectName("gframe")

        self.splitter1 = QSplitter(Qt.Horizontal)
        self.splitter1.addWidget(self.topleft)
        self.splitter1.addWidget(self.topright)
        self.splitter1.setSizes([5,2])

        self.splitter2 = QSplitter(Qt.Vertical)
        self.splitter2.addWidget(self.splitter1)
        self.splitter2.addWidget(self.bottom)
        self.splitter2.setSizes([375,75])
        self.hbox1=QHBoxLayout()
        self.hbox1.addWidget(self.splitter2)
        self.setLayout(self.hbox1)
        self.initGrid()

    def initDir(self):
        self.store_dir= os.path.join(dataset_path,user['uname'])
        if os.path.isdir(self.store_dir)==False:
            try:
                original_umask = os.umask(0)
                os.makedirs(self.store_dir)
            finally:
                os.umask(original_umask)

    def initGrid(self):
        range_x=(self.maxSnapshotCnt+1)/2
        self.snpLabels =[]
        for i in range(self.maxSnapshotCnt):
            self.snpLabels.append(QLabel())
            self.snpLabels[i].setScaledContents(True)
            self.snpLabels[i].setFixedSize(self.snapshot_size)
            self.snpLabels[i].setObjectName("gframe")

        range_y =2
        pos = [(i,j) for i in range(range_x) for j in range(range_y)]
        
        for p, lbl in zip(pos, self.snpLabels):
            self.snpGrid.addWidget(lbl,*p)


    def display_video_stream(self):
        ret, frame = self.capture.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                
        faces = self.faceCascade.detectMultiScale(
          gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40),
            flags=cv2.cv.CV_HAAR_SCALE_IMAGE
        )

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
        frame = cv2.cvtColor(frame, cv2.cv.CV_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = QImage(frame, frame.shape[1], frame.shape[0], 
                       frame.strides[0], QImage.Format_RGB888)
        
        self.imageLabel.setPixmap(QPixmap.fromImage(image))



    def startCapture(self):
        global new_user_added
        if new_user_added == True:

            self.initDir()
            self.capturing = True
            self.capture = cv2.VideoCapture(0)
            self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.video_size.width())
            self.capture.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.video_size.height())

            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.display_video_stream)
            self.timer.start(30)

        else:
            self.messageLbl.setText('Warning: First create new user')

    def stopCapture(self):
        #print "pressed End"
        if self.capturing == True:
            self.capturing = False
            self.capture.release()
            self.timer.stop()
            cv2.destroyAllWindows()

    def takeSnapshot(self):

        if self.capturing == False:
            self.messageLbl.setText('Warning: Start the camera')
            return

        if self.snapshotCnt == self.maxSnapshotCnt:
            self.messageLbl.setText('Warning: All snapshots taken, no need to take more now!')
            return                 
        
        if (self.capturing == True)  and (self.snapshotCnt < self.maxSnapshotCnt):
            try:
                r , frame = self.capture.read()
                frame = cv2.flip(frame, 1)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.faceCascade.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(40, 40),
                    flags=cv2.cv.CV_HAAR_SCALE_IMAGE
                )
                if len(faces)==0:
                    return
                max_area = 0
                mx = 0
                my = 0 
                mh = 0 
                mw = 0
                for (x, y, w, h) in faces:
                    if w*h > max_area:
                        mx = x
                        my = y
                        mh = h
                        mw = w
                        max_area=w*h    
                
                image_crop = frame[my:my+mh,mx:mx+mw]
                self.snapshotCnt=self.snapshotCnt+1
                self.messageLbl.setText('Process: Total snapshots captured: %d (Remaining: %d)' % (self.snapshotCnt,self.maxSnapshotCnt-self.snapshotCnt))
                file_name = 'img_%d.jpg'% (self.snapshotCnt)
                file = os.path.join(self.store_dir,file_name)
                cv2.imwrite(file, image_crop)
                self.snpLabels[self.snapshotCnt-1].setPixmap(QPixmap(file))

            except Exception as e:
                self.messageLbl.setText('Error: Snapshot capturing failed')
                print "Snapshot capturing failed...\n Errors:"
                print e

        if(self.snapshotCnt == self.maxSnapshotCnt):
            self.captureCompleted=True
            self.stopCapture()


    def uploadDataset(self):
        if self.capturing == True:
            self.stopCapture()

        if self.captureCompleted == False:
            self.messageLbl.setText('Warning: Take required no of snapshot for uploading dataset!')
            return
        i=1
        personName = user['uname']
        if not personName:
            self.messageLbl.setText('Error: Username empty!')
            print 'username empty!'
            self.messageLbl.setText('Error: Upload dataset failed!')
            print 'upload dataset failed!'
            return

        for file in os.listdir(self.store_dir):
            file_path=os.path.join(self.store_dir,file)
            try:
                self.messageLbl.setText('Process: Uploading image... %d' %i)
                print 'Uploading... %d' % i
                imup.upload_person_image(file_path,file,user['uname'])
                print 'Uploaded... %d' % i
                self.messageLbl.setText('Success: Uploaded image... %d' %i)
                i=i+1
            except Exception as e:
                print("Error: %s" % e.message)

        if i==1:
            self.messageLbl.setText('Error: Some error while uploading to cloudnary, Please try later!')
            print 'Some error while uploading to cloudnary, Please try later!'
            return

        try:    
            cloudinary_dir= cloudinary_dataset+'/'+personName+'/'
            for i in range(1,self.maxSnapshotCnt+1):
                image_url=cloudinary_dir+'img_%d.jpg' % i
                print image_url
                self.messageLbl.setText('Process: Adding face... %d' %i)
                print 'Adding face... %d'%i
                msface.add_person_face(user['personId'],image_url)
                print 'Added face... %d'%i
                self.messageLbl.setText('Success: Added face... %d' %i)
            
            print "Dataset Uploaded Sucessfuly!"    
            self.messageLbl.setText('Success: Dataset Uploaded Sucessfuly!')
            self.uploadCompleted = True    
        except Exception as e:
                self.messageLbl.setText('Error: Unknown Error!')
                print("Error: \n")
                print e

    def trainModel(self):
            self.messageLbl.setText('Process: Training Started ')
            print('Training Started...')
            msface.train()
            print('Training Completed...')
            self.messageLbl.setText('Success: Training Completed Successfully')

class MainWindow:

    def __init__(self): 
        self.qt = QTabWidget()
        self.qt.setGeometry(window_x, window_y, window_width, window_height)
        self.pal=QPalette()
        self.pal.setColor(QPalette.Background,Qt.white)
        self.pal.setColor(QPalette.Foreground,Qt.black)
        self.qt.setPalette(self.pal)
    
        self.tab1 = QWidget()
        self.DetailsTab=AddDetailsTab(self.tab1)
        self.qt.addTab(self.DetailsTab,"Create User")
    
        self.tab2 = QWidget()
        self.DatasetTab=GenerateDatasetTab(self.tab2)
        self.qt.addTab(self.DatasetTab,"Generate Face Dataset")

        self.tab3 = QWidget()
        self.ReminderTab=AddRemindersTab(self.tab3)
        self.qt.addTab(self.ReminderTab,"Add Reminder")

        self.tab4 = QWidget()
        self.EventsTab=AddEventsTab(self.tab3)
        self.qt.addTab(self.EventsTab,"Create Event")

        self.qt.show()
        self.qt.setStyleSheet("#gframe {border-radius:5px;border:1px solid #a5a5a5}")
        


if __name__ == '__main__':
    a = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(a.exec_())
