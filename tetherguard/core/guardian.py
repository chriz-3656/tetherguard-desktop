import enum

class GuardianState(enum.Enum):
    OFF = "OFF"
    ARMING = "ARMING"
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    DISARMING = "DISARMING"
    ERROR = "ERROR"

class GuardianMode:
    def __init__(self):
        self._state = GuardianState.OFF

    @property
    def state(self) -> GuardianState:
        return self._state

    def arm(self):
        if self._state in [GuardianState.OFF, GuardianState.ERROR]:
            self._state = GuardianState.ARMING
            # Transition to ACTIVE after detectors start successfully
            
    def activate(self):
        if self._state == GuardianState.ARMING:
            self._state = GuardianState.ACTIVE
            
    def trigger(self):
        if self._state == GuardianState.ACTIVE:
            self._state = GuardianState.TRIGGERED
            
    def disarm(self):
        self._state = GuardianState.DISARMING
        # Transition to OFF after detectors stop successfully
        
    def turn_off(self):
        self._state = GuardianState.OFF
        
    def set_error(self):
        self._state = GuardianState.ERROR
