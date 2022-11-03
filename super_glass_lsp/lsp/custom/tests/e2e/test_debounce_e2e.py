# Ideas for testing if debounce works in the server thread.
#
# We already have unit tests for debouncing, they depend on counting calls
# with pytest.mocker to `Feature._subprocess_run`, which we don't have access
# to in e2e tests.
#
# Parsing log lines, or sending special LSP messages to the client?
