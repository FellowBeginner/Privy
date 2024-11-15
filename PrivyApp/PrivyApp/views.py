"""
Routes and views for the flask application.
"""

import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from PrivyApp.Features.FilesBackupRun import FilesBackupRun_main
from PrivyApp.forms import RegistrationForm, LoginForm
from PrivyApp.models import  db,User, Expense, Password
from datetime import datetime
from sqlalchemy import func
import csv
import io
from PrivyApp import app,login_manager


db.init_app(app)
@app.before_request
def create_tables():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def search_expense():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')

    query = Expense.query.filter_by(user_id=current_user.id)
    # Query to aggregate sum(amount) grouped by description
    aggregate_query = db.session.query(
        Expense.description,
        func.sum(Expense.amount).label('total_amount')
    ).group_by(Expense.description).filter_by(user_id=current_user.id)
    # Calculate the total amount
    total_amount_query = db.session.query(func.sum(Expense.amount)).filter_by(user_id=current_user.id)

    if start_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        query = query.filter(Expense.date >= start_date)
        aggregate_query = aggregate_query.filter(Expense.date >= start_date)
        total_amount_query = total_amount_query.filter(Expense.date >= start_date)

    if end_date:
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(Expense.date <= end_date)
        aggregate_query = aggregate_query.filter(Expense.date <= end_date)
        total_amount_query = total_amount_query.filter(Expense.date <= end_date)

    if min_amount:
        min_amount = float(min_amount)
        query = query.filter(Expense.amount >= min_amount)
        aggregate_query = aggregate_query.filter(Expense.amount >= min_amount)
        total_amount_query = total_amount_query.filter(Expense.amount >= min_amount)

    if max_amount:
        max_amount = float(max_amount)
        query = query.filter(Expense.amount <= max_amount)
        aggregate_query = aggregate_query.filter(Expense.amount <= max_amount)
        total_amount_query = total_amount_query.filter(Expense.amount <= max_amount)

    return query,aggregate_query,total_amount_query

@app.route('/expenseManager')
@login_required
def expense_manager():
    query,aggregate_query,total_amount_query = search_expense()

    expenses = query.all()
    expenses_chart = aggregate_query.all()
    total_amount = total_amount_query.scalar()

    return render_template('expense_index.html', expenses=expenses, expenses_chart=expenses_chart, total_amount=total_amount)

@app.route('/expenseManager/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        description = request.form['description']
        amount = request.form['amount']
        date = request.form['date']
        reason = request.form['reason']
        expense = Expense(
            description=description,
            amount=float(amount),
            date=datetime.strptime(date, '%Y-%m-%d'),
            reason=reason,
            user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        return redirect(url_for('expense_manager'))
    return render_template('expense_form.html')

@app.route('/expenseManager/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_expense(id):
    expense = Expense.query.get(id)
    if expense.user_id != current_user.id:
        return redirect(url_for('index'))
    if request.method == 'POST':
        expense.description = request.form['description']
        expense.amount = float(request.form['amount'])
        expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        expense.reason = request.form['reason']
        db.session.commit()
        return redirect(url_for('expense_manager'))
    return render_template('expense_form.html', expense=expense)

@app.route('/expenseManager/delete/<int:id>')
@login_required
def delete_expense(id):
    expense = Expense.query.get(id)
    if expense.user_id != current_user.id:
        return redirect(url_for('index'))
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('expense_manager'))

# Route for uploading Excel file and importing data
@app.route('/expenseManager/upload', methods=['GET', 'POST'])
def upload_expense():
    if request.method == 'POST':
        # Get the uploaded file
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            # Read the Excel file into a DataFrame
            df = pd.read_excel(file)

            # Iterate through the DataFrame and add to the database
            for index, row in df.iterrows():
                expense = Expense(
                    description=row['Description'],
                    amount=row['Amount'],
                    date= row['Date'],#datetime.strptime(row['Date'], '%Y-%m-%d'),
                    reason=row['Reason'],
                    user_id=current_user.id
                )
                db.session.add(expense)
            db.session.commit()

            return redirect(url_for('expense_manager'))
    return render_template('upload_expense.html')

@app.route('/expenseManager/export_csv')
def export_csv_expense():
    # Query all expenses from the database
    query = search_expense()
    expenses = query.all()

    # Create an in-memory buffer
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(['Description', 'Amount', 'Date','Reason'])

    # Write the data
    for expense in expenses:
        writer.writerow([expense.description, expense.amount, expense.date, expense.reason])

    # Set the buffer to the beginning
    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8')
    output = io.BytesIO(csv_bytes)  # Rewrap in BytesIO for binary download

    # Send the file to the user
    return send_file(output, mimetype='text/csv', download_name='expenses.csv', as_attachment=True)

@app.route('/passwordManager', methods=['GET', 'POST'])
@app.route('/passwordManager/<int:id>', methods=['GET', 'POST'])
@login_required
def password_manager(id=-1):
    passwords = Password.query.filter_by(user_id=current_user.id).all()
    decrypted_password = ""
    if(id != -1):
        passw=Password.query.get_or_404(id)
        decrypted_password = passw.get_password()  # Assuming this method decrypts the password
    return render_template('password_index.html', passwords=passwords, password_id=id, decrypted_password=decrypted_password)

@app.route('/passwordManager/add_password', methods=['GET', 'POST'])
@login_required
def add_password():
    if request.method == 'POST':
        service_name = request.form['service_name']
        username = request.form['username']
        password = request.form['password']

        new_password = Password(service_name=service_name, username=username, user_id=current_user.id)
        new_password.set_password(password)

        db.session.add(new_password)
        db.session.commit()
        return redirect(url_for('password_manager'))
    return render_template('add_password.html')

@app.route('/passwordManager/edit_password/<int:id>', methods=['GET', 'POST'])
def edit_password(id):
    password_entry = Password.query.get(id)
    if request.method == 'POST':
        password_entry.service_name = request.form['service_name']
        password_entry.username = request.form['username']
        new_password = request.form['password']
        if new_password:
            password_entry.set_password(new_password)

        db.session.commit()
        return redirect(url_for('password_manager'))
    return render_template('edit_password.html', password_entry=password_entry)

@app.route('/passwordManager/delete_password/<int:id>', methods=['POST'])
def delete_password(id):
    password_entry = Password.query.get(id)
    db.session.delete(password_entry)
    db.session.commit()
    return redirect(url_for('password_manager'))

@app.route('/passwordManager/export_csv')
def export_csv_password():
    # Query all expenses from the database
    passwords = Password.query.filter_by(user_id=current_user.id).all()

    # Create an in-memory buffer
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(['Site Name', 'UserName', 'Password'])

    # Write the data
    for passwordObj in passwords:
        writer.writerow([passwordObj.service_name, passwordObj.username, passwordObj.get_password()])

    # Set the buffer to the beginning
    output.seek(0)
    csv_bytes = output.getvalue().encode('utf-8')
    output = io.BytesIO(csv_bytes)  # Rewrap in BytesIO for binary download

    # Send the file to the user
    return send_file(output, mimetype='text/csv', download_name='passwords.csv', as_attachment=True)


#REGION: DEFAULT
@app.route('/home_default')
def home():
    """Renders the home page."""
    return render_template(
        'index-default.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact_default')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact-default.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about_default')
def about():
    """Renders the about page."""
    return render_template(
        'about-default.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/files_backup_manager', methods=['GET', 'POST'])
def files_backup_manager():
    if request.method == 'POST':
        FilesBackupRun_main(request.form['source_folder'],request.form['destination_folder']);
    return render_template('files_backup_index.html')