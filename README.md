# CLI Tools LSP server

Parses the output of linters, formatters, style checkers, etc and converts them to LSP.

Inspired by: https://github.com/mattn/efm-langserver#example-for-configyaml

Probably will only ever support LSP diagnostics and formatting.

### Example Neovim Lua config

```lua
clitool_configs = {
	{
		language_id = "markdown",
		command = { "markdownlint", "--stdin" },
		parsing = {
			formats = {
				"stdin:{line:d}:{col:d} {msg}",
				"stdin:{line:d} {msg}",
				"stdin {msg}",
			},
			line_offset = -1,
			col_offset = -1,
		},
	},
	{
		language_id = "json",
		command = { "jq", "." },
		parsing = {
			formats = { "{msg} at line {line:d}, column {col:d}" },
		},
	},
},
```

## Testing

`poetry run python -m pytest`
