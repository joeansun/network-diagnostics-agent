import argparse
import uuid

from netdiag.config.config import load_config
from netdiag.database import (
    create_db,
    get_db_connection,
    insert_ping_records_db,
    insert_sessions_db,
    update_session_status_db,
)
from netdiag.os import get_os_adapter
from netdiag.presentation import format_ping_report
from netdiag.probes.ping import run_ping


# Override the argparse
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage()
        print(f"\nError: {message}")
        print("\nRun with --help for more information.")
        self.exit(2)


def cmd_ping(args, app_config, conn, session_id):
    os_adapter = get_os_adapter()
    ping_config = app_config.ping
    for host in app_config.ping.targets:
        ping_record = run_ping(
            host=host,
            os_adapter=os_adapter,
            count=args.count
            if hasattr(args, "count") and args.count is not None
            else ping_config.count,
            timeout_ms=args.timeout_ms
            if hasattr(args, "timeout_ms") and args.timeout_ms is not None
            else ping_config.timeout_ms,
            session_id=session_id,
        )
        
        insert_ping_records_db(session_id= session_id, conn=conn, ping_record=ping_record)
        print(format_ping_report(ping_record))


def cmd_dns(args, app_config, conn, session_id):
    pass


def cmd_run(args, app_config, conn, session_id):
    cmd_ping(args, app_config, conn, session_id)


def build_parser():
    parser = MyParser(prog="netdiag", description="Local-first network diagnostics")

    sub = parser.add_subparsers(dest="command", required=True)

    ping = sub.add_parser("ping")
    ping.add_argument("--count", "-c", type=int, help="")
    ping.add_argument("--timeout-ms", "-t", type=int, help="")
    ping.set_defaults(func=cmd_ping)

    dns = sub.add_parser("dns")
    dns.set_defaults(func=cmd_dns)

    run = sub.add_parser("run")
    run.set_defaults(func=cmd_run)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    app_config = load_config()
    session_id = str(uuid.uuid4())
    
    with get_db_connection(app_config.database_path) as conn:
        create_db(conn)
        insert_sessions_db(
            session_id=session_id,
            command=args.command,
            conn=conn,
        )

        try:
            args.func(args, app_config, conn, session_id)
            status = "completed"
        except Exception:
            status = "failed"
        finally:
            update_session_status_db(session_id=session_id, status=status, conn=conn)

    return None