from flask import Blueprint, render_template

router = Blueprint("ui", __name__)

@router.route("/", methods=["GET"])
def read_root():
    return render_template("index.html")

@router.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@router.route("/endpoint", methods=["GET"])
def endpoint_page():
    return render_template("endpoint.html")

@router.route("/lan", methods=["GET"])
def lan_page():
    return render_template("lan.html")

@router.route("/modbus", methods=["GET"])
def modbus_page():
    return render_template("modbus.html")
