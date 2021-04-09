# SPDX-FileCopyrightText: 2021 Kevin Matocha
#
# SPDX-License-Identifier: MIT
"""
Example of the Annotation widget to annotate a Switch widget or
for freeform annotation.
"""

import time
import board
import displayio
import adafruit_touchscreen
from adafruit_displayio_layout.widgets.switch_round import SwitchRound as Switch
from adafruit_displayio_layout.widgets.annotation import Annotation

display = board.DISPLAY

ts = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XL,
    board.TOUCH_XR,
    board.TOUCH_YD,
    board.TOUCH_YU,
    calibration=((5200, 59000), (5800, 57000)),
    size=(display.width, display.height),
)

# Create the switch widget
my_switch = Switch(190, 50)

# Create several annotations

# This annotation is positioned relative to the switch widget, with default values.
switch_annotation = Annotation(
    widget=my_switch,  # positions are relative to the switch
    text="Widget Annotation: Switch",
)

# This annotation is positioned relative to the switch widget, with the line
# going in the downard direction and anchored at the middle bottom of the switch.
# The position is "nudged" downward using ``position_offset`` to create a 1 pixel
# gap between the end of the line and the switch.
# The text is positioned under the line by setting ``text_under`` to True.
switch_annotation_under = Annotation(
    widget=my_switch,  # positions are relative to the switch
    text="Annotation with: text_under = True",
    delta_x=-10,
    delta_y=15,  # line will go in downward direction (positive y)
    anchor_point=(0.5, 1.0),  # middle, bottom of switch
    position_offset=(0, 1),  # nudge downward by one pixel
    text_under=True,
)

# This is a freeform annotation that is positioned using (x,y) values at the bottom, right
# corner of the display (display.width, display.height).
# The line direction is
freeform_annotation = Annotation(
    x=display.width,  # uses freeform (x,y) position
    y=display.height,
    text="Freeform annotation (display.width, height)",
)

my_group = displayio.Group(max_size=4)
my_group.append(my_switch)
my_group.append(switch_annotation)
my_group.append(switch_annotation_under)
my_group.append(freeform_annotation)

# Add my_group to the display
display.show(my_group)

# Start the main loop
while True:

    p = ts.touch_point  # get any touches on the screen

    if p:  # Check each switch if the touch point is within the switch touch area
        # If touched, then flip the switch with .selected
        if my_switch.contains(p):
            my_switch.selected(p)

    time.sleep(0.05)  # touch response on PyPortal is more accurate with a small delay
