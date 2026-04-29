from pathlib import Path

# backend/
BASE_DIR = Path(__file__).resolve().parents[2]

# backend/data/
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# backend/schemas/
SCHEMA_DIR = BASE_DIR / "schemas"

# Convenience paths
DEFAULT_INPUT_PATH = INPUT_DIR / "wugang_letters_material.md"
DEFAULT_OUTPUT_PATH = OUTPUT_DIR / "wugang_letters_content_pack.json"
CONTENT_PACK_SCHEMA_PATH = SCHEMA_DIR / "content_pack.schema.json"
