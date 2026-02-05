"""Tests for CLI module (cli.py)"""

import argparse
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from netdiag.cli import MyParser, build_parser, cmd_dns, cmd_ping, cmd_run, main
from netdiag.config.config import AppConfig, PingConfig
from netdiag.data.ping import (
    DiagnosisCause,
    PingDiagnosis,
    PingMetrics,
    PingRecord,
    PingSignals,
)

# ============================================================================
# Fixtures - Reusable test data
# ============================================================================


@pytest.fixture
def sample_config():
    """Sample application config with two ping targets"""
    return AppConfig(
        ping=PingConfig(
            enabled=True,
            targets=["8.8.8.8", "1.1.1.1"],
            count=5,
            timeout_ms=1000,
            interval_s=1,
        ),
        database_path="test.db",
    )


@pytest.fixture
def sample_ping_record():
    """Sample successful ping record"""
    return PingRecord(
        run_id="test-run-id",
        timestamp=datetime.now(),
        target="8.8.8.8",
        metrics=PingMetrics(
            sent=5,
            received=5,
            loss_pct=0.0,
            rtt_min_ms=10.0,
            rtt_max_ms=20.0,
            rtt_avg_ms=15.0,
            rtt_stddev_ms=2.0,
            jitter=2.5,
            jitter_ratio=0.17,
        ),
        signals=PingSignals(
            no_reply=False,
            any_loss=False,
            high_loss=False,
            high_latency=False,
            unstable_jitter=False,
            unstable=False,
        ),
        diagnosis=PingDiagnosis(
            cause=DiagnosisCause.OK,
            confidence=0.95,
            summary="Connection is healthy",
            evidence={},
        ),
    )


@pytest.fixture
def mock_cmd_ping_deps():
    """Mock all dependencies for cmd_ping tests"""
    with patch("netdiag.cli.run_ping") as mock_run_ping, \
         patch("netdiag.cli.get_os_adapter") as mock_os_adapter, \
         patch("netdiag.cli.insert_ping_records_db") as mock_insert, \
         patch("netdiag.cli.format_ping_report") as mock_format:

        mock_os_adapter.return_value = Mock()
        mock_format.return_value = "formatted output"

        yield {
            "run_ping": mock_run_ping,
            "os_adapter": mock_os_adapter,
            "insert_db": mock_insert,
            "format_report": mock_format,
        }


@pytest.fixture
def mock_main_deps():
    """Mock all dependencies for main() tests"""
    with patch("netdiag.cli.build_parser") as mock_parser_builder, \
         patch("netdiag.cli.load_config") as mock_load_config, \
         patch("netdiag.cli.get_db_connection") as mock_get_conn, \
         patch("netdiag.cli.create_db") as mock_create_db, \
         patch("netdiag.cli.insert_sessionss_db") as mock_insert_session, \
         patch("netdiag.cli.update_session_status_db") as mock_update_session, \
         patch("netdiag.cli.uuid.uuid4") as mock_uuid:

        # Default setup
        mock_uuid.return_value = "test-uuid"
        mock_parser = Mock()
        mock_args = Mock(command="ping", func=Mock())
        mock_parser.parse_args.return_value = mock_args
        mock_parser_builder.return_value = mock_parser
        mock_load_config.return_value = Mock(database_path="test.db")
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        yield {
            "parser_builder": mock_parser_builder,
            "parser": mock_parser,
            "args": mock_args,
            "load_config": mock_load_config,
            "get_conn": mock_get_conn,
            "conn": mock_conn,
            "create_db": mock_create_db,
            "insert_session": mock_insert_session,
            "update_session": mock_update_session,
            "uuid": mock_uuid,
        }


# ============================================================================
# Tests
# ============================================================================


class TestMyParser:
    """Test custom argument parser with improved error messages"""

    def test_error_method_prints_usage_and_message(self, capsys):
        """Test that parser errors show usage and helpful message"""
        parser = MyParser(prog="test")
        parser.add_argument("--required", required=True)

        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "Error:" in captured.out
        assert "Run with --help for more information" in captured.out

    def test_error_includes_custom_message(self, capsys):
        """Test that custom error message is displayed"""
        parser = MyParser(prog="test")

        with pytest.raises(SystemExit):
            parser.error("custom error message")

        captured = capsys.readouterr()
        assert "custom error message" in captured.out


class TestBuildParser:
    """Test argument parser construction"""

    def test_parser_has_correct_program_name(self):
        parser = build_parser()
        assert parser.prog == "netdiag"

    def test_parser_requires_command(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_ping_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["ping"])
        assert args.command == "ping"
        assert args.func == cmd_ping

    def test_ping_accepts_count_argument(self):
        parser = build_parser()
        args = parser.parse_args(["ping", "--count", "10"])
        assert args.count == 10

        args = parser.parse_args(["ping", "-c", "5"])
        assert args.count == 5

    def test_ping_accepts_timeout_argument(self):
        parser = build_parser()
        args = parser.parse_args(["ping", "--timeout-ms", "2000"])
        assert args.timeout_ms == 2000

        args = parser.parse_args(["ping", "-t", "1500"])
        assert args.timeout_ms == 1500

    def test_ping_arguments_are_optional(self):
        parser = build_parser()
        args = parser.parse_args(["ping"])
        assert args.count is None
        assert args.timeout_ms is None

    def test_dns_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["dns"])
        assert args.command == "dns"
        assert args.func == cmd_dns

    def test_run_subcommand_exists(self):
        parser = build_parser()
        args = parser.parse_args(["run"])
        assert args.command == "run"
        assert args.func == cmd_run

    def test_invalid_subcommand_fails(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["invalid"])


class TestCmdPing:
    """Test ping command execution"""

    def test_calls_run_ping_for_each_target(
        self, mock_cmd_ping_deps, sample_config, sample_ping_record
    ):
        """Test cmd_ping executes ping for each configured target"""
        mocks = mock_cmd_ping_deps
        mocks["run_ping"].return_value = sample_ping_record

        args = argparse.Namespace(count=None, timeout_ms=None)
        cmd_ping(args, sample_config, Mock(), "test-run-id")

        assert mocks["run_ping"].call_count == 2
        calls = mocks["run_ping"].call_args_list
        assert calls[0].kwargs["host"] == "8.8.8.8"
        assert calls[0].kwargs["count"] == 5
        assert calls[0].kwargs["timeout_ms"] == 1000
        assert calls[1].kwargs["host"] == "1.1.1.1"

    def test_uses_cli_args_over_config(
        self, mock_cmd_ping_deps, sample_config, sample_ping_record
    ):
        """Test cmd_ping prioritizes CLI arguments over config"""
        mocks = mock_cmd_ping_deps
        mocks["run_ping"].return_value = sample_ping_record

        args = argparse.Namespace(count=10, timeout_ms=2000)
        cmd_ping(args, sample_config, Mock(), "test-run-id")

        call_kwargs = mocks["run_ping"].call_args.kwargs
        assert call_kwargs["count"] == 10
        assert call_kwargs["timeout_ms"] == 2000

    def test_inserts_records_to_database(
        self, mock_cmd_ping_deps, sample_config, sample_ping_record
    ):
        """Test cmd_ping stores results in database"""
        mocks = mock_cmd_ping_deps
        mocks["run_ping"].return_value = sample_ping_record

        run_id = "test-run-id"
        conn = Mock()
        args = argparse.Namespace(count=None, timeout_ms=None)
        cmd_ping(args, sample_config, conn, run_id)

        assert mocks["insert_db"].call_count == 2
        call_kwargs = mocks["insert_db"].call_args.kwargs
        assert call_kwargs["run_id"] == run_id
        assert call_kwargs["conn"] == conn
        assert call_kwargs["ping_record"] == sample_ping_record

    def test_prints_formatted_report(
        self, mock_cmd_ping_deps, sample_config, sample_ping_record, capsys
    ):
        """Test cmd_ping prints formatted output for each target"""
        mocks = mock_cmd_ping_deps
        mocks["run_ping"].return_value = sample_ping_record

        args = argparse.Namespace(count=None, timeout_ms=None)
        cmd_ping(args, sample_config, Mock(), "test-run-id")

        captured = capsys.readouterr()
        assert captured.out.count("formatted output") == 2


class TestCmdDns:
    """Test dns command execution"""

    def test_is_placeholder(self):
        """Test cmd_dns currently does nothing (placeholder)"""
        cmd_dns(Mock(), Mock(), Mock(), "test-run-id")


class TestCmdRun:
    """Test run command execution"""

    @patch("netdiag.cli.cmd_ping")
    def test_calls_cmd_ping(self, mock_cmd_ping):
        """Test cmd_run executes ping command"""
        args, config, conn, run_id = Mock(), Mock(), Mock(), "test-run-id"
        cmd_run(args, config, conn, run_id)
        mock_cmd_ping.assert_called_once_with(args, config, conn, run_id)


class TestMain:
    """Test main entry point"""

    def test_parses_args_and_loads_config(self, mock_main_deps):
        """Test main initializes and loads configuration"""
        mocks = mock_main_deps
        main()

        mocks["parser_builder"].assert_called_once()
        mocks["parser"].parse_args.assert_called_once()
        mocks["load_config"].assert_called_once()

    def test_creates_database_and_session(self, mock_main_deps):
        """Test main creates database and inserts session record"""
        mocks = mock_main_deps
        main()

        mocks["create_db"].assert_called_once_with(mocks["conn"])
        mocks["insert_session"].assert_called_once_with(
            run_id="test-uuid", command="ping", conn=mocks["conn"]
        )

    def test_calls_command_function(self, mock_main_deps):
        """Test main executes the command function"""
        mocks = mock_main_deps
        mock_func = Mock()
        mocks["args"].func = mock_func

        main()

        mock_func.assert_called_once()

    def test_updates_session_status_on_success(self, mock_main_deps):
        """Test main marks session as completed on success"""
        mocks = mock_main_deps
        main()

        mocks["update_session"].assert_called_once_with(
            run_id="test-uuid", status="completed", conn=mocks["conn"]
        )

    def test_updates_session_status_on_failure(self, mock_main_deps):
        """Test main marks session as failed on exception"""
        mocks = mock_main_deps
        mocks["args"].func = Mock(side_effect=RuntimeError("Test error"))

        main()

        mocks["update_session"].assert_called_once_with(
            run_id="test-uuid", status="failed", conn=mocks["conn"]
        )

    def test_returns_none(self, mock_main_deps):
        """Test main returns None"""
        result = main()
        assert result is None
