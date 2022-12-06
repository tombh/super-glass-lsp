from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from super_glass_lsp.lsp.server import CustomLanguageServer

from parse import parse  # type: ignore

from pygls.lsp.types import Position, Location

from super_glass_lsp.lsp.custom.config_definitions import LSPFeature
from super_glass_lsp.lsp.custom.features._feature import Feature


class GotoDefinition(Feature):
    @classmethod
    async def run_all(
        cls,
        server: "CustomLanguageServer",
        text_doc_uri: str,
        cursor_position: Position,
    ) -> Optional[List[Location]]:
        language_id = server.get_document_from_uri(text_doc_uri).language_id
        configs = server.custom.get_all_config_by(
            LSPFeature.goto_definition, language_id
        )
        definitions = []
        for id, config in configs.items():
            definer = cls(server, id, text_doc_uri)
            server.logger.debug(f"Running Goto Definition request for: {id}: {config}")
            location = await definer.get_location(cursor_position)
            definitions.extend(location)

        return definitions

    async def get_location(self, cursor_position: Position) -> List[Location]:
        default_format = "{uri} {start_line}:{start_char},{end_line}:{end_char}"
        word = self.get_wordish_under_cursor(cursor_position)
        line = self.get_line_under_cursor(cursor_position)
        output = await self.run_cli_tool(line, word, cursor_position)

        locations = []
        for line in output.splitlines():
            parsed = parse(default_format, output)
            if parsed is None:
                continue
            location = Location(
                uri=f'file://{parsed["uri"]}',  # TODO: formalise workspace_root/file:/// usage
                range=self.parse_range(
                    parsed["start_line"],
                    parsed["start_char"],
                    parsed["end_line"],
                    parsed["end_char"],
                ),
            )
            locations.append(location)

        return locations

    async def run_cli_tool(
        self,
        line: str,
        word: str,
        cursor_position: Position,
    ) -> str:
        self.server.logger.debug("!!!!!!!!!!!!!!!!!!!!!!!")
        self.server.logger.debug(line)
        self.server.logger.debug("!!!!!!!!!!!!!!!!!!!!!!!")
        replacements = [
            ("{line}", line),
            ("{word}", word),
            ("{cursor_line}", str(cursor_position.line)),
            ("{cursor_char}", str(cursor_position.character)),
        ]
        commands = self.resolve_commands(replacements)

        await self.run_pre_commands(commands)
        if isinstance(commands, list):
            final_command = commands[-1]
        else:
            final_command = commands
        result = await self.shell(final_command)
        return result.stdout
