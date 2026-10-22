"""Create the portfolio archive from the current workspace only."""

import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "InsightFlow-Portfolio.zip"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
    ".tmp",
    ".pnpm-store",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-results",
}
EXCLUDED_FILES = {".env", ".DS_Store", DESTINATION.name}


def include_file(path: Path) -> bool:
    name = path.name
    return not (
        name in EXCLUDED_FILES
        or name.startswith(".env.")
        and name != ".env.example"
        or name.endswith((".pyc", ".pyo", ".tsbuildinfo", ".egg-info"))
    )


with zipfile.ZipFile(
    DESTINATION, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8
) as archive:
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [
            name
            for name in dirs
            if name not in EXCLUDED_DIRS and not name.endswith(".egg-info")
        ]
        for name in files:
            path = Path(directory) / name
            if include_file(path):
                archive.write(
                    path, (Path("InsightFlow") / path.relative_to(ROOT)).as_posix()
                )

with zipfile.ZipFile(DESTINATION) as archive:
    if archive.testzip() is not None:
        raise SystemExit("Archive integrity check failed")
    names = archive.namelist()
    required = [
        "README.md",
        "compose.yaml",
        "frontend/package.json",
        "backend/pyproject.toml",
        "backend/migrations/versions/001_initial.py",
        "sample-data/small_sales.csv",
    ]
    missing = [name for name in required if f"InsightFlow/{name}" not in names]
    if missing:
        raise SystemExit(f"Missing required archive entries: {missing}")
print(
    f"Created {DESTINATION} with {len(names)} files ({DESTINATION.stat().st_size:,} bytes)"
)
