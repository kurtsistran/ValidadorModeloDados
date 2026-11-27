"""Split a physical data-type text into its base name and arguments.

The Erwin export and the SM077 document both store the type as text, for
example ``DECIMAL(11,2)`` or ``INT NOT NULL``. Length, precision, and scale
are not separate fields in the export, so they are read from this text.
"""

import re
from dataclasses import dataclass

_TRAILING = re.compile(r"\s+(NOT\s+NULL|NULL|IDENTITY(\s*\([^)]*\))?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class PhysicalType:
    """A type name and the values written between parentheses."""

    base: str
    arguments: tuple[str, ...]
    has_parentheses: bool

    def normalized(self) -> str:
        """Comparable text, independent of spacing and case."""
        if not self.has_parentheses:
            return self.base
        return f"{self.base}({','.join(self.arguments)})"


def parse_physical_type(text: str) -> PhysicalType:
    """Parse ``text``. An empty text produces an empty base name."""
    cleaned = " ".join(text.split()).upper()
    previous = None
    while previous != cleaned:
        previous = cleaned
        cleaned = _TRAILING.sub("", cleaned).strip()
    if "(" not in cleaned:
        return PhysicalType(base=cleaned, arguments=(), has_parentheses=False)
    base, _, rest = cleaned.partition("(")
    inside = rest.rsplit(")", 1)[0]
    arguments = tuple(part.strip() for part in inside.split(",") if part.strip())
    return PhysicalType(base=base.strip(), arguments=arguments, has_parentheses=True)
