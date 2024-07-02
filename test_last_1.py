import mysql.connector
import socket
from bichtest4 import Read_LP_from_photo

#-------------------code hoan chinh---------------
# Function to send data to ESP32
def send_data_to_esp32(ip, port, data):
    esp32_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    esp32_socket.connect((ip, port))
    esp32_socket.sendall(data.encode())
    esp32_socket.close()

# Function to check parking status
def checkParkingStatus(Card_key, lisence):
    if Card_key is not None or lisence is not None:
        try: 
            query = "SELECT * FROM parking.history_parking WHERE Card_key = %s AND License_Plate = %s AND status = 1;"
            cursor.execute(query, (Card_key, lisence))
            results = cursor.fetchall()
            return len(results) == 0
        except mysql.connector.Error as error:
            print("Error:", error)
            return False
    return False

# Function to receive data from ESP32
def receive_data_from_esp32(ip, port):
    esp32_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    esp32_socket.connect((ip, port))
    received_data = ""
    while True:
        chunk = esp32_socket.recv(1024).decode("utf-8")
        if not chunk:
            break
        received_data += chunk
    esp32_socket.close()
    return received_data

# Function to check if a license plate is parked
def checkLisenceIsParking(lisence):
    if lisence is not None:
        try: 
            query = "SELECT * FROM parking.history_parking WHERE License_Plate = %s AND status = 1;"
            cursor.execute(query, [lisence])
            results = cursor.fetchall()
            return len(results) > 0
        except mysql.connector.Error as error:
            print("Error:", error)
            return False
    return False

# Function to park a vehicle
def parkingIn(Card_key, lisence):
    if Card_key is not None or lisence is not None:
        try: 
            if checkLisenceIsParking(lisence):
                print("Xe đã có trong bãi")
                send_data_to_esp32(esp32_ip, esp32_port, "0")
            else:
                query = "INSERT INTO `history_parking` (`Card_key`, `License_Plate`) VALUES (%s, %s);"
                cursor.execute(query, (Card_key, lisence))
                conn.commit()
                if cursor.rowcount > 0:
                    print("INSERT operation was successful.")
                    send_data_to_esp32(esp32_ip, esp32_port, "1")
                else:
                    print("INSERT operation failed.")
                    send_data_to_esp32(esp32_ip, esp32_port, "0")
        except mysql.connector.Error as error:
            print("Error:", error)
            send_data_to_esp32(esp32_ip, esp32_port, "0")

# Function to remove a vehicle from parking
def getOut(Card_key, lisence):
    if Card_key is not None or lisence is not None:
        try: 
            query = "UPDATE `history_parking` SET `Status` = '0', `Time_Out` = CURRENT_TIMESTAMP WHERE (`Card_key` = %s AND `License_Plate` = %s);"
            cursor.execute(query, (Card_key, lisence))
            conn.commit()
            if cursor.rowcount > 0:
                print("Update operation was successful.")
                send_data_to_esp32(esp32_ip, esp32_port, "2")
            else:
                print("Update operation failed.")
                send_data_to_esp32(esp32_ip, esp32_port, "0")
        except mysql.connector.Error as error:
            print("Error:", error)
            send_data_to_esp32(esp32_ip, esp32_port, "0")

# Function to handle parking operations
def handleParking(Card_key, lisence):
    if Card_key is not None or lisence is not None:
        try: 
            if checkParkingStatus(Card_key, lisence):
                parkingIn(Card_key, lisence)
            else: 
                getOut(Card_key, lisence)
        except mysql.connector.Error as error:
            print("Error:", error)
            send_data_to_esp32(esp32_ip, esp32_port, "0")

# Establish connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="parking"
)

# Create cursor
cursor = conn.cursor()

# ESP32 IP and port
esp32_ip = "192.168.190.139"
esp32_port = 80

# Receive data from ESP32
received_data = receive_data_from_esp32(esp32_ip, esp32_port)
print("Received data from ESP32:", received_data)

#Camera IP and port
camIP = "192.168.45.97"
port = "8080"
Received_LP = Read_LP_from_photo(camIP, port)
print("License plate detected:", Received_LP)

# Handle parking operation
handleParking(received_data, Received_LP)
