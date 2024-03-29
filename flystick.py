#!/usr/bin/python
"""
flystick - python script to control an RC plane with a USB joystick.
Copyright (C) 2016 Janne Savukoski

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from flystick_config import (
    CHANNELS, DISPLAY, DISPLAY_BRIGHTNESS, PPM_OUTPUT_PIN, PWM_INITIAL_TRIM, PWM_DIFF, JOYSTICK_ROLL_TRIM_CHANNEL, JOYSTICK_PITCH_TRIM_CHANNEL, isLcd)

import logging
import pygame
import signal
import threading
import time
from lcd import LCD

try:
    import pigpio
except ImportError as e:
    logging.warn(e, exc_info=True)
    logging.warn("Failed to load pigpio library, running in debug mode")
    pigpio = None

_running = False

_output = ()

def shutdown(signum, frame):
    global _running
    _running = False


def main():
    global _output
    try:
        global lcd
        lcd = LCD()
    except:
        print("could not init lcd")

    pygame.init()

    # Reading only "clicks" via events. These are used for advanced
    # mappings. Events to avoid tracking state manually. Axes are read
    # by snapshotting.
    pygame.event.set_allowed([pygame.JOYBUTTONDOWN,
                              pygame.JOYHATMOTION])

    pi_gpio = 1 << PPM_OUTPUT_PIN

    if pigpio:
        pi = pigpio.pi()
        pi.set_mode(PPM_OUTPUT_PIN, pigpio.OUTPUT)
        pi.wave_add_generic([pigpio.pulse(pi_gpio, 0, 2000)])
        # padding to make deleting logic easier
        waves = [None, None, pi.wave_create()]
        pi.wave_send_repeat(waves[-1])
    else:
        pi = None

    prev = None
    prev_rll_trim = None
    prev_ptch_trim = None
    
    counter = 0
    while _running:
        # clicks for advanced mapping
        clicks, hats = [], []
        for evt in pygame.event.get():
            if evt.type == pygame.JOYBUTTONDOWN:
                # print "JOYBUTTONDOWN: %r\n%s" % (evt, dir(evt))
                clicks.append(evt)
            elif evt.type == pygame.JOYHATMOTION and any(evt.value):
                # print "JOYHATMOTION: %r\n%s" % (evt, dir(evt))
                hats.append(evt)

        # tuple to enforce immutability
        _output = tuple(max(min(ch((clicks, hats)), 1.), -1.)
                        for ch in CHANNELS)
        # rll_trim = _output[0] * PWM_DIFF + PWM_INITIAL_TRIM
        # ptch_trim = _output[1] * PWM_DIFF + PWM_INITIAL_TRIM
        rll_trim = int((_output[0] - _output[JOYSTICK_ROLL_TRIM_CHANNEL]) * 100) # convert to %
        ptch_trim = int((_output[1] - _output[JOYSTICK_PITCH_TRIM_CHANNEL]) * 100)

        # Update if changed trim
        try:
            if prev_rll_trim != rll_trim or prev_ptch_trim != ptch_trim:
                lcd.lcd_string("rll " + str(int(rll_trim)) + "%", lcd.LCD_LINE_1)
                lcd.lcd_string("ptch " + str(int(ptch_trim)) + "%", lcd.LCD_LINE_2)
        except:
            pass
        # if _output == prev:
        #     # do nothing
        #     pass
        #
        # elif pigpio:
        if pigpio:
            pulses, pos = [], 0
            index_tuple = 0
            for value in _output:
                # exclude 5,6 channels from being pwm channel
                if index_tuple == JOYSTICK_ROLL_TRIM_CHANNEL or index_tuple == JOYSTICK_PITCH_TRIM_CHANNEL and 0:
                    # do nothing, exclude 6th and 7th channels
                    pass
                else:
                    # calibrated with Taranis to [-99.6..0..99.4]
                    # us = int(round(750 + 300 * value))
                    us = int(round(PWM_INITIAL_TRIM/2 + PWM_DIFF/2 * value))
                    pulses += [pigpio.pulse(0, pi_gpio, 300),
                               pigpio.pulse(pi_gpio, 0, us - 300)]
                    pos += us
                index_tuple += 1

            # subcycle_time_us = 20k
            pulses += [pigpio.pulse(0, pi_gpio, 300),
                       pigpio.pulse(pi_gpio, 0, 20000 - 300 - pos - 1)]

            pi.wave_add_generic(pulses)
            waves.append(pi.wave_create())
            pi.wave_send_using_mode(waves[-1], pigpio.WAVE_MODE_REPEAT_SYNC)

            last, waves = waves[0], waves[1:]
            if last:
                pi.wave_delete(last)

        prev = _output
        prev_rll_trim = rll_trim
        prev_ptch_trim = ptch_trim
        # NO BUSYLOOPING. And locking with ``pygame.event.wait`` doesn't sound
        # very sophisticated. (At this point, at least.)
        # time.sleep(.02)

    if pi:
        pi.stop()


if __name__ == '__main__':
    _running = True
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    main()
