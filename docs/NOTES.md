## Configs

### Nvim LSPConfig
```lua
local util = require 'lspconfig.util'

return {
  default_config = {
    cmd = { 'python3', '/home/streamer/Workspace/cli-tools-lsp/src/main.py' },
    filetypes = { 'python' },
    root_dir = util.find_git_ancestor,
  },
  docs = {
    description = [[
Heyyyyyyy these are the docs
]],
  },
}
```
