import subprocess

def run_commands(commands):
    """Run predefined commands and return their output."""
    results = []
    for command in commands:
        try:
            output = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
            results.append({
                "command": command,
                "output": output.stdout.strip() if output.stdout else output.stderr.strip()
            })
        except Exception as e:
            results.append({
                "command": command,
                "output": f"Error running command: {str(e)}"
            })
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
            "ActiveState": status_data.get("ActiveState", "unknown"),
            "SubState": status_data.get("SubState", "unknown"),
            "MainPID": "N/A" if status_data.get("MainPID", "0") == "0" else status_data.get("MainPID", "N/A"),
            "Logs": logs
        }

    except Exception as e:
        return {
            "ActiveState": "error",
            "SubState": "error",
            "MainPID": "error",
            "Logs": [f"⚠️ Exception: {str(e)}"]
        }
