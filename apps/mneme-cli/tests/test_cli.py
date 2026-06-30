"""Tests for mneme-cli."""

from click.testing import CliRunner

from mneme_cli.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_init():
    runner = CliRunner()
    result = runner.invoke(main, ["init"])
    assert result.exit_code == 0
    assert "Tier:" in result.output


def test_status():
    runner = CliRunner()
    result = runner.invoke(main, ["status"])
    assert result.exit_code == 0


def test_recall():
    runner = CliRunner()
    result = runner.invoke(main, ["recall", "test query"])
    assert result.exit_code == 0
