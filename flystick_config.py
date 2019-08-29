"""
This "demo" configuration is for the most spartanly-named
"Thrustmaster USB Joystick" (http://www.thrustmaster.com/products/usb-joystick).
It was the cheapest joystick in my local electronics shop, and - as an added
bonus - it had just the throttle lever I wanted.
"""
from flystick_conf_models import *

throttles = Joystick(0)
joystick = Joystick(1)

if throttles.get_name() != "Thrustmaster Throttle - HOTAS Warthog":
    throttles = Joystick(1)
    joystick = Joystick(0)

# aileron trim, hat side-to-side axis
ail_trim = joystick.hat_switch(hat=0, axis=0, positions=41, initial=20)

# Raspberry Pi GPIO pin where to output the PPM signal.
# Pin map: http://wiki.mchobby.be/images/3/31/RASP-PIZERO-Correspondance-GPIO.jpg
# (Connect this pin to the RC transmitter trainer port.)
PPM_OUTPUT_PIN = 18

# Output (PPM) channels.
CHANNELS = (
    # channel 1: aileron with trim
    joystick.axis(0) + ail_trim * 0.5,
    # a more elaborate example with reverse, offset, weight and trim:
    #(-joystick.axis(0) + 0.1) * 0.7 + ail_trim * 0.5,
    # channel 2: elevator (reversed)
    -joystick.axis(1),
    # channel 3: throttle (reversed)
    -throttles.axis(2),
    -throttles.axis(0),
    # channel 4: flight mode
    # hat up-down axis, 5 states to match scrollphat vertical resolution
    joystick.hat_switch(hat=0, axis=1, positions=5),
    # channels 5-8: buttons demo
    joystick.button(0),
    joystick.button(1),
    joystick.button(2),
    joystick.button(3),
)

# dual-channel display component
stick_dot = XYDot(col=5)

# Render outputs (channels). One-to-one line match to CHANNELS.
DISPLAY = (
    # channel 1: dot horizontal axis
    stick_dot.horizontal(),
    # channel 2: dot vertical axis
    stick_dot.vertical(),
    # channel 3: throttle bar
    YBar(col=0, width=2),
    # channel 4: flight mode switch
    YDot(col=9),
    # channels 5-8: buttons demo
    Block(corner=(10, 0)),
    Block(corner=(10, 1)),
    Block(corner=(10, 2)),
    Block(corner=(10, 3)),
)

# TODO what's the range? 128? http://www.issi.com/WW/pdf/31FL3730.pdf
DISPLAY_BRIGHTNESS = 10
