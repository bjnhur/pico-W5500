# SPDX-FileCopyrightText: 2021 Kevin Matocha
#
# SPDX-License-Identifier: MIT
#############################
"""
This is a basic demonstration of a Dial widget.
"""

import time
import board
import displayio
import terminalio
from adafruit_displayio_layout.widgets.dial import Dial

# Fonts used for the Dial tick labels
tick_font = terminalio.FONT

display = board.DISPLAY  # create the display on the PyPortal or Clue (for example)
# otherwise change this to setup the display
# for display chip driver and pinout you have (e.g. ILI9341)


# Define the minimum and maximum values for the dial
minimum_value = 0
maximum_value = 100

# Create a Dial widget
my_dial = Dial(
    x=20,  # set x-position of the dial inside of my_group
    y=20,  # set y-position of the dial inside of my_group
    width=180,  # requested width of the dial
    height=180,  # requested height of the dial
    padding=25,  # add 25 pixels around the dial to make room for labels
    start_angle=-120,  # left angle position at -120 degrees
    sweep_angle=240,  # total sweep angle of 240 degrees
    min_value=minimum_value,  # set the minimum value shown on the dial
    max_value=maximum_value,  # set the maximum value shown on the dial
    tick_label_font=tick_font,  # the font used for the tick labels
    tick_label_scale=2.0,  # the scale factor for the tick label font
)

my_group = displayio.Group(max_size=1)
my_group.append(my_dial)

display.show(my_group)  # add high level Group to the display

step_size = 1

while True:

    # run the dial from minimum to maximum
    for this_value in range(minimum_value, maximum_value + 1, step_size):
        my_dial.value = this_value
        display.refresh()  # force the display to refresh
    time.sleep(0.5)

    # run the dial from maximum to minimum
    for this_value in range(maximum_value, minimum_value - 1, -step_size):
        my_dial.value = this_value
        display.refresh()  # force the display to refresh
    time.sleep(0.5)
