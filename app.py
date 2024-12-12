import streamlit as st
import pandas as pd
import plotly.express as px
from models import SessionLocal, Loan, Income, Expense, Category
from db_init import init_db
from datetime import date
from calculate_plan import calculate_optimal_plan

# Инициализация БД
init_db()
session = SessionLocal()

# Хранение временных данных в session_state
if "loans_cache" not in st.session_state:
    st.session_state.loans_cache = []

if "page" not in st.session_state:
    st.session_state.page = "Калькулятор кредитов"

# Боковое меню
page = st.sidebar.selectbox("Навигация", ["Калькулятор кредитов", "Финансовый планировщик", "Категории", "План погашения"])

st.title("ФинКалькулятор (Streamlit версия)")

if page == "Калькулятор кредитов":
    income = st.number_input("Ежемесячный доход", value=100000.0, step=1000.0)
    expenses = st.number_input("Расходы на проживание", value=50000.0, step=1000.0)
    strategy = st.selectbox("Стратегия погашения", ["snowball", "avalanche"])

    st.subheader("Добавить кредит")
    loan_name = st.text_input("Название кредита", "")
    loan_balance = st.number_input("Остаток долга", value=250000.0, step=10000.0)
    loan_payment = st.number_input("Ежемесячный платеж", value=15000.0, step=1000.0)
    loan_interest = st.number_input("Ставка % годовых", value=12.0, step=1.0)

    if st.button("Добавить кредит"):
        if loan_name.strip():
            st.session_state.loans_cache.append({
                "name": loan_name,
                "balance": loan_balance,
                "payment": loan_payment,
                "interest_rate": loan_interest
            })
            st.success("Кредит добавлен")
        else:
            st.error("Введите название кредита")

    if st.session_state.loans_cache:
        st.subheader("Ваши кредиты")
        for i, loan in enumerate(st.session_state.loans_cache):
            st.write(f"{loan['name']} | Остаток: {loan['balance']} | Платеж: {loan['payment']} | Ставка: {loan['interest_rate']}%")
            if st.button(f"Удалить {loan['name']}", key=f"del_{i}"):
                st.session_state.loans_cache.pop(i)
                st.experimental_rerun()
    else:
        st.write("Нет кредитов")

    if st.button("Рассчитать план"):
        # Запускаем расчет
        plan = calculate_optimal_plan(income, expenses, st.session_state.loans_cache, strategy=strategy)
        if 'error' in plan:
            st.error(plan['error'])
        else:
            st.session_state.plan_result = plan['plan']
            st.session_state.income_for_plan = income
            st.session_state.expenses_for_plan = expenses
            st.session_state.strategy_for_plan = strategy
            st.success("План рассчитан! Перейдите на страницу 'План погашения'")

elif page == "Финансовый планировщик":
    st.subheader("Добавить доход")
    cat_inc = [c.name for c in session.query(Category).filter_by(type='income').all()]
    inc_amount = st.number_input("Сумма дохода", value=50000.0, step=1000.0)
    inc_cat = st.selectbox("Категория дохода", cat_inc)
    if st.button("Добавить доход"):
        cat_id = session.query(Category).filter_by(name=inc_cat, type='income').first().id
        new_inc = Income(amount=inc_amount, date=date.today(), category_id=cat_id)
        session.add(new_inc)
        session.commit()
        st.success("Доход добавлен")

    st.subheader("Добавить расход")
    cat_exp = [c.name for c in session.query(Category).filter_by(type='expense').all()]
    exp_amount = st.number_input("Сумма расхода", value=15000.0, step=1000.0)
    exp_cat = st.selectbox("Категория расхода", cat_exp)
    if st.button("Добавить расход"):
        cat_id = session.query(Category).filter_by(name=exp_cat, type='expense').first().id
        new_exp = Expense(amount=exp_amount, date=date.today(), category_id=cat_id)
        session.add(new_exp)
        session.commit()
        st.success("Расход добавлен")

    # Отображение диаграммы по доходам и расходам
    all_incomes = session.query(Income).all()
    all_expenses = session.query(Expense).all()
    income_vals = [x.amount for x in all_incomes]
    expense_vals = [x.amount for x in all_expenses]

    df_main = pd.DataFrame({
        "Тип": ["Доходы", "Расходы"],
        "Сумма": [sum(income_vals), sum(expense_vals)]
    })
    fig = px.pie(df_main, names="Тип", values="Сумма", hole=0.4, title="Соотношение доходов и расходов")
    st.plotly_chart(fig)

    detail_choice = st.radio("Показать детали по:", ["Ничего", "Доходы", "Расходы"])
    if detail_choice == "Доходы":
        df_i = pd.DataFrame([(inc.amount, inc.category.name) for inc in all_incomes], columns=["Сумма", "Категория"])
        grp = df_i.groupby("Категория")["Сумма"].sum().reset_index()
        fig_detail = px.pie(grp, names="Категория", values="Сумма", hole=0.4, title="Распределение доходов по категориям")
        st.plotly_chart(fig_detail)
    elif detail_choice == "Расходы":
        df_e = pd.DataFrame([(exp.amount, exp.category.name) for exp in all_expenses], columns=["Сумма", "Категория"])
        grp_e = df_e.groupby("Категория")["Сумма"].sum().reset_index()
        fig_detail = px.pie(grp_e, names="Категория", values="Сумма", hole=0.4, title="Распределение расходов по категориям")
        st.plotly_chart(fig_detail)

elif page == "Категории":
    st.subheader("Управление категориями")
    cat_type = st.selectbox("Тип категории", ["income", "expense"])
    cat_name = st.text_input("Название категории", "")
    if st.button("Добавить категорию"):
        if cat_name.strip():
            exists = session.query(Category).filter_by(name=cat_name, type=cat_type).first()
            if not exists:
                new_cat = Category(name=cat_name, type=cat_type)
                session.add(new_cat)
                session.commit()
                st.success("Категория добавлена")
            else:
                st.warning("Категория уже существует")
        else:
            st.error("Введите название категории")

    st.write("Доходы:", [c.name for c in session.query(Category).filter_by(type='income')])
    st.write("Расходы:", [c.name for c in session.query(Category).filter_by(type='expense')])

    del_type = st.selectbox("Тип для удаления", ["income", "expense"], key="del_type")
    cats_del = [c.name for c in session.query(Category).filter_by(type=del_type)]
    if cats_del:
        del_cat = st.selectbox("Выберите категорию для удаления", cats_del)
        if st.button("Удалить категорию"):
            cat_obj = session.query(Category).filter_by(name=del_cat, type=del_type).first()
            if cat_obj:
                session.delete(cat_obj)
                session.commit()
                st.success("Категория удалена")
                st.experimental_rerun()
    else:
        st.write("Нет категорий для удаления")

elif page == "План погашения":
    if "plan_result" in st.session_state:
        plan = st.session_state.plan_result
        strategy = st.session_state.strategy_for_plan
        st.write(f"Стратегия погашения: {strategy}")
        for month_data in plan:
            st.subheader(f"Месяц {month_data['month']}")
            df = pd.DataFrame(month_data['payments'])
            st.table(df)
    else:
        st.info("План еще не рассчитан. Перейдите на 'Калькулятор кредитов' и рассчитайте план.")
