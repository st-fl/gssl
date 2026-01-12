#!/usr/bin/env python3
"""
Generate a player card PDF from an SVG template.

Usage:
    # Single player
    uv run python main.py "John Doe" "1990-01-15"
    uv run python main.py "John Doe" "1990-01-15" "2026-01-12"

    # Batch from YAML file
    uv run python main.py --batch players.yaml
"""

import argparse
import os
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import cairosvg
import yaml
from pypdf import PageObject, PdfReader, PdfWriter


def update_svg_text(
    svg_content: str, name: str, dob: str, issue_date: str, expiration_date: str
) -> str:
    """Update text elements in SVG by their id."""
    replacements = {
        "NameField": name,
        "DOBField": dob,
        "IssuedDate": issue_date,
        "ExpirationDate": expiration_date,
    }

    updated_svg = svg_content
    for field_id, new_text in replacements.items():
        # Try multiple patterns to match different SVG text structures
        patterns = [
            # Pattern 1: <text id="FieldName">content</text>
            rf'(<text[^>]*id="{field_id}"[^>]*>)([^<]*)(</text>)',
            # Pattern 2: <text id="FieldName"><tspan>content</tspan></text>
            rf'(<text[^>]*id="{field_id}"[^>]*><tspan[^>]*>)([^<]*)(</tspan></text>)',
            # Pattern 3: id attribute with different quote styles or positions
            rf"(<text[^>]*id='{field_id}'[^>]*>)([^<]*)(</text>)",
        ]

        for pattern in patterns:
            match = re.search(pattern, updated_svg)
            if match:
                updated_svg = re.sub(
                    pattern,
                    lambda m: f"{m.group(1)}{new_text}{m.group(3)}",
                    updated_svg,
                )
                break

    return updated_svg


def slugify_name(name: str) -> str:
    """Convert player name to a safe filename."""
    return name.lower().replace(" ", "_").replace("-", "_")


def generate_card(
    name: str, dob: str, issue_date: datetime, output_dir: Path, fonts_dir: Path
) -> str:
    """Generate a player card PDF and return the output path."""
    # Calculate expiration date (1 week from issue date)
    expiration_date = issue_date + timedelta(weeks=1)

    # Format dates
    issue_date_str = issue_date.strftime("%Y-%m-%d")
    expiration_date_str = expiration_date.strftime("%Y-%m-%d")

    # Read the SVG template for page 1
    svg_path = Path("page1.svg")
    svg_content = svg_path.read_text()

    # Update the SVG with new text
    updated_svg = update_svg_text(
        svg_content, name, dob, issue_date_str, expiration_date_str
    )

    # Write to temporary file and convert to PDF
    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp_svg:
        tmp_svg.write(updated_svg)
        tmp_svg_path = tmp_svg.name

    tmp_pdf = tempfile.mktemp(suffix=".pdf")
    try:
        # Convert page1 SVG to PDF
        cairosvg.svg2pdf(url=tmp_svg_path, write_to=tmp_pdf)

        # Read both PDFs to get dimensions
        with open(tmp_pdf, "rb") as f:
            page1_reader = PdfReader(f)
            page1 = page1_reader.pages[0]
            page1_width = float(page1.mediabox.width)
            page1_height = float(page1.mediabox.height)

        with open("page2.pdf", "rb") as f:
            page2_reader = PdfReader(f)
            page2 = page2_reader.pages[0]
            page2_width = float(page2.mediabox.width)

        # Calculate scale factor to size page2 down to page1
        scale = page1_width / page2_width

        # Create merged PDF with both pages at page1 size
        merger = PdfWriter()

        # Add page1 as-is
        merger.append(tmp_pdf)

        # Scale page2 down to match page1
        with open("page2.pdf", "rb") as f:
            reader = PdfReader(f)
            page = reader.pages[0]

            # Create new page with page1 dimensions
            scaled_page = PageObject.create_blank_page(
                width=page1_width, height=page1_height
            )

            # Apply transformation to scale page2 down
            page.scale_by(scale)
            scaled_page.merge_page(page)

            merger.add_page(scaled_page)

        # Generate output filename based on player name
        output_filename = f"{slugify_name(name)}.pdf"
        output_path = output_dir / output_filename

        merger.write(str(output_path))
        merger.close()

        print(f"✓ Generated {output_path}")
        print(f"  Name: {name}")
        print(f"  DOB: {dob}")
        print(f"  Issued: {issue_date_str}")
        print(f"  Expires: {expiration_date_str}")

        return str(output_path)
    finally:
        # Clean up temporary files
        Path(tmp_svg_path).unlink()
        Path(tmp_pdf).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate player card PDF from SVG template"
    )
    parser.add_argument(
        "--batch", help="YAML file with player data for batch generation"
    )
    parser.add_argument("name", nargs="?", help="Player name")
    parser.add_argument("dob", nargs="?", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument(
        "issue_date", nargs="?", help="Issue date (YYYY-MM-DD), defaults to today"
    )
    args = parser.parse_args()

    # Configure fontconfig to use bundled fonts
    fonts_dir = Path(__file__).parent / "fonts"
    os.environ["FONTCONFIG_FILE"] = str(fonts_dir / "fonts.conf")
    os.environ["FONTCONFIG_PATH"] = str(fonts_dir)

    # Create outputs directory
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    if args.batch:
        # Batch mode: process YAML file
        with open(args.batch) as f:
            players = yaml.safe_load(f)

        if not isinstance(players, list):
            print("Error: YAML file must contain a list of player entries")
            return

        print(f"Processing {len(players)} players from {args.batch}...\n")

        for player in players:
            name = player.get("name")
            dob = player.get("dob")
            issue_date_str = player.get("issue_date")

            if not name or not dob:
                print(f"⚠ Skipping entry with missing name or dob: {player}")
                continue

            # Parse issue date (default to today)
            if issue_date_str:
                issue_date = datetime.strptime(issue_date_str, "%Y-%m-%d")
            else:
                issue_date = datetime.now()

            generate_card(name, dob, issue_date, output_dir, fonts_dir)
            print()

        print(f"✓ Batch complete: {len(players)} cards generated in {output_dir}/")
    else:
        # Single player mode
        if not args.name or not args.dob:
            parser.error("name and dob are required when not using --batch")

        # Parse issue date (default to today)
        if args.issue_date:
            issue_date = datetime.strptime(args.issue_date, "%Y-%m-%d")
        else:
            issue_date = datetime.now()

        generate_card(args.name, args.dob, issue_date, output_dir, fonts_dir)


if __name__ == "__main__":
    main()
