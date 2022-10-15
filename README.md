# CLI Tools LSP Server and/or Pygls Starting Template

This project has 2 goals.

1. A generic LSP server that parses CLI tools, or indeed any program that outputs to STDOUT, such as  linters, formatters, style checkers, etc and converts their output to LSP-compatible behaviour.
2. An easily-forkable template to start your own custom LSP server using [Pygls](https://github.com/openlawlibrary/pygls).

Because the heavy-lifting of this language server is done by external tooling (think `pylint`, `jq`, `markdownlint`, etc), there is minimal implementation-specific code in this repo. That is to say that the majority of the code here is applicable to any language server built with Pygls. Or at the very least, it demonstrates a reasonable starting point. Deleting the `src/lsp/custom` folder should leave the codebase as close as possible to the minimum starting point for your own custom language server. You will also want to rename occurrences of `[C|c]ustom` to your own language server's name.

## Installation

`pip install cli-tools-lsp`

## Usage

### Example Neovim Lua config

Since this project is very beta, we're not yet submitting this language server to the LSP Config plugin (the defacto way to add new language servers). Therefore, for now, we have to use Neovim's vanilla LSP setup (which has actually simplified a lot recently).

```lua
vim.api.nvim_create_autocmd({ "BufEnter" }, {
	-- NB: You must remember to manually put the file extension matchers for each LSP filetype
	pattern = { "*.md", "*.json" },
	callback = function()
		vim.lsp.start({
			name = "clitools",
  			cmd = { "cli-tools-lsp" },
			root_dir = vim.fs.dirname(vim.fs.find({ "setup.py", "pyproject.toml" }, { upward = true })[1]),
			init_options = {
				configs = {
					markdownlint = {
						enabled = "false",
						lsp_feature = "diagnostic",
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
					jqlint = {
						lsp_feature = "diagnostic",
						language_id = "json",
						command = { "jq", "." },
						parsing = {
							formats = { "{msg} at line {line:d}, column {col:d}" },
						},
					},
					fuzzybuffertokens = {
						enabled = true,
						lsp_feature = "completion",
						language_id = "python",
						command = {
							"bash",
							"-c",
							-- # `{cursor_line}` and `{cursor_row}` should also be available
							"cat {file} | tr -cs '[:alnum:]' '\n' | fzf --filter='{word}' | uniq",
						},
					},
				}
			},
		})
	end,
})
```

## Testing

Uses [@alcarney](https://github.com/alcarney)'s [pytest-lsp module](https://github.com/alcarney/lsp-devtools/tree/develop/lib/pytest-lsp) for end-to-end testing.

`poetry run python -m pytest`

## Acknowledgements

This projects takes a lot of inspiration from [@alcarney](https://github.com/alcarney)'s fantastic Sphinx/RST LSP server [Esbonio](https://github.com/swyddfa/esbonio). 

## Other generic LSP servers

* https://github.com/iamcco/diagnostic-languageserver
* https://github.com/mattn/efm-langserver
* https://github.com/jose-elias-alvarez/null-ls.nvim (Neovim only)
