import json
from pymodbus.client import ModbusSerialClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import Endian
from pymodbus import pymodbus_apply_logging_config
import os
import time
# Load configuration from JSON file
import requests
import json
from datetime import datetime
import pytz
import socket
CACHE_FILE = "modbus_data_cache.jsonl"
THINGSBOARD_HOST = 'samasth.io:443'
ACCESS_TOKEN = '5ypb2oxoq1qzkukspnyv'
THINGSBOARD_END_URL = 'https://samasth.io:443/api/v1/5ypb2oxoq1qzkukspnyv'
MAX_CACHE_LINES = 2000000
# Send telemetry data
def send_telemetry(URL,payload,PROXY_URL):
    url = f'{URL}/telemetry'
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload,indent=2),proxies=PROXY_URL)
        response.raise_for_status()
        print('Telemetry data sent successfully')
    except requests.exceptions.RequestException as e:
        print(f'Error sending telemetry data: {e}')
    result = payload

    if is_internet_available():
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    try:
                        cached_data = json.loads(line.strip())
                        try:
                            response = requests.post(url, headers=headers, data=json.dumps(cached_data,indent=2),proxies=PROXY_URL)
                            response.raise_for_status()
                            print('Telemetry data sent successfully')
                        except requests.exceptions.RequestException as e:
                            print(f'Error sending telemetry data: {e}')
                    except Exception as e:
                        print("Failed to send cached data:", e)
            open(CACHE_FILE, "w").close()
    else:
        # Save current result to file
        with open(CACHE_FILE, "a") as f:
            f.write(json.dumps(result) + "\n")
        # Trim file if too long
        with open(CACHE_FILE, "r") as f:
            lines = f.readlines()

        if len(lines) > MAX_CACHE_LINES:
            lines = lines[-MAX_CACHE_LINES:]  # Keep only the last N lines
            with open(CACHE_FILE, "w") as f:
                f.writelines(lines)


# Get device attributes
def get_attributes(URL,attribute_keys,PROXY_URL):
     url = f'{URL}/attributes?sharedKeys={attribute_keys}'
     try:
        response = requests.get(url,proxies=PROXY_URL)
        response.raise_for_status()
        print('Attributes fetched successfully')
        return response.json()
     except requests.exceptions.RequestException as e:
        print(f'Error fetching attributes: {e}')
        return None

from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

def read_tag_data(client, tag):
    try:
        address = int(tag["start_address"])
        data_type = tag["data_type"]
        function_code = int(tag["function_code"])

        # Calculate register count based on data type
        bytes_per_value = {
            "int16": 2, "uint16": 2,
            "int32_BB": 4, "float32_BB": 4,
            "int32_LB": 4, "float32_LB": 4,
            "int32_BL": 4, "float32_BL": 4,
            "int32_LL": 4, "float32_LL": 4,
            "float64": 8,
            "hex": 2, "binary": 2  # minimal unit
        }

        if data_type not in bytes_per_value:
            return [f"Unsupported data type: {data_type}"]

        count = int(tag["quantity"])
        reg_count = (bytes_per_value[data_type] // 2) * count  # Modbus register = 2 bytes

        # Read registers or bits
        if function_code == 3:
            result = client.read_holding_registers(address=address, count=reg_count)
        elif function_code == 4:
            result = client.read_input_registers(address=address, count=reg_count)
        elif function_code == 1:
            result = client.read_coils(address=address, count=count)
        elif function_code == 2:
            result = client.read_discrete_inputs(address=address, count=count)
        else:
            return ["Unsupported function code"]

        if result.isError():
            return [f"Read error: {result}"]

        values = []

        if function_code in [3, 4]:  # Registers
            print(f"Raw Registers: {result.registers}")
            decoder_BB = BinaryPayloadDecoder.fromRegisters(
                result.registers, byteorder=Endian.BIG, wordorder=Endian.BIG
            )
            decoder_LL = BinaryPayloadDecoder.fromRegisters(
                result.registers, byteorder=Endian.LITTLE, wordorder=Endian.LITTLE
            )
            decoder_LB = BinaryPayloadDecoder.fromRegisters(
                result.registers, byteorder=Endian.LITTLE, wordorder=Endian.BIG
            )
            decoder_BL = BinaryPayloadDecoder.fromRegisters(
                result.registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE
            )
            for _ in range(count):
                if data_type == "int16":
                    values.append(decoder_BL.decode_16bit_int())
                elif data_type == "uint16":
                    values.append(decoder_BL.decode_16bit_uint())
                elif data_type == "float64":
                    values.append(decoder_BL.decode_64bit_float())

                elif data_type == "int32_BB":
                    values.append(decoder_BB.decode_32bit_int())
                elif data_type == "int32_BL":
                    values.append(decoder_BL.decode_32bit_int())
                elif data_type == "int32_LL":
                    values.append(decoder_LL.decode_32bit_int())
                elif data_type == "int32_LB":
                    values.append(decoder_LB.decode_32bit_int())

                elif data_type == "float32_BL":
                    values.append(decoder_BL.decode_32bit_float())
                elif data_type == "float32_BB":
                    values.append(decoder_BB.decode_32bit_float())
                elif data_type == "float32_LL":
                    values.append(decoder_LL.decode_32bit_float())
                elif data_type == "float32_LB":
                    values.append(decoder_LB.decode_32bit_float())
                
                
                elif data_type == "hex":
                    raw = decoder_BL.decode_16bit_uint()
                    values.append(hex(raw))
                elif data_type == "binary":
                    raw = decoder_BL.decode_16bit_uint()
                    values.append(bin(raw))
                else:
                    values.append("Unsupported decode type")
        else:  # Coils or discrete inputs
            values = list(result.bits[:count])

    except Exception as e:
        values = [f"Exception: {e}"]

    return values[0]

def generate_modbus_json(client, config):
    tags = config["modbus"]["tags"]
    output = {}
    for tag in tags:
        tag_name = tag["tag_name"]
        output[tag_name] = read_tag_data(client, tag)
    tz = pytz.timezone("Asia/Kolkata")  # Change if needed
    now = datetime.now(tz)
    formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    output["current"] = {
        "datetime": formatted_time
    }
    return output


def is_internet_available(host="8.8.8.8", port=53, timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error:
        return False

def handle_offline_data(client, config, END_URL, PROXY_URL):


    result = generate_modbus_json(client, config)

    if is_internet_available():
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    try:
                        cached_data = json.loads(line.strip())
                        send_telemetry(END_URL, cached_data, PROXY_URL)
                    except Exception as e:
                        print("Failed to send cached data:", e)

            # Clear the file after successful sending
            open(CACHE_FILE, "w").close()
    else:
        # Save current result to file
        with open(CACHE_FILE, "a") as f:
            f.write(json.dumps(result) + "\n")


# Main execution
if __name__ == "__main__":
    while True:
        CONFIG_FILE_PATH = "onion-config/config.json"  # Or use absolute path if needed
        if not os.path.exists(CONFIG_FILE_PATH):
            print("Config file not found!")
            exit(1)

        with open(CONFIG_FILE_PATH, "r") as f:
            config = json.load(f)
        polling_minutes = int(config["modbus"]["config"]["Polling_time"])
        polling_seconds = polling_minutes * 60
        END_URL=config["endpoint"]["endpoint_url"]
        PROXY_URL=config["endpoint"]["proxy_url"]

        SERIAL_PORT = "/dev/ttyS2"  # Adjust this based on your system
        UNIT_ID = 1  # Modbus slave ID
        client = ModbusSerialClient(
            port=SERIAL_PORT,
            baudrate=int(config["modbus"]["config"]["Baudrate"]),
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=1
        )
        pymodbus_apply_logging_config("DEBUG")
	
        try:
            if client.connect():
                try:
                    result = generate_modbus_json(client, config)
                    print(json.dumps(result, indent=2))
                except Exception as e:
                    print(f"Modbus data fetch error: {e}")
                    result = {"status": "NA"}
                send_telemetry(END_URL,result,PROXY_URL)
                client.close()
            else:
                print("Failed to connect to Modbus RTU device.")
                send_telemetry(END_URL,{"status": "NA"},PROXY_URL)
        except Exception as e:
            print(f"Unexpected error: {e}")
            send_telemetry(END_URL,{"status": "NA"},PROXY_URL)

        try:
            attributes = get_attributes(END_URL,'targetTemperature, desiredHumidity',PROXY_URL)
            if attributes:
                print(f'Attributes: {attributes}')
        except Exception as e:
            print(f"Error fetching attributes: {e}")
        print(polling_seconds)
        time.sleep(polling_seconds)

