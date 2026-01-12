#!/usr/bin/env python3
"""
Generate a player card PDF from an SVG template.

Usage:
    # Single player (dates can be YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, or MM/DD/YYYY)
    uv run python main.py "John Doe" "1990-01-15"
    uv run python main.py "John Doe" "01/15/1990" "01/12/2026"

    # Batch from YAML file
    uv run python main.py --batch players.yaml
"""

import argparse
import os
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

import cairosvg
import yaml
from pypdf import PageObject, PdfReader, PdfWriter


def update_svg_text(
    svg_content: str, name: str, dob: str, issue_date: str, expiration_date: str
) -> str:
    """Update text elements in SVG by their id.

    Escapes user input to prevent XML injection and validates that all
    required field IDs are found in the SVG.

    Raises:
        ValueError: If any required field id is not found in the SVG.
    """
    # Escape user input to prevent XML injection
    replacements = {
        "NameField": escape(name),
        "DOBField": escape(dob),
        "IssuedDate": escape(issue_date),
        "ExpirationDate": escape(expiration_date),
    }

    updated_svg = svg_content
    missing_ids: list[str] = []

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

        replaced = False
        for pattern in patterns:
            new_svg, count = re.subn(
                pattern,
                lambda m: f"{m.group(1)}{new_text}{m.group(3)}",
                updated_svg,
            )
            if count > 0:
                updated_svg = new_svg
                replaced = True
                break

        if not replaced:
            missing_ids.append(field_id)

    if missing_ids:
        raise ValueError(
            f"Missing expected SVG text element id(s): {', '.join(missing_ids)}"
        )

    return updated_svg


def parse_date(date_input: str | datetime) -> datetime:
    """Parse date string in multiple formats: YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, MM/DD/YYYY."""
    # If already a datetime object, return it
    if isinstance(date_input, datetime):
        return date_input

    # If it's a date object (from YAML parsing), convert to datetime
    from datetime import date

    if isinstance(date_input, date):
        return datetime.combine(date_input, datetime.min.time())

    # Otherwise, parse the string
    formats = [
        "%Y-%m-%d",  # YYYY-MM-DD
        "%Y/%m/%d",  # YYYY/MM/DD
        "%m-%d-%Y",  # MM-DD-YYYY
        "%m/%d/%Y",  # MM/DD/YYYY
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_input, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Unable to parse date '{date_input}'. Expected formats: YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, or MM/DD/YYYY"
    )


def slugify_name(name: str) -> str:
    """Convert player name to a safe filename.

    Non-alphanumeric characters are replaced with underscores, and the result
    is lowercased. Falls back to "card" if the slug becomes empty.
    """
    # Replace any non-alphanumeric character with underscore
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_").lower()
    if not slug:
        slug = "card"
    return slug


def generate_card(name: str, dob: str, issue_date: datetime, output_dir: Path) -> str:
    """Generate a player card PDF and return the output path."""
    # Parse and format DOB (without leading zeroes)
    dob_date = parse_date(dob)
    dob_formatted = f"{dob_date.month}/{dob_date.day}/{dob_date.year}"

    # Calculate expiration date (1 week from issue date)
    expiration_date = issue_date + timedelta(weeks=1)

    # Format dates without leading zeroes (M/D/YYYY)
    issue_date_str = f"{issue_date.month}/{issue_date.day}/{issue_date.year}"
    expiration_date_str = (
        f"{expiration_date.month}/{expiration_date.day}/{expiration_date.year}"
    )

    # Use __file__-relative paths instead of CWD
    base_dir = Path(__file__).parent
    svg_path = base_dir / "page1.svg"
    page2_path = base_dir / "page2.pdf"

    # Read the SVG template for page 1
    svg_content = svg_path.read_text()

    # Update the SVG with new text
    updated_svg = update_svg_text(
        svg_content, name, dob_formatted, issue_date_str, expiration_date_str
    )

    # Initialize temporary file paths
    tmp_svg_path = None
    tmp_pdf_path = None

    try:
        # Write to temporary file and convert to PDF
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".svg", delete=False
        ) as tmp_svg:
            tmp_svg.write(updated_svg)
            tmp_svg_path = tmp_svg.name

        # Create secure temporary file for PDF
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            tmp_pdf_path = tmp_pdf.name

        # Convert page1 SVG to PDF
        cairosvg.svg2pdf(url=tmp_svg_path, write_to=tmp_pdf_path)

        # Read both PDFs to get dimensions
        with open(tmp_pdf_path, "rb") as f:
            page1_reader = PdfReader(f)
            page1 = page1_reader.pages[0]
            page1_width = float(page1.mediabox.width)
            page1_height = float(page1.mediabox.height)

        with open(page2_path, "rb") as f:
            page2_reader = PdfReader(f)
            page2 = page2_reader.pages[0]
            page2_width = float(page2.mediabox.width)

        # Calculate scale factor to size page2 down to page1
        scale = page1_width / page2_width

        # Create merged PDF with both pages at page1 size
        merger = PdfWriter()

        # Add page1 as-is
        merger.append(tmp_pdf_path)

        # Scale page2 down to match page1
        with open(page2_path, "rb") as f:
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
        print(f"  DOB: {dob_formatted}")
        print(f"  Issued: {issue_date_str}")
        print(f"  Expires: {expiration_date_str}")

        return str(output_path)
    finally:
        # Clean up temporary files, handling error paths properly
        if tmp_svg_path is not None:
            Path(tmp_svg_path).unlink(missing_ok=True)
        if tmp_pdf_path is not None:
            Path(tmp_pdf_path).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(
        description="Generate player card PDF from SVG template"
    )
    parser.add_argument(
        "--batch", help="YAML file with player data for batch generation"
    )
    parser.add_argument("name", nargs="?", help="Player name")
    parser.add_argument(
        "dob",
        nargs="?",
        help="Date of birth (accepts YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, or MM/DD/YYYY)",
    )
    parser.add_argument(
        "issue_date",
        nargs="?",
        help="Issue date (accepts YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, or MM/DD/YYYY), defaults to today",
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
                issue_date = parse_date(issue_date_str)
            else:
                issue_date = datetime.now()

            generate_card(name, dob, issue_date, output_dir)
            print()

        print(f"✓ Batch complete: {len(players)} cards generated in {output_dir}/")
    else:
        # Single player mode
        if not args.name or not args.dob:
            parser.error("name and dob are required when not using --batch")

        # Parse issue date (default to today)
        if args.issue_date:
            issue_date = parse_date(args.issue_date)
        else:
            issue_date = datetime.now()

        generate_card(args.name, args.dob, issue_date, output_dir)


if __name__ == "__main__":
    main()
