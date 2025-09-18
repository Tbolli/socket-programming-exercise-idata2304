# Business logic for the smart tv
class SmartTV:
    def __init__(self, available_channels):
        self.is_on = False
        self.available_channels = available_channels
        self.active_channel = 1
    
    def turnOn(self):
        if self.is_on:
            return False, "Smart TV is already turned on"
        self.is_on = True
        return True, "Smart TV is turned on"
    
    def turnOff(self):
        if not self.is_on:
            return False, "Smart TV is already turned off"
        self.is_on = False
        return True, "Smart TV is turned off"
    
    def getNumberOfChannels(self):
        if not self.is_on:
            return False, "Smart TV is off | Unable to complete this request"
        return True, f"Total number of channels: {self.available_channels}"

    def getChannel(self):
        if not self.is_on:
            return False, "Smart TV is off | Unable to complete this request"
        return True, f"Active channel: {self.active_channel}"
    
    def setChannel(self, channel: int):
        if not self.is_on:
            return False, "Smart TV is off | Unable to complete this request"
        if channel < 1 or channel > self.available_channels:
            return False, f"Channel {channel} is out of range, valid range: 1-{self.available_channels}"
        self.active_channel = channel
        return True, f"Active channel set to: {channel}"
    
    def downChannel(self):
        if self.active_channel == 1:
            return False, "Channel cannot go any lower than channel 1"
        self.active_channel -= 1
        return True, f"Channel went down to {self.active_channel}"
    
    def upChannel(self):
        if self.active_channel == self.available_channels:
            return False, f"Channel cannot go any higher than channel {self.available_channels}"
        self.active_channel += 1
        return True, f"Channel went up to {self.active_channel}"