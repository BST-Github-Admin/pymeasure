#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Parker classes -- Motor controller
#
# automate Python package
# Authors: Colin Jermain, Graham Rowlands
# Copyright: 2014 Cornell University
#
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from automate.instruments import Instrument, SerialAdapter, RangeException
from time import sleep
import re

class ParkerGV6(Instrument):
    """ Represents the Parker Gemini GV6 Servo Motor Controller
    and provides a high-level interface for interacting with
    the instrument    
    """
    
    degreesPerCount = 0.00045 # 90 deg per 200,000 count
    
    def __init__(self, port):
        super(ParkerGV6, self).__init__(
            SerialAdapter(port, 9600, timeout=0.5),
            "Parker GV6 Motor Controller"
        )
        self.setDefaults()
             
    def setDefaults(self):
        """ Sets up the default values for the motor, which
        is run upon construction        
        """
        self.setEcho(False)
        self.setHardwareLimits(False)
        self.setAbsolutePosition()
        self.setAverageAcceleration(1)
        self.setAcceleration(1)
        self.setVelocity(3)
        
    def reset(self):
        """ Resets the motor controller while blocking and 
        (CAUTION) resets the absolute position value of the motor
        """
        self.write("RESET")
        sleep(5)
        self.setDefault()
        self.enable()
        
    def enable(self):
        """ Enables the motor to move """
        self.write("DRIVE1")
        
    def disable(self):
        """ Disables the motor from moving """
        self.write("DRIVE0")
    
    def status(self):
        """ Returns a list of the motor status in readable format """
        return self.ask("TASF").split("\r\n\n")
        
    def isMoving(self):
        """ Returns True if the motor is currently moving """
        return self.getPosition() == None
        
    def getAngle(self):
        """ Returns the angle in degrees based on the position
        and whether relative or absolute positioning is enabled,
        returning None on error        
        """
        position = self.getPosition()
        if position != None:
            return position*self.degreesPerCount
        else:
            return None

    def getAngleError(self):
        """ Returns the angle error in degrees based on the
        position error, or returns None on error        
        """
        positionError = self.getPositionError()
        if positionError != None:
            return positionError*self.degreesPerCount
        else:
            return None
            
    def setAngle(self, angle):
        """ Gives the motor a setpoint in degrees based on an
        angle from a relative or absolution position
        """
        self.setPosition(int(angle*self.degreesPerCount**-1))
        
    def getPosition(self):
        """ Returns an integer number of counts that correspond to
        the angular position where 1 revolution equals 4000 counts        
        """
        match = re.search(r'(?<=TPE)-?\d+', self.ask("TPE"))
        if match == None:
            return None
        else:
            return int(match.group(0))
            
    def getPositionError(self):
        """ Returns the error in the number of counts that corresponds
        to the error in the angular position where 1 revolution equals
        4000 counts        
        """
        match = re.search(r'(?<=TPER)-?\d+', self.ask("TPER"))
        if match == None:
            return None
        else:
            return int(match.group(0))
        
    def setPosition(self, counts): # in counts: 4000 count = 1 rev
        """ Gives the motor a setpoint in counts where 4000 counts
        equals 1 revolution
        """
        self.write("D" + str(int(counts)))
    
    def move(self):
        """ Initiates the motor to move to the setpoint """
        self.write("GO")
        
    def stop(self):
        """ Stops the motor during movement """
        self.write("S")
        
    def kill(self):
        """ Stops the motor """
        self.write("K")
        
    def setAbsolutePosition(self):
        """ Sets the motor to accept setpoints from an absolute
        zero position
        """
        self.write("MA1")
        self.write("MC0")
        
    def setRelativePosition(self):
        """ Sets the motor to accept setpoints that are relative
        to the last position
        """
        self.write("MA0")
        self.write("MC0")
        
    def setHardwareLimits(self, enable=False):
        """ Enables (True) or disables (False) the hardware
        limits for the motor
        """
        if enable:
            self.write("LH1")
        else:
            self.write("LH0")
            
    def setSoftwareLimits(self, positive, negative):
        """ Sets the software limits for motion based on
        the count unit where 4000 counts is 1 revolution
        """
        self.write("LSPOS%d" % int(positive))
        self.write("LSNEG%d" % int(negative))
    
    def setEcho(self, enable=False):
        """ Enables (True) or disables (False) the echoing
        of all commands that are sent to the instrument        
        """
        if enable:
            self.write("ECHO1")
        else:
            self.write("ECHO0")
        
    def setAcceleration(self, acceleration):
        """ Sets the acceleration setpoint in revolutions per second 
        squared
        """
        self.write("A" + str(float(acceleration)))
        
    def setAverageAcceleration(self, acceleration):
        """ Sets the average acceleration setpoint in revolutions
        per second squared
        """
        self.write("AA" + str(float(acceleration)))
        
    def setVelocity(self, velocity): # in revs/s
        """ Sets the velocity setpoint in revolutions per second """
        self.write("V" + str(float(velocity)))
        
    def write(self, command):
        """ Overwrites the Insturment.write command to provide the correct
        line break syntax
        """
        self.connection.write(command + "\r")
        
    def read(self):
        """ Overwrites the Instrument.read command to provide the correct
        functionality        
        """
        return re.sub(r'\r\n\n(>|\?)? ', '', "\n".join(self.readlines()))