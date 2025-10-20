import time
from emailer.email_sheet import sheet
import yagmail
from emailer.MT5_encryption import assign_account, decrypt_account

EMAIL_ADDRESS = "saaddighi20@gmail.com"
EMAIL_PASSWORD = "xazc vkyw oqjo qdei"  
yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)

previous_row_count = len(sheet.get_all_values())
members_nb = sum(1 for row in sheet.get_all_values() if row[3] == "cohort_2")
cohort_status = "open" if members_nb < 10 else "close"

def welcome_email():
    global previous_row_count

    while True:
        try:
            current_data = sheet.get_all_values()
            current_row_count = len(current_data)

            if current_row_count > previous_row_count:
                for row_index in range(previous_row_count, current_row_count):
                    new_row = current_data[row_index]
                    if new_row and new_row[5] == 'yes':
                        recipient_email = new_row[2]
                        trader_name = new_row[1] if len(new_row) > 1 else "Trader"

                        discord_invite = "https://discord.gg/VwJTH65k"

                        if cohort_status == "open":
                            subject = f"👋 Welcome to Lotus Capital Trader Cohort, {trader_name}!"
                            body = f"""
                            Hi {trader_name},

                            Congratulations! You've been accepted into our next trader cohort.
                            Please join our Discord server using the link below to begin onboarding:
                            {discord_invite}
                            """
                        else:
                            subject = "Your Trader Application - Next Steps"
                            body = """Thanks for applying! Our current cohort is full.
                            You'll be notified as soon as the next cohort opens.
                            Stay tuned for updates."""
                        if new_row[16] == "sent":
                            pass
                        else:
                            yag.send(to=recipient_email, subject=subject, contents=body)
                            print(f"Email sent to {recipient_email} for row {row_index + 1}")
                            sheet.update_cell(int(new_row[0]) + 1, 17, "sent")
                            sheet.update_cell(int(new_row[0]) + 1, 4, "cohort_2")

                previous_row_count = current_row_count
                
            time.sleep(30)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(30)


def first_assessment_email(traderid):
    id = traderid
    assign_account(id)
    credentials = decrypt_account(id)
    data = sheet.get_all_values()
    for row in data:
        if row[0] == id:
            recipient_email = row[2]
            name = row[1]
            subject = "Your TM5 Trading Account Credentials"
            body = f"""
                        Hi {name},

                        Welcome aboard! 

                        Your TM5 trading account has been successfully created. Here are your credentials to get started:

                        - Username: {credentials['username']}
                        - Password: {credentials['password']}

                        Please make sure to:Log in at {credentials["link"]}.
                    """
            yag.send(to=recipient_email, subject=subject, contents=body)
