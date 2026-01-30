# Claude Code CLI Reference

## Main Commands

| Command | Description |
|---------|-------------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start REPL with initial prompt |
| `claude -p "query"` | Print mode (non-interactive, exits after response) |
| `claude -c` | Continue most recent conversation |
| `claude -r <session>` | Resume specific session by ID or name |
| `claude update` | Update to latest version |
| `claude mcp` | Configure MCP servers |

## Key Flags

| Flag | Description |
|------|-------------|
| `--print, -p` | Non-interactive output mode |
| `--continue, -c` | Continue last conversation |
| `--resume, -r` | Resume specific session |
| `--model` | Set model (sonnet, opus, haiku) |
| `--verbose` | Enable verbose logging |
| `--output-format` | Output format: text, json, stream-json |
| `--permission-mode` | Start in plan, auto, or normal mode |
| `--max-turns` | Limit agentic turns |
| `--add-dir` | Add additional working directories |

## Interactive Commands (prefix with `/`)

- `/help` - Usage help
- `/clear` - Clear conversation
- `/model` - Change model
- `/config` - Open settings
- `/context` - Show context usage
- `/cost` - Token statistics
- `/compact` - Compact conversation to save context
- `/resume` - Resume a session
- `/exit` - Exit REPL

## Keyboard Shortcuts

- `Ctrl+C` - Cancel current operation
- `Ctrl+D` - Exit session
- `Shift+Tab` - Toggle permission modes
- `Alt+P` - Switch model
- `\` + `Enter` - Multiline input
