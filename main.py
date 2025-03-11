from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from utils import run_commands, get_service_status
import subprocess

app = FastAPI()

# Session middleware for authentication
SECRET_KEY = "your_secret_key_here"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory="templates")

# List of services to check
SERVICES = [
    "canbus",
    "canbus_listener",
    "boat-tracker",
    "dhcpcd",
    "temperature_mqtt",
    "zwave-js-ui",
    "gpsd",
    "mumble-server"
]

# List of shell commands to run

TEMP_CMD = """
awk '{print "CPU Temperature: " $1/1000 "°C"}' /sys/class/thermal/thermal_zone0/temp
"""

COMMANDS = [
    'iwconfig wlan1',
    'iwconfig wlan0',    
    'candump -n 4 can0',
    'lscpu | grep "MHz"',
    TEMP_CMD,
    'tailscale status',
    'ip route show',
    'nmcli connection show'
]

@app.get("/services", response_class=HTMLResponse)
async def services_page(request: Request):
    """Render the services page with detailed statuses and command outputs."""
    statuses = {service: get_service_status(service) for service in SERVICES}
    command_outputs = run_commands(COMMANDS)
    return templates.TemplateResponse(
        "services.html", 
        {"request": request, "statuses": statuses, "command_outputs": command_outputs}
    )

@app.get("/api/services")
async def get_services():
    """Return full service statuses as JSON, including logs."""
    statuses = {service: get_service_status(service) for service in SERVICES}
    return statuses

@app.get("/", response_class=HTMLResponse)
async def home():
    """Default landing page"""
    return "<h1>FastAPI is running!</h1>"
