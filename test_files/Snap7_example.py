import snap7

IP = '192.168.0.1'

RACK = 0
SLOT = 1
plc = snap7.client.Client()
plc.connect(IP, RACK, SLOT)

print(plc.get_cpu_state())

data = plc.db_read(1, 0, 4)
print(data)
data[0] = 0b00000001
data[3] = 0b00000011
plc.db_write(1, 0, data)
