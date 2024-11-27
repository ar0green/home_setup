from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from application.forms import IncomeForm, ExpenseForm
from datetime import datetime
from collections import defaultdict
from .models import Income, Expense, Category
from . import app, db

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            income = float(request.form['income'])
            expenses = float(request.form['expenses'])
            strategy = request.form['strategy']

            loan_names = request.form.getlist('loan_name[]')
            loan_balances = request.form.getlist('loan_balance[]')
            loan_payments = request.form.getlist('loan_payment[]')
            loan_interests = request.form.getlist('loan_interest[]')

            loans = []
            for name, balance, payment, interest in zip(loan_names, loan_balances, loan_payments, loan_interests):
                loans.append({
                    'name': name,
                    'balance': float(balance),
                    'payment': float(payment) if payment else None,
                    'interest_rate': float(interest)
                })

            plan = calculate_optimal_plan(income, expenses, loans, strategy)
            if 'error' in plan:
                strategy_name = 'Метод снежного кома' if strategy == 'snowball' else 'Метод лавины'
                return render_template('plan.html', error=plan['error'], strategy_name=strategy_name)
            else:
                strategy_name = 'Метод снежного кома' if strategy == 'snowball' else 'Метод лавины'
                return render_template('plan.html', plan=plan, strategy_name=strategy_name)
        except ValueError:
            error = 'Пожалуйста, введите корректные числовые значения.'
            return render_template('plan.html', error=error)
    return render_template('index.html')

def calculate_optimal_plan(income, expenses, loans, strategy):
    for loan in loans:
        if loan['payment'] is None or loan['payment'] <= 0:
            loan['payment'] = max(loan['balance'] * 0.05, 1000)
        loan['monthly_rate'] = loan['interest_rate'] / 12 / 100

    total_monthly_payments = sum([loan['payment'] for loan in loans])
    available_budget = income - expenses

    if total_monthly_payments > available_budget:
        return {'error': 'Ваш доход не позволяет покрыть расходы на проживание и обязательные платежи по кредитам.'}

    plan = []
    month = 1

    while any(loan['balance'] > 0 for loan in loans):
        month_info = {'month': month, 'payments': []}

        for loan in loans:
            if loan['balance'] > 0:
                interest = loan['balance'] * loan['monthly_rate']
                loan['balance'] += interest

        active_loans = [loan for loan in loans if loan['balance'] > 0]

        if strategy == 'snowball':
            active_loans.sort(key=lambda x: x['balance'])
        elif strategy == 'avalanche':
            active_loans.sort(key=lambda x: x['interest_rate'], reverse=True)

        total_monthly_payments = sum([loan['payment'] for loan in active_loans])

        available_budget = income - expenses
        if total_monthly_payments > available_budget:
            return {'error': f'В месяце {month} ваш доход не позволяет покрыть обязательные платежи по кредитам.'}

        free_cash = available_budget - total_monthly_payments

        for loan in active_loans:
            loan['actual_payment'] = loan['payment']
            loan['extra_payment'] = 0

        current_loan_index = 0
        while free_cash > 0 and current_loan_index < len(active_loans):
            loan = active_loans[current_loan_index]
            remaining_balance = loan['balance'] - loan['actual_payment']
            if remaining_balance <= 0:
                current_loan_index += 1
                continue

            possible_extra_payment = min(free_cash, remaining_balance)
            loan['actual_payment'] += possible_extra_payment
            loan['extra_payment'] += possible_extra_payment
            free_cash -= possible_extra_payment

            if loan['balance'] - loan['actual_payment'] <= 0:
                current_loan_index += 1

        for loan in loans:
            if loan['balance'] <= 0:
                continue

            payment = loan['actual_payment']
            actual_payment = min(payment, loan['balance'])
            loan['balance'] -= actual_payment

            month_info['payments'].append({
                'loan_name': loan['name'],
                'mandatory_payment': round(loan['payment'], 2),
                'extra_payment': round(loan['extra_payment'], 2),
                'total_payment': round(actual_payment, 2),
                'interest_accrued': round(loan['balance'] * loan['monthly_rate'], 2),
                'remaining_balance': round(loan['balance'], 2),
                'interest_rate': loan['interest_rate']
            })

            loan['actual_payment'] = None
            loan['extra_payment'] = 0

        plan.append(month_info)
        month += 1

    return plan

@app.route('/planner', methods=['GET', 'POST'])
def planner():
    income_form = IncomeForm(db.session)
    expense_form = ExpenseForm(db.session)

    incomes = Income.query.all()
    expenses = Expense.query.all()

    income_categories = [
        {"name": category.name, "amount": sum(income.amount for income in category.incomes)}
        for category in Category.query.filter_by(type='income')
    ]

    expense_categories = [
        {"name": category.name, "amount": sum(expense.amount for expense in category.expenses)}
        for category in Category.query.filter_by(type='expense')
    ]

    return render_template(
        'planner.html',
        income_form=income_form,
        expense_form=expense_form,
        income_data=[income.amount for income in incomes],
        expense_data=[expense.amount for expense in expenses],
        income_categories=income_categories,
        expense_categories=expense_categories
    )


    
@app.route('/categories', methods=['GET', 'POST'])
def categories():
    if request.method == 'POST':
        category_name = request.form.get('category_name')
        category_type = request.form.get('category_type')
        if category_name and category_type:
            new_category = Category(name=category_name, type=category_type)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('categories'))
    
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('categories'))

@app.route('/test', methods=['GET'])
def test_connection():
    return('Соединение установлено', 200)

@app.route('/planner/incomes', methods=['GET'])
def planner_incomes():
    incomes = Income.query.all()
    return render_template('incomes.html', incomes=incomes)

@app.route('/planner/expenses', methods=['GET'])
def planner_expenses():
    expenses = Expense.query.all()
    return render_template('expenses.html', expenses=expenses)


if __name__ == '__main__':
    app.run(debug=True)
