"""
Google Sheets reader.
Supports both service account auth and CSV fallback.
"""
import os
import pandas as pd


def read_sheet(sheet_id: str = None, csv_path: str = None) -> pd.DataFrame:
    """
    Read contacts from Google Sheets or a local CSV.
    Returns a normalised DataFrame.
    """
    if csv_path:
        df = pd.read_csv(csv_path)
        return _normalise(df)

    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "credentials.json")
    sheet_id = sheet_id or os.getenv("GOOGLE_SHEET_ID", "")

    if not sheet_id:
        raise ValueError("Provide GOOGLE_SHEET_ID in .env or pass --csv")

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        return _normalise(df)

    except Exception as e:
        raise RuntimeError(f"Could not read Google Sheet: {e}")


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names to lowercase snake_case."""
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    df = df.dropna(how="all")
    if "email" in df.columns:
        df["email"] = df["email"].str.strip().str.lower()
        df = df[df["email"].str.contains("@", na=False)]
    return df.reset_index(drop=True)
