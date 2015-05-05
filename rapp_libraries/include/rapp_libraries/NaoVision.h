//#####################
// written by Jan Figat
//#####################

#include "ros/ros.h"
#include "std_msgs/String.h"
#include "rapp_robot_agent/GetImage.h"//change it for core
#include "rapp_robot_agent/SetCameraParam.h"//change it for core
#include "rapp_robot_agent/GetTransform.h"//change it for core
//#include "rapp_robot_agent/Say.h"//change it for core
#include "sensor_msgs/Image.h"

#include <stdio.h>
#include <fstream>

#include <cstdio>
#include <ostream>
#include <iostream>
#include <unistd.h>
#include <vector>
#include <string>

#include <math.h>       // for atan2

//openCV library
#include <cv_bridge/cv_bridge.h>
#include <opencv2/core/core.hpp>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <opencv2/calib3d/calib3d.hpp>

#include <zbar.h> // for QRcode detection


using namespace std;
using namespace cv;
using namespace zbar;

class NaoVision {

public:
	NaoVision (int argc, char **argv);
	ros::ServiceClient client_captureImage;
	ros::ServiceClient client_setCameraParam;
	ros::ServiceClient client_getTransform;
	ros::NodeHandle *n;
	
	std::string NAO_IP;// = "nao.local";
	int NAO_PORT;// = 9559;

	//std::vector< std::vector<float> > cameraTopMatrix(3, vector<float>(3,0.0));
	double camera_top_matrix_3[3][3];
	double camera_top_matrix_2[3][3];
	double camera_top_matrix_1[3][3];

	struct QRcodeDetection
   {
		bool isQRcodeFound;// = false;
		int numberOfQRcodes;// = 0; //number of detected QRcodes
		std::vector< cv::Mat > LandmarkInCameraCoordinate;//Transformation matrix from camera to Landmark
		std::vector< cv::Mat > LandmarkInRobotCoordinate;//Transformation matrix from camera to robot
		std::vector<std::string> QRmessage; //vector for messages from QRcodes

		void clear()
		{
			isQRcodeFound = false;
			numberOfQRcodes = 0;
			LandmarkInCameraCoordinate.clear();
			LandmarkInRobotCoordinate.clear();
			QRmessage.clear();
		}
   };
	
	struct QRcodeHazardDetection
   {
		bool isHazardFound;// = false;
		std::vector<double> hazardPosition_x; // in robot coordinate system - x-axis is directed to the front
		std::vector<double> hazardPosition_y; // in robot coordinate system - y-axis is directed to the left
		std::vector<std::string> openedObject; //message from QRcode of an open object

		void clear()
		{
			isHazardFound = false;
			hazardPosition_x.clear();
			hazardPosition_y.clear();
			openedObject.clear();
		}
   };
	
	void init(int argc, char **argv);

	sensor_msgs::Image captureImage(std::string cameraId, int cameraResolution);	 // For frame capture from selected camera; with the desired camera resolution: 3->4VGA,2->VGA,1->QVGA
	bool setCameraParameter(int cameraId, int cameraParameterId, int newValue );	 /*// Modifies camera internal parameter. cameraId: 0-top; 1-bottom; cameraParameterId - see Camera parameters [http://doc.aldebaran.com/2-1/family/robots/video_robot.html#cameraparameter-mt9m114]
	Parameter			Min	Value	Max Value	Default Value	Camera parameter ID name	cameraParameterId	Remarks
	Brightness				0			255			55			kCameraBrightnessID					0	Auto Exposition must be enabled
	Contrast				16			64			32			kCameraContrastID					1	The contrast value represents the gradient of the contrast adjustment curve, measured at the target brightness point (as controlled by Brightness parameter). The device supports a range of gradients from 0.5 to 2.0; Device represents this as a contrast range from 16 (0.5) to 64 (2.0).
	Saturation				0			255			128			kCameraSaturationID					2	 
	Hue						-180		180			0			kCameraHueID						3	Disabled
	Gain					32			255			32			kCameraGainID						6	Auto Exposition must be disabled
	Horizontal Flip			0			1			0			kCameraHFlipID						7	 
	Vertical Flip			0			1			0			kCameraVFlipID						8	 
	Auto Exposition			0			1			1			kCameraAutoExpositionID				11	 
	Auto White Balance		0			1			1			kCameraAutoWhiteBalanceID			12	 
	Camera Resolution		kQVGA		k4VGA		kQVGA		kCameraResolutionID					14	Not to be set manually
	Frames Per Second		1			30			5			kCameraFrameRateID					15	Not to be set manually
	Exposure (time[ms]=value/10)	1	2500(250ms)	NA			kCameraExposureID					17	Auto Exposition must be disabled otherwise display last value before auto exposure was activated. Once auto exposure disabled paremeter is set to the last value used by the camera internal algorithm
	Camera Select			0			1			0			kCameraSelectID						18	0: Top Camera; 1: Bottom Camera;
	Reset camera registers	0			1			0			kCameraSetDefaultParamsID			19	1: reset camera and reset parameter to 0
	Auto Exposure Algorithm	0			3			1			kCameraExposureAlgorithmID			22	0: Average scene Brightness; 1: Weighted average scene Brightness; 2: Adaptive weighted auto exposure for hightlights; 3: Adaptive weighted auto exposure for lowlights
	Sharpness				-1			7			0			kCameraSharpnessID					24	-1: disabled
	White Balance (Kelvin)	2700		6500		NA			kCameraWhiteBalanceID				33	Read only if Auto White Balance is enabled Read/Write if Auto White Balance is disabled
	Back light compensation	0			4			1			kCameraBacklightCompensationID		34
	*/

	cv::Mat getTransform(std::string chainName, int space); // For computing transforamtion matrix from one coordinate system to another

	struct QRcodeDetection qrCodeDetection(sensor_msgs::Image &frame_, zbar::ImageScanner &set_zbar, cv::Mat &robotToCameraMatrix); // For QRcode detection

	struct QRcodeHazardDetection openDoorDetection(std::vector< cv::Mat > &LandmarkInRobotCoordinate, std::vector<std::string> &QRmessage); // For Hazard detection while using QRcodes

	std::vector<double> compute_euler_x( std::vector<double> &m21, std::vector<double> &m22, std::vector<double> &euler_y); //For the computation of the 1-st euler angle
	std::vector<double> compute_euler_y(std::vector<double> &m20); //For the computation of the 2-nd euler angle
	std::vector<double> compute_euler_z(std::vector<double> &m10, std::vector<double> &m00, std::vector<double> &euler_y); //For the computation of the 3-rd euler angle

protected:
	// For QRcode detection:
	float landmarkTheoreticalSize;// = 0.16; //# QRcode real size in meters
	std::string currentQRcodeCamera;// = "CameraTop";
};
