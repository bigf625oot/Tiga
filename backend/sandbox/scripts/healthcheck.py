import sys
import os
import subprocess
import socket
import json

def check_disk_space():
    stat = os.statvfs('/')
    return {
        "total": stat.f_blocks * stat.f_frsize,
        "available": stat.f_bavail * stat.f_frsize,
        "used_percent": (1 - stat.f_bavail / stat.f_blocks) * 100
    }

def check_memory():
    with open('/proc/meminfo', 'r') as f:
        meminfo = f.read()
    total = 0
    free = 0
    for line in meminfo.splitlines():
        if "MemTotal" in line:
            total = int(line.split()[1])
        if "MemAvailable" in line:
            free = int(line.split()[1])
    return {
        "total_kb": total,
        "available_kb": free,
        "used_percent": (1 - free / total) * 100 if total > 0 else 0
    }

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False

def main():
    health = {
        "status": "healthy",
        "disk": check_disk_space(),
        "memory": check_memory(),
        "internet": check_internet(),
        "toolchain": {}
    }

    # Quick check of key tools
    tools = ["gcc", "java", "node", "python3", "docker"]
    for tool in tools:
        try:
            subprocess.check_call([tool, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            health["toolchain"][tool] = "ok"
        except:
            health["toolchain"][tool] = "missing"
            health["status"] = "degraded"

    print(json.dumps(health, indent=2))
    
    if health["status"] != "healthy":
        sys.exit(1)

if __name__ == "__main__":
    main()
