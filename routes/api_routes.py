import os
import json
import subprocess
from flask import Blueprint, request

from routes.auth_routes import token_required

router = Blueprint("api", __name__, url_prefix="/api")

CONFIG_FILE_PATH = "onion-config/config.json"


def set_static_ip(interface, ipaddr, netmask, gateway,dns):
    try:
        # Set interface to static
        subprocess.run(["uci", "set", f"network.{interface}=interface"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.proto=static"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.ifname={interface}"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.ipaddr={ipaddr}"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.netmask={netmask}"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.gateway={gateway}"], check=True)
        subprocess.run(["uci", "set", f"network.{interface}.dns={dns}"], check=True)
        # Commit and reload network
        subprocess.run(["uci", "commit", "network"], check=True)
        subprocess.run(["/etc/init.d/network", "restart"], check=True)

        print("Ethernet settings updated successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to update settings:", e)
@router.route("/health", methods=["GET"])
def health():
    return {"status": True, "message": "API is running!"}

@router.route("/config/lan", methods=["GET"])
def get_lan_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    res = config.get("ethernet", {})
    return res

@router.route("/config/endpoint", methods=["GET"])
def get_endpoint_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    res = config.get("endpoint", {})
    return res

@router.route("/config/modbus", methods=["GET"])
def get_modbus_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    res = config.get("modbus", {})
    return res

@router.route("/config/lan", methods=["POST"])
def save_lan_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    new_ethernet = request.get_json(silent=True)
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    config["ethernet"] = new_ethernet
    print(new_ethernet)
    set_static_ip("eth0", new_ethernet["ip"],new_ethernet["subnet"],new_ethernet["gateway"],new_ethernet["dns"])
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return {"status": True, "message": "LAN config saved successfully."}

@router.route("/config/endpoint", methods=["POST"])
def save_endpoint_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    new_endpoint = request.get_json(silent=True)
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    config["endpoint"] = new_endpoint
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return {"status": True, "message": "Endpoint config saved successfully."}

@router.route("/config/modbus/main", methods=["POST"])
def save_modbus_main_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    new_modbus = request.get_json(silent=True)
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    config["modbus"]["config"] = new_modbus
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return {"status": True, "message": "Modbus config saved successfully."}

@router.route("/config/modbus/tags", methods=["POST"])
def save_modbus_tags_config():
    if not token_required(request):
        return {"status": False, "message": "Token validation failed."}
    new_modbus = request.get_json(silent=True)
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
    config["modbus"]["tags"] = new_modbus
    with open(CONFIG_FILE_PATH, "w") as f:
        json.dump(config, f, indent=2)
    return {"status": True, "message": "Modbus tags saved successfully."}