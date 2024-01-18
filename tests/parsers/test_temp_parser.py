"""
Aim: 
----

This is 37 bytes long. The first byte will be a 1 or a 2 indicating 
which of two temperature sensor chips sent the data. After that, there 
are nine sensors read out, each has 4 bytes of data. So you can start 
the parse by stripping off byte 1, then splitting the remaining message 
into groups of 4 bytes.

For a given measurement (4 bytes wide), the first byte indicates errors. 
See page 20 of this PDF. If there is no error, the first byte == 1 . If 
it has a different value, there is no need to try to plot that measurement. 
The remaining three bytes of a measurement store the temperature data (see 
the same PDF page 20). If the leading bit is a 1, the value is negative. 
In these remaining three bytes, there is a decimal place 9 digits from the 
right. To implement all this, you can do something like this to the 3 bytes 
of temperature data:

1. Check the leftmost bit (if value & 0x800000, is_negative = 1 if you store 
    value as an int). If is 1, remember to add a minus in front of your 
    temperature later, and set value = value - 0x800000 to avoid making an 
    enormous number when you convert, if it is negative.

2. Make a float: temperature_c = (1 - 2*is_negative)*value / 1024.0 and send 
    that to plot somewhere. I think you should divide by 1024. It could be 
    bigger or smaller.

3. (Do this again for the remaining 8 sensor measurements).
"""


import numpy as np

import FoGSE.parsers.temp_parser as tp


EXAMPLE_ERROR0 = "01"
EXAMPLE_MEASUREMENT0 = "0065b2"

EXAMPLE_FRAME0 = "0200000000010000220dc0f0200080f8340081f8340080f02000c2f0200081f8300080f0200081f83400" # no valid entries
EXAMPLE_FRAME1 = "010000000003010065b2c0f0200080f8340081f8340080f02000c2f0200081f8300080f0200081f83400" # first temp. sensor should be 25.423828125 C


def test_temp_sensor_parser():
    """ Test for `temp_sensor_parser`. """

    assert np.isclose(tp.get_temp(EXAMPLE_MEASUREMENT0), 25.423828125), "Fail: `temp_sensor_parser` mismatch." # C

if __name__=="__main__":
    
    # temp_sensor_parser("010065b2") # == 25.423828125 C
    test_temp_sensor_parser()