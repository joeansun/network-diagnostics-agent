import subprocess

def execute_ping(host: str, count: int, timeout_ms: int):
    cmd = ["ping", host,
        "-c", str(count),
        "-W", str(timeout_ms)
    ]

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

def run_ping(app_config): 
    ping_config = app_config.ping
    for host in ping_config.targets:
        result = execute_ping(
            parse_ping() if host == "gateway" else host, 
            ping_config.count,
            ping_config.timeout_ms
        )
        print(result.stdout, result.stderr, result.returncode)


def parse_ping():
    result = subprocess.run(
                ["route", "-n", "get", "default"],
                capture_output=True,
                text=True,
                check=False,
            )
    for line in result.stdout.splitlines():
        stripped_line = line.lstrip()
        if stripped_line.startswith("gateway"):
            return stripped_line.split(":", 1)[1].strip()