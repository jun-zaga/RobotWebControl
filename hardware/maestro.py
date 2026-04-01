import serial
from sys import version_info

PY2 = version_info[0] == 2


class Controller:
    def __init__(self, ttyStr="/dev/ttyACM0", device=0x0C):
        self.usb = serial.Serial(ttyStr)
        self.PololuCmd = chr(0xAA) + chr(device)
        self.Targets = [0] * 24
        self.Mins = [0] * 24
        self.Maxs = [0] * 24

    def close(self):
        self.usb.close()

    def sendCmd(self, cmd):
        cmdStr = self.PololuCmd + cmd
        if PY2:
            self.usb.write(cmdStr)
        else:
            self.usb.write(bytes(cmdStr, "latin-1"))

    def setRange(self, chan, min_val, max_val):
        self.Mins[chan] = min_val
        self.Maxs[chan] = max_val

    def setTarget(self, chan, target):
        if self.Mins[chan] > 0 and target < self.Mins[chan]:
            target = self.Mins[chan]
        if self.Maxs[chan] > 0 and target > self.Maxs[chan]:
            target = self.Maxs[chan]

        lsb = target & 0x7F
        msb = (target >> 7) & 0x7F
        cmd = chr(0x04) + chr(chan) + chr(lsb) + chr(msb)
        self.sendCmd(cmd)
        self.Targets[chan] = target

    def setSpeed(self, chan, speed):
        lsb = speed & 0x7F
        msb = (speed >> 7) & 0x7F
        cmd = chr(0x07) + chr(chan) + chr(lsb) + chr(msb)
        self.sendCmd(cmd)

    def setAccel(self, chan, accel):
        lsb = accel & 0x7F
        msb = (accel >> 7) & 0x7F
        cmd = chr(0x09) + chr(chan) + chr(lsb) + chr(msb)
        self.sendCmd(cmd)