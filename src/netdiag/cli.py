import argparse

# Override the argparse
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage()
        print(f"\nError: {message}")
        print("\nRun with --help for more information.")
        self.exit(2)

def cmd_ping(args):
    print("cmd_ping")

def build_parser():
    parser = MyParser(
        prog="netdiag",
        description="Local-first network diagnostics"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    ping = sub.add_parser("ping")
    ping.add_argument("--count", "-c", type=int, default=5, help="")

    ping.set_defaults(func=cmd_ping)
    return parser

def main():
    parser = build_parser()
    arg = parser.parse_args()
    return arg.func(arg)
