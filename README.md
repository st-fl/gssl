# Player Card Generator

Automates the creation of player card PDFs from an SVG template.

## Setup

```bash
uv sync
```

## Usage

Generate a player card with name and date of birth (issue date defaults to today):

```bash
uv run python main.py "John Doe" "1990-01-15"
```

Generate with a custom issue date:

```bash
uv run python main.py "Jane Smith" "1985-06-20" "2026-02-01"
```

This will:
1. Update the text fields in `page1.svg` (NameField, DOBField, IssuedDate, ExpirationDate)
2. Calculate the expiration date as 1 week from the issue date
3. Convert `page1.svg` to PDF
4. Merge with `page2.pdf` to create `playercard.pdf` (2 pages total)

## Arguments

- `name` (required): Player name
- `dob` (required): Date of birth in YYYY-MM-DD format
- `issue_date` (optional): Issue date in YYYY-MM-DD format, defaults to today

## Files

- `page1.svg`: Template for the first page with text fields to be updated
- `page2.pdf`: Static second page (pre-existing)
- `playercard.pdf`: Generated output (2-page PDF)

## Known Issues

### Font Compatibility

The script currently relies on system fonts when generating PDFs. If Calibri is not available on the system (e.g., on Linux), the generated PDF will use a fallback font, causing visual inconsistencies.

See `plans/2026-01-12-font-compatibility.md` for detailed analysis and solutions.
