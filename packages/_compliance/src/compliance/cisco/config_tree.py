import re
from collections.abc import Iterator
from dataclasses import dataclass, field

from netutils.config.compliance import parser_map
from netutils.lib_mapper import NETUTILSPARSER_LIB_MAPPER_REVERSE


@dataclass(eq=False, kw_only=True)
class ConfigLine:
    """
    One line of a config

    Args:
        text: The line without its indent
        parents: The lines above it in the tree, outermost first
    """

    text: str
    parents: tuple[str, ...] = ()
    children: list["ConfigLine"] = field(default_factory=list)

    @property
    def path(self) -> str:
        """
        The line with its parents, for a report: `line vty 0 4 > transport input telnet`
        """
        return " > ".join((*self.parents, self.text))

    def descendants(self) -> Iterator["ConfigLine"]:
        for child in self.children:
            yield child
            yield from child.descendants()


class ConfigTree:
    """
    A device config as a tree of lines

    Rules use this class and not the parser library. The parser (netutils) knows the banners and
    the comments of each network OS.

    Args:
        top: The lines without a parent
        lines: Each config line, top to bottom. The text of a banner is not a config line: it is
            the child of its `banner` line, and `find` does not search it
    """

    def __init__(self, text: str, *, network_os: str) -> None:
        """
        Raises:
            LookupError: If there is no parser for the network OS
        """
        parser = parser_map.get(NETUTILSPARSER_LIB_MAPPER_REVERSE.get(network_os, network_os))
        if parser is None:
            raise LookupError(f"no config parser for network OS {network_os}")

        self.top: list[ConfigLine] = []
        self.lines: list[ConfigLine] = []
        # The last line seen at each depth
        open_lines: list[ConfigLine] = []
        for parsed in parser(text).config_lines:
            depth = len(parsed.parents)
            line = ConfigLine(text=parsed.config_line.strip(), parents=tuple(p.strip() for p in parsed.parents))
            (open_lines[depth - 1].children if depth else self.top).append(line)
            open_lines[depth:] = [line]
            # The parser returns the text of a banner as one line with line breaks
            if "\n" not in line.text:
                self.lines.append(line)

    def find(self, pattern: str, *, top_level: bool = False) -> list[ConfigLine]:
        """
        Lines that the pattern matches (re.search on the text of the line)

        Args:
            top_level: Search only lines without a parent, e.g. to find `interface` sections
        """
        lines = self.top if top_level else self.lines
        return [line for line in lines if re.search(pattern, line.text)]
