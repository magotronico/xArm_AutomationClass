import socket

HOST = "192.168.1.130"  # The server's hostname or IP address
PORT = 20000  # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b"cmd Online")
    s.sendall(b"cmd trigger")
    data = s.recv(24) #IMPORTANTE REVISAR EL TAMAÑO DEL STRING QUE SE ENVÍA PARA SELECCIONAR LOS BITES ADECUADOS 


print(f"Received2 {data!r}")

str1 = data.decode('UTF-8')
t=str1.split(" ")   #IMPORTANTE REVISAR CUAL ES EL CARACTER USADO PARA DELIMITAR CADA DATO
x=float(t[0])
y=float(t[1])
r=float(t[2])
print(x)
print(y)  
print(r) 


