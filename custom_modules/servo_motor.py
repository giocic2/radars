# SG90 Servo Motor (Micro Servo 9g)
import RPi.GPIO as GPIO
import time

def define_PWM_pin(pinNumber: int, PWM_frequency: int):
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pinNumber, GPIO.OUT)
    servoMotor = GPIO.PWM(pinNumber, PWM_frequency)
    servoMotor.start(0) # Duty cycle set to "0" at start.
    return servoMotor

def rotate_servo_to_angle(servoMotor, beamAngle: float):
    MAX_ANGLE = +90
    MAX_ANGLE_DUTY_CYCLE = 2
    MIN_ANGLE = -90
    MIN_ANGLE_DUTY_CYCLE = 12
    dutyCycle = (beamAngle - MIN_ANGLE) / (MAX_ANGLE - MIN_ANGLE) * (MIN_ANGLE_DUTY_CYCLE - MAX_ANGLE_DUTY_CYCLE) + MAX_ANGLE_DUTY_CYCLE
    servoMotor.ChangeDutyCycle(dutyCycle)
    time.sleep(0.5)
    servoMotor.ChangeDutyCycle(0) # To avoid servo jitter.
    

def shut_down_servo(servoMotor):
    servoMotor.stop()
    GPIO.cleanup()

if __name__ == "__main__":
    print("Standalone script not yet developed.")