import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "path/account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)
spreadsheet_id = "1tZQzyJdZ85lWFd6dPBo7z17lEZ_6e7Xmeihk7Nr34lU"
sheet = gc.open_by_key(spreadsheet_id).sheet1
