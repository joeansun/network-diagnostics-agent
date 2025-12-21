from netdiag.config import load_config
from netdiag.probes.ping import run_ping


def main():
    config = load_config()
    run_ping(config)