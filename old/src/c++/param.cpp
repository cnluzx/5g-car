////param  parameters  参数

#include "param.h" 
#include <stdio.h>

#include <pthread.h>
#include <sys/stat.h>
#include <unistd.h>

#include <vector>
#include <fstream>
#include <cstdlib>
#include <sstream>
#include <cstring>
#include <chrono>

#include <iostream>
#include<stdlib.h>
#include <thread>
#include <condition_variable>
#include <mutex>

#include <cmath>
#include <csignal>
// #include <portaudio.h>
// #include <opencv4/opencv2/opencv.hpp>
// #include <opencv4/opencv2/highgui/highgui.hpp>
// #include <opencv4/opencv2/imgproc/imgproc.hpp>
// #include<opencv4/opencv2/core/core.hpp>
// #include<opencv4/opencv2/imgproc/types_c.h>
// #include <AL/al.h>
// #include <AL/alc.h>
//#include <numpy/arrayobject.h>

// #include "pigpio.h"


using namespace cv;
using namespace std;
using namespace std::chrono;

// add.h
#ifndef ADD_H
#define ADD_H
#define PI 3.1415926