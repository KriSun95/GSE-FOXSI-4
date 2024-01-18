import os
import struct

import numpy as np
import polars as pl
import pandas as pd
import logging

FILE_DIR = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(filename=FILE_DIR+"/../../temp_parser.log", encoding='utf-8', level=logging.DEBUG)


def chop_string(raw_string, seg_len):
    """ 
    Split `raw_string` into segments `seg_len` long. 
    
    Ignore remainders. 
    """
    groups = [raw_string[i:i+seg_len] for i in range(0,len(raw_string),seg_len)]

    if len(groups)==0:
        return groups 
    
    return groups if len(groups[-1])==seg_len else groups[:-1]

def rtdparser(file_raw):
    """ 
    Designed to split the file data into 42-byte frames and pass each of 
    them off to `temp_frame_parser`.
    
    Parameters
    ----------
    file_raw : `str`
        The raw file (N times 42-byte long) which contains the chip and temperature 
        frame information for N measurements.

    Returns
    -------
    List of (`numpy.ndarray`, `numpy.ndarray`) : 
        list of temperature information with each row containing a measurements 
        temeprature and error information. First, the temperature values from 
        the frame for each temperature sensor and, secondly, another array 
        containing strings of any error codes for each sensor in the same 
        structure.
    """

    if len(file_raw)<1:
        print("No data given to parser.")
        return polar_struct([[0]]*19, dttype=pl.Float32), polar_struct([['0']]*19, dttype=pl.Utf8)

    # convert from binary to hex
    byte_array = bytearray(file_raw)
    hex_string = ''.join(struct.pack('B', x).hex() for x in byte_array)

    # split raw data into 42-byte long frames (2 entries per byte=84)
    # work from the end, depending on backward buffer might cut off start
    frames_r = chop_string(raw_string=hex_string[::-1], seg_len=84)

    # run through each frame and reverse internally then externally to 
    # get in the correct written order
    frames = [f[::-1] for f in frames_r][::-1]

    if len(frames)<1:
        print("No data from parser.")
        return polar_struct([[0]]*19, dttype=pl.Float32), polar_struct([['0']]*19, dttype=pl.Utf8)

    # run through and process each read frame
    times = []
    read_frames_data = np.full((18,len(frames)), np.nan)
    read_frames_error = np.full((18,len(frames)), ' '*8)
    for c,frame in enumerate(frames):
        time, data, error = temp_frame_parser(frame)
        times.append(time)
        read_frames_data[:,c] = data
        read_frames_error[:,c] = error

    df = polar_struct([times,*list(read_frames_data)], dttype=pl.Float32)
    df_err = polar_struct([times,*list(read_frames_error)], dttype=pl.Utf8)
        
    logging.info(f'{times}\n{read_frames_data}\n')
    logging.error(f'{read_frames_error}\n\n')

    return df, df_err

def numpy_struct(sensor_value_fmt, num, _default_fill=np.nan):
    """ 
    Function to set-up a Numpy structured array to be filled with values 
    obtained from the temeprature readout.
    
    Parameters
    ----------
    sensor_value_fmt : `str`
        A string to indicate the format of the temperature information. 
        E.g., if floats represent the information then a 32-bit floating-point
        number ay be reasonable (i.e., 'f4') or, for error information then
        a string of 16 characters may be useful (i.e., '<U16').

    _default_fill : any Numpy compatible value
        The default entry value for the array.
        Default: `numpy.nan`

    Returns
    -------
    `int`, `list`, `list`: 
        The time, temperature information, and error information.
    """

    # 9 temperature sensors for each chip
    temp_sensors = ['ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8', 'ts9', 'ts10', 'ts11', 'ts12', 'ts13', 'ts14', 'ts15', 'ts16', 'ts17']
    temp_sensor_fmt = [f"({num},){sensor_value_fmt}"]*18 #

    # create dtypes
    dt = np.dtype({'names':('ti', *temp_sensors),
                   'formats':(f'({num},)i4', *temp_sensor_fmt)}) # u1==np.uint8,u4==np.uint32, i4==int32
    
    return np.full(10, _default_fill, dtype=dt)[0]

def polar_struct(data, dttype=pl.Float32):
    """ 
    Function to set-up a Polars dataframe to be filled with values 
    obtained from the temeprature readout.
    
    Parameters
    ----------
    data : `list`
        The list of temperature arrays.

    dttype : `polars.dtype`
        The type of the temperature information.
        Default: `polars.Float32`

    Returns
    -------
    `polars.DataFrame`: 
        The time, temperature information.
    """

    # 9 temperature sensors for each chip
    temp_sensors = ['ts0', 'ts1', 'ts2', 'ts3', 'ts4', 'ts5', 'ts6', 'ts7', 'ts8', 'ts9', 'ts10', 'ts11', 'ts12', 'ts13', 'ts14', 'ts15', 'ts16', 'ts17']

    return pl.DataFrame(dict(zip(['ti', *temp_sensors], data)), schema={"ti": pl.Int32, **dict.fromkeys(temp_sensors, dttype)})

def temp_frame_parser(frame):
    """
    Function to parse a single raw temperature frame and return the 
    temeprature values and error information.
    
    Parameters
    ----------
    frame : `str`
        The raw frame (42-bit long) which contains the chip and temperature 
        frame information.

    Returns
    -------
    (`numpy.ndarray`, `numpy.ndarray`) : 
        First, the temperature values from the frame for each temperature 
        sensor and, secondly, another array containing strings of any error 
        codes for each sensor in the same structure.
    """

    _chip = int(frame[:2])#.replace(b'\\x', b''))#
    s_no = 0 if _chip==1 else 9

    _ = frame[2:4]

    _time = int(frame[4:12],16)

    # get the 9 sensors' bytes and separate them
    _sensors = frame[12:]
    _sensors_sep = chop_string(raw_string=_sensors, seg_len=8)
    
    # for each temp. sensor, check the error message and assign to array
    temp_info, temp_error_info = [np.nan]*18, [np.nan]*18
    for t in range(len(_sensors_sep)):
        _err, _msrmt = temp_sensor_parser(_sensors_sep[t])
        if ((_err==b'01') or (_err=='01')) and s_no == 9:
            # if error is '01' then good data 
            # temp_info[s_no+t] = (get_temp(_msrmt))
            temperature = (get_temp(_msrmt))
            temperature_gt10 = temperature if temperature>10 else np.nan
            temp_info[s_no+t] = temperature_gt10
        else:
            # else just record the sensors raw byte string
            temp_error_info[s_no+t] = f"{_sensors_sep[t]:8}"

    return _time, temp_info, temp_error_info

def temp_sensor_parser(sensor_frame):
    """ 
    Function to extract the error value from a sensor's raw byte string.
    
    Parameters
    ----------
    sensor_frame : `str`
        A sensor's raw byte string.

    Returns
    -------
    (`str`, `str`) :
        The error string and measurement string in byte format.
    """

    _error = sensor_frame[:2] # good==1
    _measurement = sensor_frame[2:]
    
    return _error, _measurement 

def get_temp(measurment_bytes):
    """ 
    Function to extract the measurement value from a sensor's raw byte string.
    
    Parameters
    ----------
    measurment_bytes : `str`
        A sensor's measurement byts from its raw byte string.

    Returns
    -------
    `int` :
        The temperature value of the sensor in degrees Celsius.
    """

    # first byte is whether value is -ve or +ve
    _sign_byte = int(measurment_bytes[:2],16)
    # define the mapping (-ve for 1 and +ve for 0)
    _sign = -1 if _sign_byte>=128 else 1

    _a = hex(_sign_byte-128) if _sign_byte>=128 else hex(_sign_byte)

    # return the temperature in Celsius:
    #   convert measurement to base 10 then first 10 bits represent the right 
    #   of the decimal place so times by 2**-10 (think scientific notation).
    return _sign*int(_a+measurment_bytes[2:],16)*2**-10
    

if __name__=="__main__":
    # no valid entries
    example_frame0 = "0200000000010000220dc0f0200080f8340081f8340080f02000c2f0200081f8300080f0200081f83400"

    # first temp. sensor should be 25.423828125 C
    example_frame1 = "010000000003010065b2c0f0200080f8340081f8340080f02000c2f0200081f8300080f0200081f83400"
    # print(len(example_frame1))

    example_frames = "u01006529d8590101000801000043010000540100003d01000053010000610100001c010100290100002602006529d859010000370100000b010000000101001a010000100100000901000043010000290100003101006529d859010000070100005f01000041010000580101005a010000290101000d0100001e0100005002006529d8590100002501000016010100180100004a0101002e010000250100001a010000150100003f02006529d859010000450100001c0100003201000017010000230100001f0100001c0100003a0100001e02006529d8590101002e0100000a01000005010000090100003d010000520100005e010000120101005d01006529d8590100004d01010008010000480100001001010037010100310100004d0100001e0100004c01006529d8590100002a01010042010000380100001b010000390100000d010000350101001b0100002202006529d8590101004401000035010000320100006001000042010100140100004e010000320101001201006529d859010100450100006301000021010000630100005d0100000d0101000b010100520100005801006529d85901000003010000220100005b010000320100001b01000060010000390100000d01000020"
    
    # get_temp("010065b2") # == 25.423828125 C

    # print(temp_parser(example_frame0), "\nShould have no valid entries.\n")
    # print(temp_parser(example_frame1), "\nShould only have valid first entry with 25.423828125 C.\n")

    # print(temp_parser(example_frame0+example_frame1), "\nShould be both above together\n.")
    temp_parser(example_frame1+example_frame0+example_frame1)#, "\nShould be both above together, backwards.\n")

    # print(temp_parser(example_frames), "\nMulitple frames.")
