#!/usr/bin/env python

########################
# Imports
########################

# Importing services
from rapp_core_agent.srv import *

# Importing core system functionality
import signal
import sys, os
import rospy
import time

# Importing core functionality from Naoqi
from naoqi import ALProxy
from naoqi import ALBroker
from naoqi import ALModule

# Used for finding a text in a file
import mmap

# Needed for encoding a file
import base64

# Email sending
import smtplib
from email.mime.text import MIMEText
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.Encoders import encode_base64

#######################################

# Global variables to store the EmailRecognition module instance and proxy to ALMemory Module
EmailRecognition = None
prox_memory = None

# Constants
class Constants:
	
	SOUND_DETECTED = "onSoundDetected"
	EVENT_SOUND = "SoundDetected"
	NAO_IP = "nao.local"
	PORT = 9559

#######################################

# EmailRecognitionModule class definition
class EmailRecognitionModule(ALModule):
	""" A simple module able to react to
	sound detection events
	"""
	
	# Constructor of EmailRcognitionModule
	def __init__(self,name):
		ALModule.__init__(self,name)
		
		print "[Email server] - Acore email Server initialization"
		
		# Initialization of ROS node
		rospy.init_node('acore_email_server')
		self.moduleName = name
		
		# Initialization of Naoqi modules and ROS services
		self.initALModule()
		
		self.setVariables()
		self.openServices()
		
		print "[Email server] - Waits for clients ..."
		
		
	
	# Initialization of Naoqi modules
	def initALModule(self):
		print "[Email server] - Initialization of Naoqi modules"
		
		print "[Email server] - ALMemory proxy initialization"		
		global prox_memory
		prox_memory = ALProxy("ALMemory")
		if prox_memory is None:
			rospy.logerr("[Email server] - Could not get a proxy to ALMemory")
			exit(1)
			
		print "[Email server] - ALTextToSpeech proxy initialization"
		self.prox_tts = ALProxy("ALTextToSpeech")
		if self.prox_tts is None:
			rospy.logerr("[Email server] - Could not get a proxy to ALTextToSpeech")
			exit(1)
			
		print "[Email server] - ALSoundDetection proxy initialization"
		self.prox_sd = ALProxy("ALSoundDetection")
		if self.prox_sd is None:
			rospy.logerr("[Email server] - Could not get a proxy to ALSoundDetection")
			exit(1)
			
		print "[Email server] - ALSpeechRecognition proxy initialization"
		self.prox_sprec = ALProxy("ALSpeechRecognition")
		if self.prox_sprec is None:
			rospy.logerr("[Email server] - Could not get a proxy to ALSpeechRecognition")
			exit(1)
		
		print "[Email server] - ALAudioRecorder proxy initialization"
		self.prox_ar = ALProxy("ALAudioRecorder")
		if self.prox_ar is None:
			rospy.logerr("[Send Email]- Could not get a proxy to ALAudioRecorder")
			exit(1)
	
	
	# Setting variables
	def setVariables(self):
		print "[Email server] - Setting variables"
		self.isEmailFound = False
		self.stopListening = False
		self.email_address = "rapp.nao@gmail.com"
		self.prox_sd.setParameter("Sensitivity",0.7)
		self.period=500
		self.memValue = "LastWordRecognized"
		# Temporary database of recognized words
		self.database = ["John", "Max", "Rapp", "Nao", "Alarm", "Exit"]
		self.prox_sprec.pause(True)
		self.prox_sprec.setVocabulary(self.database, False)
		self.prox_sprec.pause(False)
		
		# Testing on NAO
		#self.filePath = "/home/nao/naoqi/lib/naoqi/data/"
		# Testing on external computer
		self.filePath = "/home/viki/catkin_ws/src/rapp_dynamic_agent/data/"
		
		self.recordedFileDest="/home/nao/recordings/microphones/rapp_email.ogg"
		# Testing on computer
		
		self.recordedExtention="ogg"
		# Sample rate of recorded audio (in Hz)
		self.sampleRate = 16000
		# Creating channel
		self.channels = []
		#Channels setup
		self.channels.append(0)
		self.channels.append(0)
		self.channels.append(1)
		self.channels.append(0)
		
		self.recordingTime = 3.0
		
	
		
	# Initialization of ROS services
	def openServices(self):
		try:
			print "[Email server] - setting services"
			print "[Email server] - service - [rapp_say]"
			self.service_rs = rospy.Service('rapp_say', Say, self.handle_rapp_say)
			print "[Email server] - service - [rapp_get_email_address]"
			self.service_rgea = rospy.Service('rapp_get_email_address', GetEmailAddress, self.handle_rapp_get_email_address)
			print "[Email server] - service - [rapp_record]"
			self.service_rr = rospy.Service('rapp_record', Record, self.handle_rapp_record)
			print "[Email server] - service - [rapp_send_email]"
			self.service_rse = rospy.Service('rapp_send_email', SendEmail, self.handle_rapp_send_email)
		except Exception, ex:
			print "[Email server] - Exception %s" % str(ex)
		
	'''# Closes ROS services
	def closeServices(self):
		print "[Email server] - closes services"
		self.service_hw.close()'''
		
	#######################################
	
	# Core functionality methods 
	
	#######################################
	
	# Subscribes Nao events
	def subscribe(self):
		print "[Email server] - Subscribing SoundDetected event"
		
		try:
			self.prox_sprec.subscribe("Test_SpeechDetected",self.period, 0.0)
			prox_memory.subscribeToEvent(Constants.EVENT_SOUND, self.moduleName, "onSoundDetected" )
		except Exception, e:
			print "[Email server] - Error in subscribe(): %s", str(e)
			
		
		
	# Unsubscribes Nao events
	def unsubscribe(self):
		
		print "[Email server] - Unsubscribing SoundDetected event"
		try:
			
			#prox_memory.unsubscribeToEvent(Constants.EVENT_SOUND, self.moduleName)
			self.prox_sprec.unsubscribe("Test_SpeechDetected")
		except TypeError, e:
			print "[Email server] - Error TypeError in unsubscribe(): %s", str(e)
			#self.prox_sprec.unsubscribe("Test_SpeechDetected")
		except Exception, e:
			print "[Email server] - Error in unsubscribe(): %s", str(e)
			#self.prox_sprec.unsubscribe("Test_SpeechDetected")
			
			
	# Method that is called when sound is detected
	def onSoundDetected(self, *_args):
		"""This method will be called each time NAO recognised a sound.
		It will try to find out correct email address.
		"""
		try:
			# Unsubscribing to the event of Sound detection to avoid calling a method while executing interior of the method.
			prox_memory.unsubscribeToEvent(Constants.EVENT_SOUND, self.moduleName)
			val = prox_memory.getData(self.memValue)
			
			print "[Email server] -       " + val[0]
			print "[Email server] - Sleeps"
			time.sleep(1)
			print "[Email server] - [onSoundDetected] - Heard name: " +val[0] +" with the probability equals to " + str(val[1])
			
		
			if len(val[0])!=0 and val[1]>0.5:	
				#if(val[0] == "Exit"):
				#	print "[Email server] - Exits"
				#	self.stopListening=True
				#	return
				#else:
				#	self.findOutEmail(val[0])
				self.findOutEmail(val[0])
				
				print "[Email server] - [onSoundDetected] - Email FOUND: %s" % self.email_address
				return
				
			# Subscribe again to the event
			prox_memory.subscribeToEvent(Constants.EVENT_SOUND, self.moduleName, "onSoundDetected" )
			
		except Exception, e:
			print "[Email server] - onSoundDetected - Exception %s" %e
	
	
	
	# Method used to find out an email address just using local file with email addesses located 
	# (maybe in the future in "../data/email_address.txt" (it can be done using database in a RAPP cloud)
	def findOutEmail(self,name):
		info = "Find out an email address to %s" % name
		print "[Send Email] - Find out an email address to %s" % name
		self.prox_tts.say(info)

		try:
			#rapp_f = open("../data/email_address.txt")self.pathToDictionary
			rapp_f = open(self.pathToDictionary)
			rapp_s = mmap.mmap(rapp_f.fileno(), 0, access=mmap.ACCESS_READ)
			rapp_d = rapp_s.find(name,0)
			rapp_s.seek(rapp_d)
			rapp_e= rapp_s.readline()
			rapp_s.seek(rapp_d+len(name) +1)
			rapp_g = len(rapp_e)-(len(name) +1)
			rapp_email = rapp_s.read(rapp_g)
			print "[Send Email] - An email address is: %s " % rapp_email
			rapp_s.close()
			self.prox_tts.say(rapp_email)
			print "[Send Email] - Setting an email address"
			self.email_address = rapp_email
			self.isEmailFound  = True
		except ValueError:
			print "[Send Email] - findOutEmail - Value Error - Probably there is the difference in name - capital letter"
	
	def countDown(self, message):
		print "[Send Email] - %s in 3 seconds" % message
		self.prox_tts.say(message + " in 3 seconds")
		print "[Send Email] - %s in 2 seconds" % message
		self.prox_tts.say(message + " in 2 seconds")
		print "[Send Email] - %s in 1 seconds" % message
		self.prox_tts.say(message + " in 1 second")
		# Sleeps a while (1 second)
		time.sleep(1)
		print "[Send Email] - GO"
		self.prox_tts.say("GO")
	
	# Record an email message
	def recordEmail(self):
		try:
			print "[Send Email] - Recording an email"
			self.countDown("Recording an email")
						
			#self.prox_ar.stopMicrophonesRecording()
			
			self.prox_ar.startMicrophonesRecording(self.recordedFileDest, self.recordedExtention, self.sampleRate, self.channels )
			print  "[Send Email] - Start Microphones Recording"
			print  "[Send Email] - Sleeps"
			# Waiting recordingTime - it means that the message is being recorded recordingTime (seconds)
			time.sleep(self.recordingTime)
			# Recording stops and the file is being closed after recordingTime
			self.prox_ar.stopMicrophonesRecording()
			print "[Send Email] - Recording stops"
			self.prox_tts.say("Recording stops")

		except Exception, e:
			print "[Send Email] - Error during recording an message"
			print "[Send Email] - Error: %s" % str(e)
			self.prox_ar.stopMicrophonesRecording()
			
	# A method that i used to attach files (recorded audio and an Rapp image) 
	# into a message and then sends it to defined email address.
	def sendEmail(self):
		try:
			print "[Send Email] - Entered a method that sends an Rapp email"
			smtp = 'smtp.gmail.com'
			port = int('587')
			
			print "[Send Email] - Creating an object smtp.SMTP with smtp =",smtp, "and port=",port
			server= smtplib.SMTP(smtp , port)

			# Account data
			email_user = 'rapp.nao@gmail.com'
			email_pwd = 'rapp.nao1'
			
			if len(self.email_address)!=0:
				email_to = self.email_address
			else:
				print "[Send Email] - An email address is not specified!"
				return
			
			subject = "[RAPP message] - Nao sending "			
			text_attach = "Sending an email from NAO"

			audio_nao_attach = self.recordedFileDest
			image="rapp.PNG"
			image_nao_attach=self.filePath+image
			attach=audio_nao_attach
			
			print "[Send Email] - path to audio attachments:", audio_nao_attach
			print "[Send Email] - path to image attachments:", image_nao_attach
			
			print "[Send Email] - preparing content of a message"
			msg = MIMEMultipart() 
			msg['From'] = email_user
			msg['To'] = email_to
			msg['Subject'] = subject
				
			print "[Send Email] - Attaching files"
			if attach:
				
				# Attaching to a message an Rapp recorded audio
				print "[Send Email] - Attaching audio"
				part = MIMEBase('application', 'octet-stream')
				part.set_payload(open(attach, 'rb').read())
				print "[Send Email] - Encoding audio"
				encode_base64(part)
				part.add_header('Content-Disposition','attachment; filename=%s"' % os.path.basename(attach))
				msg.attach(part)
				
				# Attaching to a message an Rapp image
				print "[Send Email] - Attaching image"
				part = MIMEBase('application', 'octet-stream')
				part.set_payload(open(image_nao_attach, 'rb').read())
				print "[Send Email] - Encoding image"
				encode_base64(part)
				part.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(image_nao_attach))
				msg.attach(part)
				
				# Attaching to a message a body
				part = MIMEText(text_attach, 'plain')
				msg.attach(part)

			if( port != "" ):
				mailServer = smtplib.SMTP(smtp, port)
			else:
				mailServer = smtplib.SMTP(smtp)
				
			print "[Send Email] - logging into a server"
			mailServer.ehlo()
			mailServer.starttls()
			mailServer.ehlo()
			mailServer.login(email_user, email_pwd)
			print "[Send Email] - sending an email"
			mailServer.sendmail(email_user, email_to,msg.as_string())

			mailServer.close()
			return 1
		except Exception, e:
			print "[Send Email] - Exception %s"%str(e)
	
	#########################
	
	# Handling methods - methods that used handling services
	
	#########################
		
	def handle_rapp_say(self,req):
		print "[Email server receives]: \t%s\n[Email server returns]: \t%s" % (req.request, "Said: %s"% req.request)
		self.prox_tts.say("Nao says : %s"% req.request)
		return SayResponse(req.request)
		
	def handle_rapp_get_email_address(self, req):
		print "[Email server] - receives path to dictionary \t%s" % req.pathToDictionary
		
		self.pathToDictionary = req.pathToDictionary
		self.isEmailFound  = False
		self.stopListening = False
		isFound=0
		
		try:
			print "[Email server] - Subscribing events"
			self.subscribe()
			#self.prox_sprec.unsubscribe("Test_SpeechDetected")
			while self.isEmailFound == False and self.stopListening == False:
				print "[Email server] - An email address was not found!"
				print "[Email server] - Say a special word from database!"
				time.sleep(4)
						
			print "[Email Email] - Unsubscribing events"
			self.unsubscribe()
			
		except AttributeError, ex:
			print "[Email server] - Exception AtrributeError = %s" % str(ex)
		except Exception, ex:
			print "[Email server] - Unnamed exception = %s" % str(ex)
		
		print "[Email server] - returns email address: \t %s" % self.email_address
		
		if self.isEmailFound == True:
			isFound =1
		return GetEmailAddressResponse(self.email_address, isFound)
	
	def handle_rapp_record(self,req):
		print "[Email server]: - Nao records %d [s]" %req.recordingTime
		self.recordingTime = req.recordingTime
		self.prox_tts.say("Nao records : ")
		self.recordEmail()
		reponse = self.recordedFileDest
		return RecordResponse(reponse)
		
	def handle_rapp_send_email(self,req):
		print "[Email server]: - Nao sends an email to %s" %req.emailAddress
		to_say = "Nao sends an email to %s" %req.emailAddress
		self.prox_tts.say(to_say)
		self.recordedFileDest = req.recordedFileDest
		isEmailSend = self.sendEmail()
		return SendEmailResponse(isEmailSend)

# Testng SIGINT signal handler
def signal_handler(signal, frame):
	print "[Email server] - signal SIGINT caught"
	print "[Email server] - system exits"
	sys.exit(0)

def main():
	""" Main entry point
	
	"""
	# It is needed to use a broker to be able to construct NAOQI 
	# modules and subscribe to other modules. The broker must stay
	# alive until  the program exists
	try:
		signal.signal(signal.SIGINT, signal_handler)
		print "[Email server] - Press Ctrl + C to exit system correctly"
		
		myBroker = ALBroker("myBroker", "0.0.0.0", 0, Constants.NAO_IP,Constants.PORT)
		global EmailRecognition
		EmailRecognition = EmailRecognitionModule("EmailRecognition")
		'''while True:
			time.sleep(1)'''
		rospy.spin()
	
	except AttributeError:
		print "[Email server] - EmailRecognition - AttributeError"
		#EmailRecognition.unsubscribe()
		myBroker.shutdown()
		sys.exit(0)
		
	except (KeyboardInterrupt, SystemExit):
		print "[Email server] - SystemExit Exception caught"
		#EmailRecognition.unsubscribe()
		myBroker.shutdown()
		sys.exit(0)
		
	except Exception, ex:
		print "[Email server] - Exception caught %s" % str(ex)
		#EmailRecognition.unsubscribe()
		myBroker.shutdown()
		sys.exit(0)
		
if __name__ == "__main__":
	try:
		main()
	except Exception,e:
		print "__name__ - Error %s" % str(e)
