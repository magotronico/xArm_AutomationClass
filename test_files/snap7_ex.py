import snap7

def init_plc():
    plc = snap7.client.Client()
    plc.connect('192.168.0.1', 0, 1)
    print(plc.get_cpu_state())
    return plc

def main():
    plc = init_plc() # Connect to PLC
    data = plc.db_read(1, 0, 3) # Read 3 bytes from DB1

    # Convert the first 2 bytes to integer
    data_decode = int.from_bytes(data[:2], byteorder='big')
    print(data_decode)

    # Set the 3rd byte to false/true. False = 0, True = 1 (in binary)
    data[2] = 0b00000010
    plc.db_write(1, 0, data)

if __name__ == '__main__':
    main()