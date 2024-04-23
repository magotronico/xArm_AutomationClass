import snap7

def init_plc():
    plc = snap7.client.Client()
    plc.connect('192.168.1.1', 0, 1)
    print(plc.get_cpu_state())
    return plc

def main():
    plc = init_plc()

    # Read all variables from DB1
    data = plc.db_read(1, 0, 2)  # Read 8 bytes from DB1

    # Set the 3rd byte to false/true. False = 0, True = 1 (in binary)
    new_counter = int.from_bytes(data[:2], byteorder='big') + 1
    data[:2] = new_counter.to_bytes(2, byteorder='big')
    plc.db_write(1, 0, data)

    # # Decode the variables
    # contadorOk = int.from_bytes(data[:1], byteorder='big')
    # working = bool(data[2])
    # contadorScrap = int.from_bytes(data[3:4], byteorder='big')
    # rutinaOk = bool(data[6])
    # piezaEnConveyer = bool(data[6])
    # Stop = bool(data[6])
    # rutinaScrap = bool(data[6])

    # print("contadorOk:", contadorOk)
    # print("working:", working)
    # print("contadorScrap:", contadorScrap)
    # print("rutinaOk:", rutinaOk)
    # print("piezaEnConveyer:", piezaEnConveyer)
    # print("Stop:", Stop)
    # print("rutinaScrap:", rutinaScrap)

if __name__ == '__main__':
    main()