#!/usr/bin/env python
__author__ = "Jan Figat"

# Importing core system functionality
import signal
import os, sys
import rospy
import rosparam

# Importing services
from rapp_ros_naoqi_wrappings.srv import *

# Needed for encoding a file
import base64

# Importing OpenCV library
#import cv #cv2.cv as cv #Use OpenCV-2.4.3
#import cv2

# Importing others
import numpy as np
import math
import Image
import time #for time measurement
import almath #Aldebaran's library for matrices operation


class AcoreCameraClient():
	
	def __init__(self):
		print "[Camera client] - Acore camera Client initialization"
	

	# Handling a communication with service "rapp_capture_image"
	def captureCameraFrame(self,request):
		print "[Camera client] - Waits for server"
		rospy.wait_for_service('rapp_capture_image')
		try:
			print "[Camera client] - captureCameraFrame"
			captureImage = rospy.ServiceProxy('rapp_capture_image', GetImage)
			resp_capture_image = captureImage(request, resolution)
			print "[Camera client] - Image captured"
			return resp_capture_image
		except rospy.ServiceException, e:
			print "[Camera client] - Calling service [/rapp_capture_image] Failed: %s"%e
			exit(1)
	
	
			
######################################################################
## Functions defined by rapp dynamic agent programmer ##
######################################################################

	# A method that i used to attach files (recorded audio and an Rapp image) 
	# into a message and then sends it to defined email address.
	

# Testng SIGINT signal handler
def signal_handler(signal, frame):
	print "[Camera server] - signal SIGINT caught"
	print "[Camera server] - system exits"
	sys.exit(0)

# Main entry point
def main():
	signal.signal(signal.SIGINT, signal_handler)
	print "[Camera server] - Press Ctrl + C to exit system correctly"
	
	# Testing ROS params
	say_param="Core agent"
	rospy.set_param("say_param", say_param)
	xy=rospy.get_param("say_param")	
	
	print "[Camera client] - Requesting %s" % (xy)
	client = AcoreCameraClient()
	
	# Testing [/rapp_capture_image] service
	print "[Camera client] - Testing [/rapp_capture_image] service"
	response_image = client.captureCameraFrame("top", 2) # "top - adaptive auto exposure 1" #0: Average scene Brightness; 1: Weighted average scene Brightness; 2: Adaptive weighted auto exposure for hightlights; 3: Adaptive weighted auto exposure for lowlights
	
	return


if __name__ == "__main__":
	try:
		main()
	except Exception,e:
		print "__name__ - Error %s" % str(e)
