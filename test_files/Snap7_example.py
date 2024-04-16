import snap7


IP = '192.168.0.1'

RACK = 0
SLOT = 1
plc = snap7.client.Client()
plc.connect(IP, RACK, SLOT)

print(plc.get_cpu_state())

# Define the size of the data block you want to read
data_block_size = 3  # Replace with the actual size

# Read the entire data block
data = plc.db_read(1, 0, data_block_size)

# Print the data
for i in range(data_block_size):
    print(f"Byte {i}: {data[i]}")

# data = plc.db_read(1, 0, 1)
# print(data)
# data[0] = 0b00000001
# data[3] = 0b00000011
# plc.db_write(1, 0, data)
