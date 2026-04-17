from enum import Enum


class State(Enum):
    IDLE = "idle"
    START = "start"
    WAIT_MATCH = "wait_match"
    WAIT_GET_CONTACT = "wait_get_contact"
    WAIT_INPUT_ORIGIN = "wait_input_origin"
    WAIT_INPUT_PIX_KEY = "wait_input_pix_key"
    WAIT_INPUT_VEHICLE = "wait_input_vehicle"
    WAIT_INPUT_PLATE = "wait_input_plate"
    WAIT_DRIVER_LOCATION = "wait_driver_location"
    WAIT_PASSENGER_LOCATION = "wait_passenger_location"
    WAIT_INPUT_DESTINATION = "wait_input_destination"
    WAIT_CODE_ACTIVATION = "wait_code_activation"
    WAIT_TWO_STEPS_VERIFICATION = "wait_two_steps_verification"
    WAIT_CONFIRM_ADDRESS = "wait_confirm_address"
    
    # Estados de Edição (Autônomos)
    EDIT_PIX = "edit_pix"
    EDIT_VEHICLE = "edit_vehicle"
