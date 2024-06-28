from enum import Enum, auto


class State(Enum):
    START = auto()
    WAIT_MATCH = auto()
    WAIT_GET_CONTACT = auto()
    WAIT_INPUT_ORIGIN = auto()
    WAIT_INPUT_PIX_KEY = auto()
    WAIT_INPUT_VEHICLE = auto()
    WAIT_INPUT_PLATE = auto()
    WAIT_DRIVER_LOCATION = auto()
    WAIT_PASSENGER_LOCATION = auto()
    WAIT_INPUT_DESTINATION = auto()
    WAIT_CODE_ACTIVATION = auto()
    WAIT_TWO_STEPS_VERIFICATION = auto()
