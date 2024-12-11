import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

Base = declarative_base()
engine = create_engine("sqlite:///finance.db")
Session = sessionmaker(bind=engine)
session = Session()


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)


class Income(Base):
    __tablename__ = 'incomes'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))


class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))


class Loan(Base):
    __tablename__ = 'loans'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    balance = Column(Float, nullable=False)
    payment = Column(Float, nullable=False)
    interest = Column(Float, nullable=False)


Base.metadata.create_all(engine)


def calculate_payment_plan(income, expenses, loans, strategy):
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

        total_monthly_payments = sum([loan['payment']
                                     for loan in active_loans])

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


def manage_categories():
    st.title("Управление категориями")
    categories = session.query(Category).all()

    with st.form("Добавить категорию"):
        name = st.text_input("Название категории")
        category_type = st.selectbox("Тип категории", ["Доход", "Расход"])
        submitted = st.form_submit_button("Добавить")
        if submitted and name:
            session.add(Category(name=name, type=category_type.lower()))
            session.commit()
            st.success(f"Категория '{name}' добавлена.")

    st.write("Существующие категории:")
    for category in categories:
        col1, col2 = st.columns([3, 1])
        col1.write(
            f"{category.name} ({'Доход' if category.type == 'income' else 'Расход'})")
        if col2.button("Удалить", key=category.id):
            session.delete(category)
            session.commit()
            st.experimental_rerun()


def calculator_page():
    st.title("Калькулятор кредитов")

    income = st.number_input("Ежемесячный доход:", min_value=0.0, step=1000.0)
    expenses = st.number_input(
        "Расходы на проживание:", min_value=0.0, step=1000.0)
    strategy = st.selectbox(
        "Стратегия выплат",
        ["snowball", "avalanche"]
    )

    with st.form("Добавить кредит"):
        name = st.text_input("Название кредита")
        balance = st.number_input("Остаток долга", min_value=0.0)
        monthly_payment = st.number_input("Ежемесячный платеж", min_value=0.0)
        interest_rate = st.number_input("Процентная ставка", min_value=0.0)
        submitted = st.form_submit_button("Добавить кредит")
        if submitted and name:
            session.add(Loan(name=name, balance=balance,
                        monthly_payment=monthly_payment, interest_rate=interest_rate))
            session.commit()
            st.success(f"Кредит '{name}' добавлен.")

    loans = session.query(Loan).all()
    if loans:
        st.write("Список кредитов:")
        for loan in loans:
            st.write(f"{loan.name}: Остаток {loan.balance}, Платеж {
                     loan.monthly_payment}, Ставка {loan.interest_rate}%")

    if st.button("Рассчитать план выплат"):
        plan = calculate_payment_plan(income, expenses, loans, strategy)
        if plan:
            st.write("План выплат:")
            for p in plan:
                st.write(f"{p['Кредит']}: Платеж {p['Платеж']}, Остаток {
                         p['Остаток']}, Ставка {p['Процент']}%")
        else:
            st.write("Недостаточно средств для выплат.")


def planner_page():
    st.title("Финансовый планировщик")

    st.subheader("Доходы")
    with st.form("add_income"):
        amount = st.number_input("Сумма дохода", min_value=0.0, step=1000.0)
        date = st.date_input("Дата дохода", value=datetime.today())
        category = st.selectbox(
            "Категория дохода",
            [(c.id, c.name)
             for c in session.query(Category).filter_by(type="income").all()],
            format_func=lambda x: x[1]
        )
        submitted = st.form_submit_button("Добавить доход")
        if submitted and amount > 0:
            session.add(Income(amount=amount, date=date,
                        category_id=category[0]))
            session.commit()
            st.success("Доход добавлен!")

    st.write("Существующие доходы:")
    incomes = session.query(Income).all()
    for income in incomes:
        col1, col2 = st.columns([3, 1])
        col1.write(f"{income.amount} - {income.date} - {income.category.name}")
        if col2.button("Удалить", key=f"del_income_{income.id}"):
            session.delete(income)
            session.commit()
            st.experimental_rerun()

    st.subheader("Расходы")
    with st.form("add_expense"):
        amount = st.number_input(
            "Сумма расхода", min_value=0.0, step=1000.0, key="expense_amount")
        date = st.date_input(
            "Дата расхода", value=datetime.today(), key="expense_date")
        category = st.selectbox(
            "Категория расхода",
            [(c.id, c.name)
             for c in session.query(Category).filter_by(type="expense").all()],
            format_func=lambda x: x[1],
            key="expense_category"
        )
        submitted = st.form_submit_button("Добавить расход")
        if submitted and amount > 0:
            session.add(Expense(amount=amount, date=date,
                        category_id=category[0]))
            session.commit()
            st.success("Расход добавлен!")

    st.write("Существующие расходы:")
    expenses = session.query(Expense).all()
    for expense in expenses:
        col1, col2 = st.columns([3, 1])
        col1.write(
            f"{expense.amount} - {expense.date} - {expense.category.name}")
        if col2.button("Удалить", key=f"del_expense_{expense.id}"):
            session.delete(expense)
            session.commit()
            st.experimental_rerun()

    incomes_sum = sum([income.amount for income in incomes])
    expenses_sum = sum([expense.amount for expense in expenses])

    st.subheader("График соотношения доходов и расходов")
    fig = px.pie(
        names=["Доходы", "Расходы"],
        values=[incomes_sum, expenses_sum],
        title="Соотношение доходов и расходов"
    )
    st.plotly_chart(fig)


def main():
    st.sidebar.title("Меню")
    page = st.sidebar.radio("Перейти на страницу:", [
                            "Калькулятор кредитов", "Финансовый планировщик", "Управление категориями"])

    if page == "Калькулятор кредитов":
        calculator_page()
    elif page == "Финансовый планировщик":
        planner_page()
    elif page == "Управление категориями":
        manage_categories()


if __name__ == "__main__":
    main()
