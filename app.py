#!/usr/bin/env python3
"""Streamlit web UI for player card PDF generation."""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st

from main import generate_card, slugify_name

# Configure page
st.set_page_config(page_title="Player Card Generator", page_icon="🎮")

# Configure fontconfig to use bundled fonts
fonts_dir = Path(__file__).parent / "fonts"
os.environ["FONTCONFIG_FILE"] = str(fonts_dir / "fonts.conf")
os.environ["FONTCONFIG_PATH"] = str(fonts_dir)

# Verify required template files exist early to fail fast with a clear message
base_dir = Path(__file__).parent
page1_path = base_dir / "page1.svg"
page2_path = base_dir / "page2.pdf"

if not page1_path.is_file() or not page2_path.is_file():
    missing = []
    if not page1_path.is_file():
        missing.append("page1.svg")
    if not page2_path.is_file():
        missing.append("page2.pdf")
    st.error(
        f"Missing required template file(s): {', '.join(missing)}. "
        "Please contact the administrator."
    )
    st.stop()

st.title("🎮 Player Card Generator")
st.write("Generate a professional player card PDF with automatic expiration date.")

# Input fields
name = st.text_input("Name *", placeholder="Enter player name")

dob_input = st.text_input(
    "Date of Birth *", placeholder="MM/DD/YYYY", help="Format: MM/DD/YYYY"
)

# Default to today's date
today = datetime.now()
default_issue_date = today.strftime("%m/%d/%Y")

issue_date_input = st.text_input(
    "Issue Date",
    value=default_issue_date,
    placeholder="MM/DD/YYYY",
    help="Format: MM/DD/YYYY (defaults to today)",
)

# Validation
name_valid = len(name.strip()) > 0
dob_valid = False
issue_date_valid = False
dob_date = None
issue_date_obj = None

# Validate DOB
if dob_input.strip():
    try:
        dob_date = datetime.strptime(dob_input, "%m/%d/%Y")
        dob_valid = True
    except ValueError:
        st.error("Invalid date of birth. Please use MM/DD/YYYY format.")

# Validate issue date
if issue_date_input.strip():
    try:
        issue_date_obj = datetime.strptime(issue_date_input, "%m/%d/%Y")
        issue_date_valid = True
    except ValueError:
        st.error("Invalid issue date. Please use MM/DD/YYYY format.")

# Show expiration date preview
if issue_date_valid and issue_date_obj:
    expiration_date = issue_date_obj + timedelta(weeks=1)
    st.info(
        f"📅 Expiration Date: {expiration_date.month}/{expiration_date.day}/{expiration_date.year}"
    )

# Enable download button only when all inputs are valid
all_valid = name_valid and dob_valid and issue_date_valid


# Generate PDF on button click
def generate_pdf() -> tuple[bytes, str]:
    """Generate PDF and return bytes and filename."""
    # Validate that issue_date_obj is set (should always be true when called)
    if issue_date_obj is None:
        raise ValueError("Issue date must be set before generating card")

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)

        # Generate the card
        output_path = generate_card(
            name=name.strip(),
            dob=dob_input,
            issue_date=issue_date_obj,
            output_dir=output_dir,
        )

        # Read the generated PDF
        pdf_bytes = Path(output_path).read_bytes()
        filename = f"{slugify_name(name.strip())}.pdf"

        return pdf_bytes, filename


# Download button
if all_valid:
    if st.button(
        "Generate & Download Player Card", type="primary", use_container_width=True
    ):
        with st.spinner("Generating PDF..."):
            try:
                pdf_bytes, filename = generate_pdf()
                st.download_button(
                    label="📥 Download Player Card",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
                st.success(f"✓ Generated {filename} successfully!")
            except Exception as e:
                st.error(f"Error generating PDF: {e}")
else:
    st.button(
        "Generate & Download Player Card",
        type="primary",
        disabled=True,
        use_container_width=True,
        help="Please fill in all required fields with valid data",
    )

# Footer
st.divider()
st.caption("Player cards expire 7 days after issue date")
