from flask import Flask, render_template, request, redirect, flash
from threading import Thread
from emailer.email_sheet import sheet
from emailer.mailer import welcome_email

app = Flask(__name__)
app.secret_key = "super_secret_key"

@app.route('/')
def home():
    return redirect('/signup')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        discord_id = request.form['discord_id'].strip()
        has_traded = request.form['has_traded'].strip()

        data = sheet.get_all_values()
        headers = data[0] if data else []
        rows = data[1:] if len(data) > 1 else []

        existing_emails = [row[2].lower() for row in rows if len(row) > 2]
        if email in existing_emails:
            flash("❌ This email is already registered.")
            return redirect('/signup')

        next_id = len(rows) + 1
        sheet.append_row([next_id, full_name, email])
        cell = sheet.find(email)
        row_index = cell.row
        sheet.update_cell(row_index, 16, discord_id)
        sheet.update_cell(row_index, 6, has_traded)
        flash("✅ Successfully signed up!")
        return redirect('/signup')

    return render_template('signup.html')

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    Thread(target=welcome_email, daemon=True).start()
    run_flask()
