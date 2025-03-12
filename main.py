from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi import WebSocket, WebSocketDisconnect
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from utils import SERVICES, COMMANDS, run_commands, get_service_status
import subprocess
import asyncio

app = FastAPI()

# Session middleware for authentication
SECRET_KEY = "your_secret_key_here"
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 Templates
templates = Jinja2Templates(directory="templates")

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

WIFI_INTERFACE = "wlan1"  # Change this if needed

async def get_wifi_signal():
    """Reads Wi-Fi signal strength and quality from /proc/net/wireless."""
    try:
        with open("/proc/net/wireless", "r") as f:
            lines = f.readlines()
            for line in lines:
                if WIFI_INTERFACE in line:
                    parts = line.split()
                    quality = int(float(parts[2]))  # Link Quality (0-100)
                    signal_level = int(float(parts[3]))  # Signal Level in dBm
                    return {"quality": quality, "signal_level": signal_level}
    except Exception as e:
        return {"quality": 0, "signal_level": -100, "error": str(e)}  # Default weak signal if error
    return {"quality": 0, "signal_level": -100}  # No data found

@app.get("/wifi", response_class=HTMLResponse)
async def wifi_page(request: Request):
    """Serve the Wi-Fi signal page"""
    return templates.TemplateResponse("wifi.html", {"request": request})

@app.websocket("/api/wifi")  # ✅ Now WebSocket uses /api/wifi
async def websocket_wifi(websocket: WebSocket):
    """WebSocket to send live Wi-Fi signal strength every second."""
    await websocket.accept()
    try:
        while True:
            wifi_data = await get_wifi_signal()
            await websocket.send_json(wifi_data)
            await asyncio.sleep(1)  # Send updates every second
    except WebSocketDisconnect:
        print("Client disconnected")
