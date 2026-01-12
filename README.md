# Player Card Generator

Automates the creation of player card PDFs from an SVG template.

## Setup

```bash
uv sync
```

## Usage

### Web Interface (Streamlit)

Run the web application locally:

```bash
uv run streamlit run app.py
```

This will start the Streamlit server at http://localhost:8501 with a user-friendly interface for generating player cards.

### Command Line Interface

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

## Deployment

### Streamlit Cloud

To deploy this application on Streamlit Cloud:

1. **Prerequisites:**
   - Ensure your repository is on GitHub
   - The repository must be public or you must connect Streamlit Cloud to your GitHub account

2. **Deploy:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository, branch (usually `main` or `master`), and set the main file path to `app.py`
   - Click "Deploy"

3. **Requirements:**
   - `requirements.txt` is included for Streamlit Cloud to install dependencies
   - `fonts/` directory and `page1.svg` + `page2.pdf` must be committed to the repository

The app will be available at a public URL after deployment completes (typically 2-3 minutes).

## Known Issues

### Font Compatibility

The script currently relies on system fonts when generating PDFs. If Calibri is not available on the system (e.g., on Linux), the generated PDF will use a fallback font, causing visual inconsistencies.

See `plans/2026-01-12-font-compatibility.md` for detailed analysis and solutions.
