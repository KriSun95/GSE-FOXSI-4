"""
A demo to walk through an existing CdTe raw file.
"""

import numpy as np
import time

import os.path

    
def fake_rtds(target_file, loops=1_000):
    """ 
    Generate fake RTD data and save to a `target_file`. 
    
    Structure 42-bytes (84 hex-digits long, values 1 or 2)
    first byte = chip
    second byte = buffer
    next four bytes = unixime
    after that there are 9 4-byte chunks, each for a separate RTD.
        first byte is the error (if 1 then good)
        second is the sign (+ve or -ve temp)
        last two are the temperature
    """

    if os.path.exists(target_file):
        os.remove(target_file)

    with open(target_file, "w") as file:
        f = fake_rtd()
        file.write(f)
        
    for _ in range(loops):
        with open(target_file, "a") as file:
            f = fake_rtd()
            file.write(f)
            time.sleep(0.5)
    

def fake_rtd():
    """ 
    Generate fake RTD frame. 
    
    Structure 42-bytes (84 hex-digits long, values 1 or 2)
    first byte = chip
    second byte = buffer
    next four bytes = unixime
    after that there are 9 4-byte chunks, each for a separate RTD.
        first byte is the error (if 1 then good)
        second is the sign (+ve or -ve temp)
        last two are the temperature
    """
    chip = '01' if np.random.rand()<0.5 else '02'
    buffer = '00'
    _t = int(time.time())
    unixtime = hex(_t)[2:].rjust(8,"0") # [2:] get rid of 0x

    
    temps_range = 100
    temps = ''
    for _ in range(9):
        error = '01' if np.random.rand()<0.99 else '3f'
        
        sign = '00' if np.random.rand()<0.8 else '01'
        _te = np.arange(0,temps_range)[np.random.randint(temps_range)] if np.random.rand()<0.99 else temps_range*10
        temp = hex(_te)[2:]
        temps += error + sign + temp.rjust(4,"0")
        assert len(error + sign + temp.rjust(4,"0"))==8

    assert len(chip)==2
    assert len(buffer)==2
    assert len(unixtime)==8
    
    return chip + buffer + unixtime + temps

if __name__=="__main__":
    import os
    # package top-level
    DATAFILE = os.path.dirname(os.path.realpath(__file__)) + "/../../../fake_temperatures.txt"
    fake_rtds(DATAFILE, loops=5)
    # print(fake_rtd())
    # print("0200000000010000220dc0f0200080f8340081f8340080f02000c2f0200081f8300080f0200081f83400")