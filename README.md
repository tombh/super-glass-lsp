_🚧 WIP: you're very welcome to try this, but I'm breaking a lot at the moment (October 16th)_

# CLI Tools LSP Server and/or Pygls Starting Template

(Considering a rename to "Super Glass" and moving it to a "Pygls-Org" github org)

This project has 2 goals.

1. A generic LSP server that parses CLI tools, or indeed any program that outputs to STDOUT, such as  linters, formatters, style checkers, etc and converts their output to LSP-compatible behaviour.
2. An easily-forkable template to start your own custom LSP server using [Pygls](https://github.com/openlawlibrary/pygls).

Because the heavy-lifting of this language server is done by external tooling (think `pylint`, `jq`, `markdownlint`, etc), there is minimal implementation-specific code in this repo. That is to say that the majority of the code here is applicable to any language server built with [Pygls](https://github.com/openlawlibrary/pygls). Or at the very least, it demonstrates a reasonable starting point. Deleting the `src/lsp/custom` folder should leave the codebase as close as possible to the minimum starting point for your own custom language server. Then you will also want to rename occurrences of `[C|c]ustom` to your own language server's name.

## Installation

`pip install cli-tools-lsp`

## Usage

### Quickstart
Once you've installed the language server and [set it up in your editor](#Editor Setups), it should be as easy as this to add new features:
```yaml
# This is jsut an ID, so can be anything. Internally it's important so that you can
# override existing configs (either the bundled defaults, or configs you have
# created elsewhere): all configs with the same ID are automaticallly merged. 
fuzzy_similar_words_completion:

  # This is the part of the language server to which the `command` will apply.
  # The other currently supported features are: `diagnostic`.
  lsp_feature: completion,
  
  # This is the external command which will be triggered and parsed for every
  # invocation of the feature. In the case of completions, editors will generally
  # trigger it for _every_ character change, or even every key press. So be
  # careful not to make this too expensive.
  #
  # Default behaviour is to pipe the entire contents of the file into the command.
  # This can be overriden with `piped: false`. In which case you will likely want
  # to manually do something with the file. You can access its path with the `{file}`
  # token. Eg; `command: "cat {file} | tr ..."`.
  #
  # This particular command first breaks up the file into a list of words, which are
  # then piped into a fuzzy finder, which then queries the list with the particular
  # word currently under your cursor in the editor. Finally the results of the fuzzy
  # search are deduplicated (with `uniq`).
  #
  # The command is run in a shell, so all the tools from your own machine are available.
  command: "tr -cs '[:alnum:]' '\n' | fzf --filter='{word}' | uniq"
```

## Editor Setups

### Example Neovim Lua config

Since this project is very beta, we're not yet submitting this language server to the LSP Config plugin (the defacto way to add new language servers). Therefore, for now, we have to use Neovim's vanilla LSP setup (which has actually simplified a lot recently).

```lua
vim.api.nvim_create_autocmd({ "BufEnter" }, {
  -- NB: You must remember to manually put the file extension pattern matchers for each LSP filetype
  pattern = { "*" },
  callback = function()
    vim.lsp.start({
      name = "clitools",
      cmd = { "cli-tools-lsp" },
      root_dir = vim.fs.dirname(vim.fs.find({ ".git" }, { upward = true })[1]),
      init_options = {
        configs = {
          fuzzybuffertokens = {
            lsp_feature = "completion",
            command = "tr -cs '[:alnum:]' '\n' | fzf --filter='{word}' | uniq",
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
