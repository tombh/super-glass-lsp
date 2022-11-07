import typing
from typing import Dict, Optional, List

import pytest  # noqa

from pygls.workspace import Document

from super_glass_lsp.lsp.custom.config_definitions import Configs
from super_glass_lsp.lsp.server import CustomLanguageServer


def create_server(
    mocker,
    configs: Dict,
    outputs: Optional[List[str]] = None,
    source: Optional[str] = "",
):
    uri = "file:///"
    mocker.patch(
        "super_glass_lsp.lsp.server.CustomLanguageServer.get_document_from_uri",
        return_value=Document(language_id="testing", uri=uri, source=source),
    )

    mocker.patch(
        "pygls.workspace.Document.source",
        return_value="",
    )

    subprocess_mock = mocker.patch(
        "super_glass_lsp.lsp.custom.features._subprocess.Subprocess.run",
        side_effect=outputs,
    )

    server = CustomLanguageServer()
    server.config = Configs(**typing.cast(Dict, {"configs": configs}))
    return server, uri, subprocess_mock
