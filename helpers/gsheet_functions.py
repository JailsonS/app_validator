from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
from zoneinfo import ZoneInfo

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SHEET_ID = "1v573sjUIGvvfEBg6vRnTpvXw7ymeAgaIzTIUAryTldo"

def get_credentials():

    creds = service_account.Credentials.from_service_account_file(
        "gee.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    return creds


def write_validation(facility_id: str, choice: str, user: str, round: int|str, asset_samples:str):
    """
    Writes a new validation row into Google Sheets.
    """
    try:
        
        creds = get_credentials()
        service = build("sheets", "v4", credentials=creds)

        sheet = service.spreadsheets()

        row = [
            datetime.now(ZoneInfo("Europe/Stockholm")).strftime("%Y-%m-%d %H:%M:%S"),
            user,
            asset_samples,
            facility_id,
            choice,
            round
        ]

        body = {"values": [row]}

        sheet.values().append(
            spreadsheetId=SHEET_ID,
            range=f"Sheet1!A:D",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()

    except HttpError as err:
        print(f"ERROR writing to sheet: {err}")
        raise err