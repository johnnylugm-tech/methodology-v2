"""SPEC.md Parser Module.

Parses SPEC.md files and extracts structured feature information including:
- Feature IDs (F1, F2, etc.)
- Feature names
- Descriptions
- Acceptance criteria
- Priority levels
- Dependencies
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class SpecParseError(Exception):
    """Exception raised when SPEC.md parsing fails.

    Attributes:
        code: Error code string (E_FILE_NOT_FOUND, E_NOT_MARKDOWN, E_PARSE_FAILED)
        message: Human-readable error message
    """

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class ParseError:
    """Record of a parsing error.

    Attributes:
        line_number: Line where error occurred
        error_type: Type of error
        details: Additional error details
    """

    line_number: int
    error_type: str
    details: str


@dataclass
class FeatureItem:
    """Represents a single feature item from SPEC.md.

    Attributes:
        id: Feature ID (e.g., "F1", "F2")
        name: Feature name
        description: Feature description text
        acceptance_criteria: List of acceptance criteria
        priority: Priority level (P0, P1, P2)
        depends_on: List of feature IDs this depends on
        line_number: Line number in SPEC.md
        raw_text: Raw markdown text of the feature
    """

    id: str
    name: str
    description: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    priority: str = "P2"
    depends_on: list[str] = field(default_factory=list)
    line_number: int = 0
    raw_text: str = ""


@dataclass
class SpecMetadata:
    """Metadata extracted from SPEC.md header.

    Attributes:
        title: Document title
        version: Document version
        created_date: Creation date
    """

    title: str = ""
    version: str = ""
    created_date: str = ""


@dataclass
class ParseStats:
    """Statistics from parsing operation.

    Attributes:
        total_lines: Total number of lines in SPEC.md
        parsed_features: Number of features successfully parsed
        parse_success_rate: Success rate as a float between 0 and 1
        errors: List of parsing errors encountered
    """

    total_lines: int = 0
    parsed_features: int = 0
    parse_success_rate: float = 1.0
    errors: list[ParseError] = field(default_factory=list)


@dataclass
class ParsedSpec:
    """Result of parsing SPEC.md.

    Attributes:
        feature_items: List of extracted feature items
        metadata: Document metadata
        parse_stats: Parsing statistics
    """

    feature_items: list[FeatureItem]
    metadata: SpecMetadata = field(default_factory=SpecMetadata)
    parse_stats: ParseStats = field(default_factory=ParseStats)


class SpecParser:
    """Parser for SPEC.md files.

    Extracts structured feature information from Markdown-formatted
    specification files.

    Attributes:
        spec_path: Path to the SPEC.md file
        _errors: Internal list of parsing errors
    """

    # Regex patterns for parsing
    FEATURE_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+F(\d+):\s+(.+)$")
    METADATA_PATTERN = re.compile(r"^\*\*(\w+)：\*\*\s*(.+)$|^\*\*(\w+):\*\*\s*(.+)$")
    DEPENDS_PATTERN = re.compile(r"\*\*依賴[：:][*]*\s*(.+?)(?:\n|$)")
    PRIORITY_PATTERN = re.compile(r"\*\*優先權\*\*：\s*(P\d)")
    CRITERIA_PATTERN = re.compile(r"\*\*驗收標準：\*\*\s*(.+?)(?:\n|$)")
    FEATURE_BLOCK_PATTERN = re.compile(r"### F(\d+):\s+(.+)")
    FEATURE_BLOCK_HEADER = re.compile(r"^#{1,4}\s+F\d+:")

    def __init__(self, spec_path: str | Path) -> None:
        """Initialize the parser with a SPEC.md file path.

        Args:
            spec_path: Path to the SPEC.md file

        Raises:
            SpecParseError: If file doesn't exist or isn't a Markdown file
        """
        self.spec_path = str(spec_path)
        self._errors: list[ParseError] = []

        if not Path(self.spec_path).exists():
            raise SpecParseError(
                code="E_FILE_NOT_FOUND",
                message=f"SPEC.md file not found: {self.spec_path}"
            )

        if not self.spec_path.endswith(".md"):
            raise SpecParseError(
                code="E_NOT_MARKDOWN",
                message=f"File is not a Markdown file: {self.spec_path}"
            )

    def parse(self) -> ParsedSpec:
        """Parse the SPEC.md file.

        Returns:
            ParsedSpec: Structured representation of the specification

        Raises:
            SpecParseError: If parsing fails critically
        """
        self._errors = []

        try:
            content = self._load_file()
        except SpecParseError:
            raise

        lines = self._normalize_lines(content)
        feature_items = self._parse_features(lines)
        metadata = self._parse_metadata(lines)

        total_lines = len(lines)
        parsed_features = len(feature_items)
        success_rate = self._calculate_success_rate(parsed_features, total_lines)

        parse_stats = ParseStats(
            total_lines=total_lines,
            parsed_features=parsed_features,
            parse_success_rate=success_rate,
            errors=self._errors.copy()
        )

        return ParsedSpec(
            feature_items=feature_items,
            metadata=metadata,
            parse_stats=parse_stats
        )

    def get_error_log(self) -> list[ParseError]:
        """Get the list of errors encountered during parsing.

        Returns:
            list[ParseError]: Copy of the error log
        """
        return self._errors.copy()

    def _load_file(self) -> str:
        """Load the SPEC.md file content.

        Returns:
            str: File content

        Raises:
            SpecParseError: If file cannot be read
        """
        try:
            with open(self.spec_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise SpecParseError(
                code="E_PARSE_FAILED",
                message=f"Failed to read SPEC.md: {str(e)}"
            )

    def _normalize_lines(self, content: str) -> list[str]:
        """Normalize line endings and split into lines.

        Args:
            content: Raw file content

        Returns:
            list[str]: Normalized lines
        """
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        return content.split("\n")

    def _parse_features(self, lines: list[str]) -> list[FeatureItem]:
        """Parse feature items from SPEC.md lines.

        Args:
            lines: Normalized lines from SPEC.md

        Returns:
            list[FeatureItem]: List of extracted features
        """
        feature_items: list[FeatureItem] = []
        current_feature: Optional[FeatureItem] = None
        current_block_lines: list[str] = []
        in_feature_block = False

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()

            # Check for feature header
            header_match = self.FEATURE_BLOCK_PATTERN.match(line)
            if header_match:
                # Save previous feature
                if current_feature is not None:
                    current_feature.raw_text = "\n".join(current_block_lines)
                    feature_items.append(current_feature)

                # Start new feature
                feature_id = f"F{header_match.group(1)}"
                feature_name = header_match.group(2)
                current_feature = FeatureItem(
                    id=feature_id,
                    name=feature_name,
                    line_number=line_num
                )
                current_block_lines = [line]
                in_feature_block = True
                continue

            if in_feature_block and current_feature is not None:
                # Check for metadata patterns
                metadata_match = self.METADATA_PATTERN.match(line)
                if metadata_match:
                    key = metadata_match.group(1) or metadata_match.group(3)
                    value = metadata_match.group(2) or metadata_match.group(4)

                    if key == "描述":
                        current_feature.description = value
                    elif key == "優先權" and value.startswith("P"):
                        current_feature.priority = value

                # Check for acceptance criteria
                criteria_match = self.CRITERIA_PATTERN.search(line)
                if criteria_match:
                    criteria_str = criteria_match.group(1)
                    current_feature.acceptance_criteria = [
                        c.strip() for c in criteria_str.split(";")
                    ]

                # Check for dependencies
                depends_match = self.DEPENDS_PATTERN.search(line)
                if depends_match:
                    depends_str = depends_match.group(1)
                    depends_ids = re.findall(r"F\d+", depends_str)
                    current_feature.depends_on = depends_ids

                current_block_lines.append(line)

                # Check for next feature header (end of current block)
                if line.startswith("### F") and "F" in line:
                    next_feature_match = re.match(r"^### F(\d+):", line)
                    if next_feature_match:
                        next_id = int(next_feature_match.group(1))
                        current_id = int(current_feature.id[1:])
                        if next_id > current_id:
                            in_feature_block = False

        # Don't forget the last feature
        if current_feature is not None:
            current_feature.raw_text = "\n".join(current_block_lines)
            feature_items.append(current_feature)

        return feature_items

    def _parse_metadata(self, lines: list[str]) -> SpecMetadata:
        """Parse metadata from SPEC.md header.

        Args:
            lines: Normalized lines from SPEC.md

        Returns:
            SpecMetadata: Extracted metadata
        """
        metadata = SpecMetadata()

        for line in lines[:20]:  # Check first 20 lines for metadata
            line = line.strip()

            if line.startswith("**版本：**") or line.startswith("**版本:**"):
                match = re.search(r"\*\*版本[：:]\*\*\s*(.+)", line)
                if match:
                    metadata.version = match.group(1).strip()

            elif line.startswith("**創建日期：**") or line.startswith("**創建日期:**"):
                match = re.search(r"\*\*創建日期[：:]\*\*\s*(.+)", line)
                if match:
                    metadata.created_date = match.group(1).strip()

            elif line.startswith("# Feature #"):
                match = re.search(r"# Feature #(\d+):\s+(.+)", line)
                if match:
                    metadata.title = match.group(2).strip()

        return metadata

    def _calculate_success_rate(self, parsed_features: int, total_lines: int) -> float:
        """Calculate the parse success rate.

        Args:
            parsed_features: Number of features successfully parsed
            total_lines: Total number of lines in file

        Returns:
            float: Success rate between 0 and 1
        """
        if total_lines == 0:
            return 0.0

        # Simple success rate based on feature count vs expected
        # This is a simplified calculation
        expected_features = parsed_features + len(self._errors)
        if expected_features == 0:
            return 1.0

        return min(1.0, parsed_features / max(1, expected_features))
