'''
Created on Jan 3, 2016
@author: graysonelias
'''

'''
This module provides some of our standard methods.
'''

import constants as c

from wallaby import ao
from wallaby import msleep
from wallaby import digital
from wallaby import seconds
from wallaby import freeze
from wallaby import set_servo_position
from wallaby import get_servo_position
from wallaby import analog
from wallaby import gyro_y

from logger import log as display

# Servo Constants
DELAY = 10
# Loop break timers #
time = 0  # This represents how long to wait before breaking a loop.


#Causes the robot to stop until the right button is pressed
def wait_for_button():
    display ("Press Button...")
    while not digital(c.RIGHT_BUTTON):
        pass
    msleep(1)
    display ("Pressed")
    msleep(1000)


#Causes the robot to stop
def DEBUG():
    freeze(c.LMOTOR)
    freeze(c.RMOTOR)
    ao()
    display ('Program stop for DEBUG\nSeconds: {}'.format(seconds() - c.startTime))
    display ("NOTE: {}\t{}".format(seconds(), c.startTime))
    exit(0)


#Causes the robot to stop and hold its position for 5 seconds
def DEBUG_WITH_WAIT():
    freeze(c.LMOTOR)
    freeze(c.RMOTOR)
    ao()
    msleep(5000)
    display ('Program stop for DEBUG\nSeconds: {}'.format(seconds() - c.startTime))
    exit(0)


#Checks to see if all of the servos, motors, and sensors are working properly
def start_up_test():
    DEBUG()
# Servo Control #
# Moves a servo with increment "speed".


def move_servo(servo, endPos, speed=10):
    # speed of 1 is slow
    # speed of 2000 is fast
    # speed of 10 is the default
    now = get_servo_position(servo)
    if speed == 0:
        speed = 2047
    if endPos > 2040:
        display("using 2040")
        endPos = 2040
    if endPos < 5:
        display("using 5")
        endPos = 5
    if now > endPos:
        speed = -speed
    for i in range(int(now), int(endPos), int(speed)):
        set_servo_position(servo, i)
        msleep(DELAY)
    set_servo_position(servo, endPos)
    msleep(DELAY)

# Moves a servo over a specific time.

def move_servo_timed(servo, endPos, time):
    if time == 0:
        speed = 2047
    else:
        speed = abs((DELAY * (get_servo_position(servo) - endPos)) / time)
    move_servo(servo, endPos, speed)


def move_two_servos_timed(servo1, endPos1, servo2, endPos2, time):
    if time == 0:
        speed = 2047
    else:
        delta1 = endPos1 - get_servo_position(servo1)
        delta2 = endPos2 - get_servo_position(servo2)
        speed1 = (DELAY * delta1) / time
        speed2 = (DELAY * delta2) / time
        moves = delta1 / speed1
        for x in range(1, abs(int(moves))):
            set_servo_position(servo1, get_servo_position(servo1) + speed1 * x)
            set_servo_position(servo2, get_servo_position(servo2) + speed2 * x)
            msleep(DELAY)
        set_servo_position(servo1, endPos1)
        set_servo_position(servo2, endPos2)

# Sets wait time in seconds before breaking a loop.
def set_wait(DELAY):
    global time
    time = seconds() + DELAY

# Used to break a loop after using "setWait". An example would be: setWiat(10) | while true and getWait(): do something().


def get_wait():
    return seconds() < time


def wait_4_light(ignore=False):
    if ignore:
        wait_for_button()
        return
    while not calibrate(c.STARTLIGHT):
        pass
    _wait_4(c.STARTLIGHT)

from wallaby import left_button, right_button


def calibrate(port):
    display ("Press LEFT button with light on")
    while not left_button():
        pass
    while left_button():
        pass
    lightOn = analog(port)
    display ("On value =" + str(lightOn))
    if lightOn > 200:
        display ("Bad calibration")
        return False
    msleep(1000)
    display ("Press RIGHT button with light off")
    while not right_button():
        pass
    while right_button():
        pass
    lightOff = analog(port)
    display ("Off value =" + str(lightOff))
    if lightOff < 3000:
        display ("Bad calibration")
        return False

    if (lightOff - lightOn) < 2000:
        display("Bad calibration")
        return False
    c.startLightThresh = (lightOff - lightOn) / 2
    display ("Good calibration! " + str(c.startLightThresh))
    return True


def _wait_4(port):
    display ("waiting for light!! ")
    while analog(port) > c.startLightThresh:
        pass


def move_bin(armIn, speed=10): # 1263
    if armIn < 5:
        armEnd = 5
    elif armIn > 2040:
        armEnd = 2040
    else:
        armEnd = armIn

    joint_start = get_servo_position(c.SERVO_JOINT) # 1750
    arm_start = get_servo_position(c.SERVO_BIN_ARM) # 700
    delta = armEnd - arm_start # 563

    for shift in range(0, abs(delta), speed):
        if delta < 0:
            shift = -shift # handles negative values (moving bin downwards)
        set_servo_position(c.SERVO_BIN_ARM, arm_start + shift)
        set_joint = joint_start + shift
        if set_joint > 1900:
            set_joint = 1900
            # return
        elif set_joint < 5:
            set_joint = 5
            # return
        set_servo_position(c.SERVO_JOINT, set_joint)

        display ("{}\t{}".format(get_servo_position(c.SERVO_JOINT), get_servo_position(c.SERVO_BIN_ARM)))

        msleep(DELAY)
    set_joint = joint_start + delta
    if set_joint > 1900:
        set_joint = 1900
    elif set_joint < 5:
        set_joint = 5
    set_servo_position(c.SERVO_BIN_ARM, armEnd)
    set_servo_position(c.SERVO_JOINT, set_joint)

def shutdown():
    freeze(c.LMOTOR)
    freeze(c.RMOTOR)
    ao()
    display ('Program stopped\nSeconds: {}'.format(seconds() - c.startTime))
    exit(0)


def found_bump():
    return gyro_y() < -c.THRESHOLD_GYRO


def on_black_back():
    return analog(c.BACK_TOPHAT) > c.THRESHOLD_TOPHAT


def on_black_front():
    return analog(c.FRONT_TOPHAT) > c.THRESHOLD_TOPHAT

def lost_ramp():
    return analog(c.ET) < c.THRESHOLD_ET