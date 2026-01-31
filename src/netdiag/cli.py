import argparse
from .probes.ping import run_ping
from .config.config import load_config

# Override the argparse
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage()
        print(f"\nError: {message}")
        print("\nRun with --help for more information.")
        self.exit(2)

def cmd_ping(args, app_config):
    run_ping(app_config)

def cmd_dns(args, app_config):
    pass

def cmd_run(args, app_config):
    cmd_ping(args, app_config)


def build_parser():
    parser = MyParser(
        prog="netdiag",
        description="Local-first network diagnostics"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    ping = sub.add_parser("ping")
    ping.add_argument("--count", "-c", type=int, default=5, help="")
    ping.set_defaults(func=cmd_ping)

    dns = sub.add_parser("dns")
    dns.set_defaults(func=cmd_dns)

    run = sub.add_parser("run")
    run.set_defaults(func=cmd_run)
    
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()
    app_config = load_config()
    return args.func(args, app_config)
