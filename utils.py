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
C1 = """
awk '{print "CPU Temperature: " $1/1000 "°C"}' /sys/class/thermal/thermal_zone0/temp
"""

C2 = """
awk '{print $1 / 1000 " MHz"}' /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq
"""

COMMANDS = [
    'uptime',
    C1,
    C2,
    'iwconfig wlan1',
    'iwconfig wlan0',
    'nmcli connection show',
    'tailscale status',
    'ip route show',
    'candump -n 4 can0',
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
    results_dict = {cmd: None for cmd in commands}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_command = {executor.submit(run_command, cmd): cmd for cmd in commands}
        for future in concurrent.futures.as_completed(future_to_command):
            result = future.result()
            results_dict[result.get('command')] = result

    return [results_dict[cmd] for cmd in commands]

def get_service_status(service):
    """Fetch detailed service status from systemctl, including logs."""
    try:
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

        status_data = {}
        for line in result.stdout.strip().split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                status_data[key] = value

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
            results.append(future.result())
    return results

def get_system_status(services, commands):
    """Retrieve both service statuses and command outputs concurrently."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        service_future = executor.submit(get_services_status, services)
        command_future = executor.submit(run_commands, commands)

        services_status = service_future.result()
        commands_output = command_future.result()

    return {
        "services_status": services_status,
        "commands_output": commands_output
    }
