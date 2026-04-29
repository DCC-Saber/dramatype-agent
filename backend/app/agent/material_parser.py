"""Read and parse markdown material into structured sections."""

from pathlib import Path

from app.core.paths import DEFAULT_INPUT_PATH


def read_material(input_path: Path | None = None) -> str:
    """Read material markdown file. Falls back to default if not specified."""
    path = input_path or DEFAULT_INPUT_PATH
    if not path.exists():
        raise FileNotFoundError(f"Input material not found: {path}")
    return path.read_text(encoding="utf-8")


def parse_material_sections(material_text: str) -> dict:
    """
    Simple rule-based parser: splits markdown by # headings into sections.
    Never crashes — always returns at least raw_text.
    """
    sections: dict[str, str] = {"raw_text": material_text}

    current_key = None
    current_lines: list[str] = []

    heading_map = {
        "剧集基本信息": "basic_info",
        "剧集信息": "basic_info",
        "基本信息": "basic_info",
        "角色设定": "characters",
        "角色": "characters",
        "关键剧情节点": "nodes",
        "剧情节点": "nodes",
        "安全边界": "safety",
        "安全": "safety",
    }

    for line in material_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            # flush previous section
            if current_key and current_lines:
                sections[current_key] = "\n".join(current_lines)
            # detect new section
            heading_text = stripped.lstrip("#").strip()
            current_key = heading_map.get(heading_text)
            current_lines = []
        else:
            current_lines.append(line)

    # flush last section
    if current_key and current_lines:
        sections[current_key] = "\n".join(current_lines)

    return sections
