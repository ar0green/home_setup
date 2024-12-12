def calculate_optimal_plan(income, expenses, loans, strategy='snowball'):
    # Пример логики, упрощенной для демо
    # Предположим, что income, expenses - float
    # loans - список словарей: {name, balance, payment, interest_rate}

    # Проверим обязательные платежи
    total_payments = sum(l['payment'] for l in loans)
    available_budget = income - expenses

    if total_payments > available_budget:
        return {'error': 'Недостаточно дохода для покрытия обязательных платежей'}

    plan = []
    month = 1

    # Сортируем кредиты по стратегии
    def sort_key(loan):
        if strategy == 'snowball':
            return loan['balance']
        elif strategy == 'avalanche':
            return loan['interest_rate']
    
    loans = sorted(loans, key=sort_key, reverse=(strategy=='avalanche'))

    while any(l['balance'] > 0 for l in loans):
        month_info = {'month': month, 'payments': []}

        total_payments = sum(l['payment'] for l in loans if l['balance'] > 0)
        free_cash = available_budget - total_payments
        # Дополнительный платеж к первому непогашенному кредиту
        for loan in loans:
            if loan['balance'] <= 0:
                continue
            payment = loan['payment']
            if loan == next((x for x in loans if x['balance'] > 0), None):
                extra = min(free_cash, loan['balance'] - loan['payment'])
                payment += extra
            # Погашаем
            loan['balance'] -= payment
            month_info['payments'].append({
                'loan_name': loan['name'],
                'interest_rate': loan['interest_rate'],
                'minimum_payment': loan['payment'],
                'extra_payment': round(payment - loan['payment'], 2),
                'total_payment': round(payment, 2),
                'remaining_balance': round(loan['balance'], 2)
            })
        plan.append(month_info)
        month += 1

    return {'plan': plan}
