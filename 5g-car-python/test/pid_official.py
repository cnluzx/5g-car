import cv2
import random
import numpy as np
import time
import pigpio as pio
import os
import keyboard
from threading import Timer

import threading#多线程



kp = 0.25 
kd =0.11  

last_error=0
error=0 
#限幅
angle_outmax=25
angle_outmin=-45  

cap= cv2.VideoCapture(0)

servo_pin=12

servo= pio.pi()
def set_duo(angle):
    # 限制角度范围
        angle = max(0, min(180, angle))

        # 0° → 500us ，180° → 2500us
        pulsewidth = 500 + (angle / 180.0) * 2000  

        print(f"[Dian_Duo] 舵机角度: {angle}°, 脉宽: {pulsewidth}us")

        servo.set_servo_pulsewidth(12, pulsewidth)

#---------------------------------------------------------
#GPIO初始化


time.sleep(2)

def main():
  while(cap.isOpened()):
    ret, img = cap.read()
    k = cv2.waitKey(1)
    img_=cv2.resize(img,(600,400))
    img1 = cv2.cvtColor(img_, cv2.COLOR_BGR2GRAY)
  
    ret,binary = cv2.threshold(img1,200,255,0)#阈值处理
    kerne = cv2.getStructuringElement(cv2.MORPH_RECT,(35,1)) #横线检测
    blackhatImg = cv2.morphologyEx(img1,cv2.MORPH_BLACKHAT,kerne) #黑帽
    image_1 = cv2.Canny(blackhatImg, 150,255)
    #cv2.imshow("3",image_1)
    t = 0
    left = [-1 for i in range(0,100)]
    right = [-1 for i in range(0,100)]
    mid = [-1 for i in range(0,100)]
    mid_sum = 0
    left[0]=0
    right[0]=0
    cv2.line(img1,(0,370),(600,370),(0,0,255),2)
    cv2.line(img1,(0,270),(600,270),(0,0,255),2)
    
    for i in range(370,270,-1):
        flag_left=0
        flag_right=0  
        for z in range(0,600):
            if(image_1[i][z]==255):
                flag_left=1
                #cv2.circle(img1, (z,i),1,(255,0,0),1)
                left[t] = z #假设为左边线
                for j in range(z,600):
                    if((image_1[i][j]==255)and(j-z>100)):
                        flag_right=1
                        right[t] = j
                        #cv2.circle(img1, (j,i),1, (255,0,0),1)
                        break
                break

            if(flag_left==0):
                left[t] = 0
                #cv2.circle(img1, (left[t],i),1, (255,0,0),1)
                right[t] = 599
                #cv2.circle(img1, (right[t],i),1, (255,0,0),1)
            
            if(flag_left==1 and flag_right==0):
                right[t] = 599  
       
        if(t>0):
            if(flag_right==0):
                if(left[t-1]-left[t]>0):
                    n = left[t-1]
                    left[t-1]=599-right[t-1]
                    right[t-1]=n
                    #cv2.circle(img1, (left[t-1],i),1, (255,0,0),1)
                #else:
                    #cv2.circle(img1, (right[t-1],i),1, (255,0,0),1)


            mid[t-1] = (left[t-1]+right[t-1])/2
            mid_sum = mid[t-1] + mid_sum
        t = t + 1
    mid_final = mid_sum/100

    global kp
    global kd
    global last_error
    global error
	
    error=mid_final-300 
    error_angle = kp*error + kd*(error-last_error)
	
    if(error_angle>angle_outmax):
      error_angle=angle_outmax
    if(error_angle<angle_outmin):
      error_angle=angle_outmin
	
    angle=85-error_angle 
    print(mid_final,        error,         error_angle,        angle)#打印赛道中线，赛道中线与图像偏差，角度偏差，角度        
    last_error = error
    set_duo(angle) 
    time.sleep(1)