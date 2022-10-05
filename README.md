# CLI Tools LSP server

Parses the output of linters, formatters, style checkers, etc and converts them to LSP.

Inspired by: https://github.com/mattn/efm-langserver#example-for-configyaml

Probably will only ever support LSP diagnostics and formatting.

### TODO
* [ ] Configs for various editors
* [ ] Docs
* [ ] Use public version of Pygls
* [ ] Add tests

## Testing

`poetry run python -m pytest`
