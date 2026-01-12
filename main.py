#!/usr/bin/env python3
"""
Generate a player card PDF from an SVG template.

Usage:
    uv run python main.py "John Doe" "1990-01-15"
    uv run python main.py "John Doe" "1990-01-15" "2026-01-12"
"""

import argparse
import re
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import cairosvg
from pypdf import PdfWriter


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


def main():
    parser = argparse.ArgumentParser(
        description="Generate player card PDF from SVG template"
    )
    parser.add_argument("name", help="Player name")
    parser.add_argument("dob", help="Date of birth (YYYY-MM-DD)")
    parser.add_argument(
        "issue_date", nargs="?", help="Issue date (YYYY-MM-DD), defaults to today"
    )
    args = parser.parse_args()

    # Parse issue date (default to today)
    if args.issue_date:
        issue_date = datetime.strptime(args.issue_date, "%Y-%m-%d")
    else:
        issue_date = datetime.now()

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
        svg_content, args.name, args.dob, issue_date_str, expiration_date_str
    )

    # Write to temporary file and convert to PDF
    with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as tmp_svg:
        tmp_svg.write(updated_svg)
        tmp_svg_path = tmp_svg.name

    tmp_pdf = tempfile.mktemp(suffix=".pdf")
    try:
        # Convert page1 SVG to PDF
        cairosvg.svg2pdf(url=tmp_svg_path, write_to=tmp_pdf)

        # Merge page1 PDF with page2 PDF
        merger = PdfWriter()
        merger.append(tmp_pdf)
        merger.append("page2.pdf")

        output_pdf = "playercard.pdf"
        merger.write(output_pdf)
        merger.close()

        print(f"✓ Generated {output_pdf}")
        print(f"  Name: {args.name}")
        print(f"  DOB: {args.dob}")
        print(f"  Issued: {issue_date_str}")
        print(f"  Expires: {expiration_date_str}")
    finally:
        # Clean up temporary files
        Path(tmp_svg_path).unlink()
        Path(tmp_pdf).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
