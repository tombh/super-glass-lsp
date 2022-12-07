import re

from pygls.workspace import position_from_utf16
from pygls.lsp.types import Range, Position
from pygls.workspace import Document as PyglsDocument

from ._base import Base


class Document(Base):
    def parse_range(
        self, start_line: int, start_char: int, end_line: int, end_char: int
    ):
        """
        Parses something like `0:0,23:3` to produce a "selection" range in a document
        """
        if self.text_doc_uri is None:
            raise Exception

        if int(end_line) == -1:
            current_document = self.get_current_document()
            end_line = len(current_document.lines)

        if int(end_char) == -1:
            # NB:
            # `end_char` may need to use something like pygls.workspace.utf16_num_units(lines[-1])
            # in order to handle wide characters. I have seen some weirdness like a single char
            # being copied on every save. But it's hard to know what's going on behind the scenes.
            end_char = 0

        return Range(
            start=Position(line=start_line, character=start_char),
            end=Position(line=end_line, character=end_char),
        )

    def range_for_whole_document(self) -> Range:
        """
        `0:0,-1:1` has the special meaning of: select the whole document.

        This is not a LSP convention.
        """
        return self.parse_range(0, 0, -1, -1)

    def get_current_document(self) -> PyglsDocument:
        if self.text_doc_uri is None:
            raise Exception

        return self.server.get_document_from_uri(self.text_doc_uri)

    def get_wordish_under_cursor(self, cursor_position: Position) -> str:
        """
        Get anything between whitespace
        """
        if self.text_doc_uri is None:
            raise Exception
        doc = self.server.get_document_from_uri(self.text_doc_uri)
        # Doesn't start with whitespace
        re_start_word = re.compile(r"[^\s]*$")
        # Doesn't end with whitespace
        re_end_word = re.compile(r"^[^\s]*")
        word = doc.word_at_position(
            cursor_position, re_start_word=re_start_word, re_end_word=re_end_word
        )
        return word

    def get_line_under_cursor(self, cursor_position: Position) -> str:
        if self.text_doc_uri is None:
            raise Exception
        doc = self.server.get_document_from_uri(self.text_doc_uri)
        lines = doc.lines
        if cursor_position.line >= len(lines):
            return ""

        row, _ = position_from_utf16(lines, cursor_position)
        line = lines[row]
        return line
