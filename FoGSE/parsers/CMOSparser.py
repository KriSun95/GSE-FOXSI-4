### Functions for CMOS Parser ###
### By Riko Shimizu (SOKENDAI)
### Oct. 25th, 2023

import numpy as np
from PIL import Image

##### Confermation of commands  160B #####

def exposureParameters(data160B):
    gain_mode = int.from_bytes(data160B[0:4], byteorder='little')
    exposureQL = int.from_bytes(data160B[4:8], byteorder='little')
    exposurePC = int.from_bytes(data160B[8:12], byteorder='little')
    repeat_N = int.from_bytes(data160B[12:16], byteorder='little')
    repeat_n = int.from_bytes(data160B[16:20], byteorder='little')
    gain_even = int.from_bytes(data160B[20:24], byteorder='little')
    gain_odd = int.from_bytes(data160B[24:28], byteorder='little')
    ncapture = int.from_bytes(data160B[28:32], byteorder='little')
    return gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture

def operateCMOS(data160B):
    cmos_init = int.from_bytes(data160B[64:68], byteorder='little')
    cmos_training =  int.from_bytes(data160B[68:72], byteorder='little')
    cmos_setting =  int.from_bytes(data160B[72:76], byteorder='little')
    cmos_start =  int.from_bytes(data160B[80:84], byteorder='little')
    cmos_stop = int.from_bytes(data160B[84:88], byteorder='little')
    return cmos_init, cmos_training, cmos_setting, cmos_start, cmos_stop

def ping(data160B):
    ping = int.from_bytes(data160B[96:100], byteorder='little')
    return ping

def discreteCommands(data160B):
    enable_double_command = int.from_bytes(data160B[128:132], byteorder='little')
    remove_all_data =  int.from_bytes(data160B[132:136], byteorder='little')
    reboot =  int.from_bytes(data160B[136:140], byteorder='little')
    shutdown =  int.from_bytes(data160B[140:144], byteorder='little')
    return enable_double_command, remove_all_data, reboot, shutdown


# for check -----------
# with open('data160B_test.bin', 'rb') as file:
#     data = file.read()
# gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture = exposureParameters(data)
# print(hex(gain_mode))
# ---------------------


##### House keeping data 352B #####

def time(data352B):
    line_time = int.from_bytes(data352B[0:4], byteorder='little')
    line_time_at_pps = int.from_bytes(data352B[4:8], byteorder='little')
    return line_time, line_time_at_pps

def cpu(data352B):
    cpu_load_average = int.from_bytes(data352B[16:20], byteorder='little')
    return cpu_load_average

def disk(data352B):
    remaining_disk_size = int.from_bytes(data352B[20:24], byteorder='little')
    return remaining_disk_size

def softFpgaStatus(data352B):
    software_status = int.from_bytes(data352B[32:36], byteorder='little')
    error_time = int.from_bytes(data352B[36:40], byteorder='little')
    error_flag = int.from_bytes(data352B[40:44], byteorder='little')
    error_training = int.from_bytes(data352B[44:48], byteorder='little')
    data_validity = int.from_bytes(data352B[48:52], byteorder='little')
    return software_status, error_time, error_flag, error_training, data_validity


def twos_complement_to_decimal(bits):
    if bits[0] == '1':  # Negative number
        inverted_bits = ''.join('1' if bit == '0' else '0' for bit in bits)
        decimal_value = int(inverted_bits, 2) + 1
        return -decimal_value
    else:  # Positive number
        return int(bits, 2)

def sensorTemp(data4B):
    value_int = int.from_bytes(data4B, 'little') 
    value_dec = int.from_bytes(data4B, 'little')
    value = (value_int << 8) + value_dec
    sensor_temp = twos_complement_to_decimal(bin(value))/(2**8)
    return sensor_temp

def fpgaTemp(data4B):
    value = int.from_bytes(data4B, 'little')
    value = value & 0xFFF
    fpga_temp = twos_complement_to_decimal(bin(value))/(2**4)
    return fpga_temp

def temperature(data352B):
    sensor_temp = sensorTemp(data352B[80:84])
    fpga_temp = fpgaTemp(data352B[84:88])
    return sensor_temp, fpga_temp


def currentExposureParameters(data352B):
    gain_mode = int.from_bytes(data352B[96:100], byteorder='little')
    exposureQL = int.from_bytes(data352B[100:104], byteorder='little')
    exposurePC = int.from_bytes(data352B[104:108], byteorder='little')
    repeat_N = int.from_bytes(data352B[108:112], byteorder='little')
    repeat_n = int.from_bytes(data352B[112:116], byteorder='little')
    gain_even = int.from_bytes(data352B[116:120], byteorder='little')
    gain_odd = int.from_bytes(data352B[120:124], byteorder='little')
    ncapture = int.from_bytes(data352B[124:128], byteorder='little')
    return gain_mode, exposureQL, exposurePC, repeat_N, repeat_n, gain_even, gain_odd, ncapture

def downlinkData(data352B):
    write_pointer_position_store_data = int.from_bytes(data352B[128:132], byteorder='little')
    read_pointer_position_QL = int.from_bytes(data352B[160:164], byteorder='little')
    data_size_QL = int.from_bytes(data352B[164:168], byteorder='little')
    read_pointer_position_PC = int.from_bytes(data352B[168:172], byteorder='little')
    data_size_PC = int.from_bytes(data352B[172:176], byteorder='little')
    return write_pointer_position_store_data, read_pointer_position_QL, data_size_QL, read_pointer_position_PC, data_size_PC


##### QL data 481kB #####

def makeDecimalList(data):
    decimal_list = []
    for i in range(0, len(data), 2):
        byte1 = data[i + 1]
        byte2 = data[i]
        decimal_number = byte1 * 256 + byte2
        decimal_list.append(decimal_number)
    return decimal_list

def sortRegions(list):
    # Convert a list to a 2-dimension
    array = []
    for i in range(0, len(list), 512):
        row = list[i:i+512]
        array.append(row)
    # Switch rows(region1>2>4>5>3 -> 1>2>3>4>5)  0-,96-,192-,288-,384-479
    array = np.array(array)
    for j in range(0, 96):
        array[[192+j, 288+j, 384+j]] = array[[384+j, 192+j, 288+j]]
    return np.ravel(array)

# def QLimageData(data481kB):
#     linetime = int.from_bytes(data481kB[4:8], byteorder='little')
#     gain = int.from_bytes(data481kB[8:12], byteorder='little')
#     exposureQL = int.from_bytes(data481kB[12:16], byteorder='little')

#     decimal_list = makeDecimalList(data481kB[16:16+491520])
#     value_array = sortRegions(decimal_list)
#     # Make QL image
#     width, height = 512, 480
#     min_value, max_value = 0, 4095
#     QLimage = Image.new("L", (width, height))
#     # Set pixel values
#     pixels = [(float(value)-min_value)/(max_value - min_value)*256 for value in value_array]
#     QLimage.putdata(pixels)

#     return linetime, gain, exposureQL, QLimage

def QLimageData(data481kB):
    linetime = int.from_bytes(data481kB[4:8], byteorder='little')
    gain = int.from_bytes(data481kB[8:12], byteorder='little')
    exposureQL = int.from_bytes(data481kB[12:16], byteorder='little')

    decimal_list = makeDecimalList(data481kB[16:16+491520])
    value_array = sortRegions(decimal_list)
    # Make QL image
    width, height = 512, 480
    min_value, max_value = 0, 4095
    # QLimage = Image.new("L", (width, height))
    # Set pixel values
    pixels = [(float(value)-min_value)/(max_value - min_value)*256 for value in value_array]
    # QLimage.putdata(pixels)

    #**********************************************************************
    #******************************** Kris ********************************
    pixels = np.array([(float(value)-min_value)/(max_value - min_value) for value in value_array])
    pixels[pixels>np.quantile(pixels, 0.9)] = np.quantile(pixels, 0.9)
    pixels[pixels<np.quantile(pixels, 0.1)] = np.quantile(pixels, 0.1)
    pixels = (pixels-np.min(pixels))/(np.max(pixels-np.min(pixels)))*256
    #**********************************************************************

    return linetime, gain, exposureQL, np.reshape(pixels, (height,width))


# for check ---------------
# with open('data481kB_test.bin', 'rb') as file:
#     QLdata = file.read()

# linetime, gain, exposureQL, QLimage = QLimageData(QLdata)
# # print(hex(gain))
# QLimage.save("testQL.png")

# ---------------------------


##### PC data 577kB #####

# def PCimageData(data577kB,frame_no=0):
    
    # frame_start = frame_no*590848

    # linetime = int.from_bytes(data577kB[frame_start+4:frame_start+8], byteorder='little')
    # gain = int.from_bytes(data577kB[frame_start+8:frame_start+12], byteorder='little')
    # exposurePC = int.from_bytes(data577kB[frame_start+12:frame_start+16], byteorder='little')

    # decimal_list = makeDecimalList(data577kB[frame_start+16:frame_start+16+589824])
    # # Make PC image
    # width, height = 768, 384
    # min_value, max_value = 0, 4095
    # PCimage = Image.new("L", (width, height))
    # # Set pixel values
    # pixels = [(float(value)-min_value)/(max_value - min_value)*256 for value in decimal_list]

    # #**********************************************************************
    # #******************************** Kris ********************************
    # pixels = np.array([(float(value)-min_value)/(max_value - min_value) for value in decimal_list])
    # pixels[pixels>np.quantile(pixels, 0.9)] = np.quantile(pixels, 0.9)
    # pixels[pixels<np.quantile(pixels, 0.1)] = np.quantile(pixels, 0.1)
    # pixels = (pixels-np.min(pixels))/(np.max(pixels-np.min(pixels)))*256
    # #**********************************************************************

    # PCimage.putdata(pixels)

    # return linetime, gain, exposurePC, PCimage

def PCimageData(data577kB,frame_no=0):
    
    frame_start = frame_no*590848

    linetime = int.from_bytes(data577kB[frame_start+4:frame_start+8], byteorder='little')
    gain = int.from_bytes(data577kB[frame_start+8:frame_start+12], byteorder='little')
    exposurePC = int.from_bytes(data577kB[frame_start+12:frame_start+16], byteorder='little')

    decimal_list = makeDecimalList(data577kB[frame_start+16:frame_start+16+589824])
    # Make PC image
    width, height = 768, 384
    min_value, max_value = 0, 4095
    # PCimage = Image.new("L", (width, height))
    # Set pixel values
    pixels = [(float(value)-min_value)/(max_value - min_value)*256 for value in decimal_list]

    #**********************************************************************
    #******************************** Kris ********************************
    pixels = np.array([(float(value)-min_value)/(max_value - min_value) for value in decimal_list])
    pixels[pixels>np.quantile(pixels, 0.9)] = np.quantile(pixels, 0.9)
    pixels[pixels<np.quantile(pixels, 0.1)] = np.quantile(pixels, 0.1)
    pixels = (pixels-np.min(pixels))/(np.max(pixels-np.min(pixels)))*256
    #**********************************************************************

    # PCimage.putdata(pixels)

    return linetime, gain, exposurePC, np.reshape(pixels, (height,width))

# for check ---------------
# with open('data577kB_test.bin', 'rb') as file:
#     PCdata = file.read()

# linetime, gain, exposurePC, PCimage = PCimageData(PCdata)
# PCimage.save("testPC.png")

# ---------------------------

if __name__=="__main__":
    import matplotlib.pyplot as plt
    from FoGSE.readBackwards import BackwardsReader
    # cmos_file = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/cmos_frames.log"
    # cmos_file = "/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/cmos.log"

    # with open(cmos_file, 'rb') as file:
    #     print(type(file))
    #     PCdata = file.read()
    # for i in range(4):
    #     linetime, gain, exposurePC, PCimage = PCimageData(PCdata,frame_no=i)
    #     print(linetime, gain, exposurePC, PCimage)
    #     print(type(linetime), type(gain), type(exposurePC), type(PCimage))
    #     # PCimage.save(f"/Users/kris/Desktop/testPC{i}.png")
    #     plt.figure()
    #     plt.imshow(PCimage)
    #     plt.show()
    
    # with BackwardsReader(file=cmos_file, blksize=590848, forward=True) as f:
    #     print(type(f))
    #     PCdata = f.read_block()
    # for i in range(4):
    #     linetime, gain, exposurePC, PCimage = PCimageData(PCdata,frame_no=i)
    #     print(linetime, gain, exposurePC, PCimage)
    #     print(type(linetime), type(gain), type(exposurePC), type(PCimage))
    #     PCimage.save(f"/Users/kris/Desktop/testPC_bkwrdsrdr{i}.png")

    with open('/Users/kris/Documents/umnPostdoc/projects/both/foxsi4/gse/cmos_parser/otherExamples-20231102/example2/cmos_ql.log', 'rb') as file:
        QLdata = file.read()

    linetime, gain, exposureQL, QLimage = QLimageData(QLdata)
    QLimage.save("/Users/kris/Desktop/testQL.png")