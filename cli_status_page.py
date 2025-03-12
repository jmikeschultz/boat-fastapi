#!/home/mike/boat-fastapi/venv/bin/python

import sys
from main import SERVICES, COMMANDS, run_commands, get_service_status

def print_service_statuses():
    """Fetch and print service statuses."""
    print("\n🔍 Checking Service Statuses...\n" + "=" * 40)
    for service in SERVICES:
        status = get_service_status(service)
        print(f"📌 Service: {service}")
        print(f"   ActiveState: {status['ActiveState']}")
        print(f"   SubState: {status['SubState']}")
        print(f"   MainPID: {status['MainPID']}")
        print("   Logs:")
        for log in status["Logs"]:
            print(f"      {log}")
        print("-" * 40)

def print_command_outputs():
    """Run and print predefined shell commands."""
    print("\n🚀 Running Shell Commands...\n" + "=" * 40)
    results = run_commands(COMMANDS)
    for result in results:
        print(f"📌 Command: {result['command']}")
        print(f"   Output:\n{result['output']}")
        print("-" * 40)

def main():
    """Command-line entry point."""
    print("🌟 Boat-FastAPI CLI Status Tool 🌟\n" + "=" * 50)

    # Allow command-line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--services":
        print_service_statuses()
    elif len(sys.argv) > 1 and sys.argv[1] == "--commands":
        print_command_outputs()
    else:
        print_service_statuses()
        print_command_outputs()

if __name__ == "__main__":
    main()
