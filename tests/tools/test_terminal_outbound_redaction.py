"""Outbound CLI command redaction for terminal-driven notifications."""

from tools.terminal_tool import _mask_outbound_cli_command


def test_lark_cli_message_send_command_is_redacted():
    raw_secret = "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz123456"
    command = (
        "lark-cli im +messages-send --as bot --user-id ou_x "
        f"--text 'leaked {raw_secret}'"
    )

    result = _mask_outbound_cli_command(command)

    assert raw_secret not in result
    assert "sk-ant" in result


def test_multica_issue_comment_heredoc_is_redacted():
    raw_secret = "app_secret=cli_secret_abcdef1234567890"
    command = (
        "multica issue comment add WS-270 --content-stdin <<'EOF'\n"
        f"{raw_secret}\n"
        "EOF"
    )

    result = _mask_outbound_cli_command(command)

    assert "cli_secret_abcdef" not in result
    assert "app_secret=" in result


def test_non_outbound_command_is_not_rewritten():
    raw_secret = "sk-ant-api03-AbCdEfGhIjKlMnOpQrStUvWxYz123456"
    command = f"python -c 'print(\"{raw_secret}\")'"

    assert _mask_outbound_cli_command(command) == command
