#!/usr/bin/env python3
"""Lightweight checks for the GitHub profile README and local visual assets."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
MAX_ASSET_BYTES = 5 * 1024 * 1024


def main() -> int:
    errors = []
    readme = README.read_text(encoding="utf-8")

    if not readme.strip():
        errors.append("README.md is empty.")

    for bad in ("Al-driven", "AI/ ML", " and i am passionate"):
        if bad in readme:
            errors.append(f"Outdated or incorrect wording found: {bad!r}")

    # Check local image sources and meaningful alt text on HTML image tags.
    for match in re.finditer(r"<img\b([^>]*?)>", readme, flags=re.IGNORECASE | re.DOTALL):
        attrs = match.group(1)
        alt = re.search(r'\balt\s*=\s*["\']([^"\']*)["\']', attrs, flags=re.IGNORECASE)
        src = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', attrs, flags=re.IGNORECASE)
        if not alt or not alt.group(1).strip():
            errors.append("An HTML image is missing descriptive alt text.")
        if src and src.group(1).startswith("./"):
            local_path = ROOT / src.group(1)[2:]
            if not local_path.is_file():
                errors.append(f"Local README image does not exist: {src.group(1)}")

    # Validate repository SVGs as XML and keep image assets within a reasonable size.
    for svg in ROOT.rglob("*.svg"):
        if ".git" in svg.parts:
            continue
        try:
            ET.parse(svg)
        except (ET.ParseError, OSError) as exc:
            errors.append(f"Invalid SVG/XML: {svg.relative_to(ROOT)} ({exc})")

    for folder in (ROOT / "assets",):
        if folder.exists():
            for asset in folder.iterdir():
                if asset.is_file() and asset.stat().st_size > MAX_ASSET_BYTES:
                    errors.append(
                        f"Asset exceeds 5 MiB: {asset.relative_to(ROOT)} "
                        f"({asset.stat().st_size / (1024 * 1024):.2f} MiB)"
                    )

    if errors:
        print("README validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("README validation passed: wording, image alt text, local image paths, SVG XML, and asset sizes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
