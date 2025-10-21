import gspread
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = "/home/saad/Documents/LCP_automation/emailer/account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/spreadsheets"]

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(credentials)
spreadsheet_id = "1CbyVgxTZ5Mz9gfbOzXbsZi37WZ7LuO8c2toQc0NkWdw"
sheet = gc.open_by_key(spreadsheet_id).sheet1
