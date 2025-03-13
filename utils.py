import subprocess
import concurrent.futures

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
    'nmcli connection show',
    '/home/mike/boat-tracker/tools/upload_stats.py /home/mike/boat-tracker/boat_tracker.db',
    '/home/mike/boat-tracker/tools/gps_snapshot.py'
]

def run_command(command):
    """Run a single command and return its output."""
    try:
        output = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return {
            "command": command,
            "output": output.stdout.strip() if output.stdout else output.stderr.strip()
        }
    except Exception as e:
        return {
            "command": command,
            "output": f"Error running command: {str(e)}"
        }

def run_commands(commands):
    """Run predefined commands concurrently and return their output."""
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_command = {executor.submit(run_command, cmd): cmd for cmd in commands}
        for future in concurrent.futures.as_completed(future_to_command):
            results.append(future.result())  # Collect results as they complete
    return results

def get_service_status(service):
    """Fetch detailed service status from systemctl, including logs."""
    try:
        # Run systemctl show
        result = subprocess.run(
            ["systemctl", "show", service, "--no-page"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return {
                "Service": service,
                "ActiveState": "error",
                "SubState": "error",
                "MainPID": "error",
                "Logs": [f"⚠️ Error retrieving service: {result.stderr.strip()}"]
            }

        # Parse systemctl output
        status_data = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                status_data[key] = value

        # Get last 10 log lines from `systemctl status`
        log_result = subprocess.run(
            ["systemctl", "status", service, "--no-pager"],
            capture_output=True,
            text=True
        )
        logs = log_result.stdout.strip().split("\n")[-10:] if log_result.returncode == 0 else ["⚠️ No logs available"]

        return {
            "Service": service,
            "ActiveState": status_data.get("ActiveState", "unknown"),
            "SubState": status_data.get("SubState", "unknown"),
            "MainPID": "N/A" if status_data.get("MainPID", "0") == "0" else status_data.get("MainPID", "N/A"),
            "Logs": logs
        }

    except Exception as e:
        return {
            "Service": service,
            "ActiveState": "error",
            "SubState": "error",
            "MainPID": "error",
            "Logs": [f"⚠️ Exception: {str(e)}"]
        }

def get_services_status(services):
    """Fetch statuses for multiple services concurrently."""
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_service = {executor.submit(get_service_status, svc): svc for svc in services}
        for future in concurrent.futures.as_completed(future_to_service):
            results.append(future.result())  # Collect results as they complete
    return results
