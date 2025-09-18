# Message class to carry information to the server
class Message:
    def __init__(self, success: bool, message: str):
        self.success
        self.message

# Business logic for the smart tv
class SmartTV:
    def __init__(self, available_channels):
        self.is_on = False
        self.available_channels = available_channels
        self.active_channel = 1
    
    def turnOn(self) -> Message:
        if self.is_on:
            return Message(False, "Smart TV is already turned on")
        self.is_on = True
        return Message(True, "Smart TV is turned on")
    
    def turnOff(self) -> Message:
        if not self.is_on:
            return Message(False, "Smart TV is already turned off")
        self.is_on = False
        return Message(True, "Smart TV is turned off")
        
    def getNumberOfChannels(self) -> Message:
        if not self.is_on:
            return Message(False, "Smart TV is off | Unable to complete this request")
        return Message(True, f"Total number of channels: {self.available_channels}")

    def getChannel(self) -> Message:
        if not self.is_on:
            return Message(False, "Smart TV is off | Unable to complete this request")
        return self.active_channel
    
    def setChannel(self, channel: int) -> Message:
        if not self.is_on:
            return Message(False, "Smart TV is off | Unable to complete this request")
        if channel > self.available_channels:
            return Message(False, f"Channel {channel} is out of range, valid range: 1-{self.available_channels}")
        self.active_channel = channel
        return Message(True, f"Active channel set to: {channel}")