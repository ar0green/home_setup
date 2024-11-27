from flask_wtf import FlaskForm
from wtforms import FloatField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired
from datetime import datetime

class IncomeForm(FlaskForm):
    amount = FloatField('Сумма', validators=[DataRequired()], render_kw={"placeholder": "Например, 50000"})
    date = DateField('Дата', validators=[DataRequired()], default=datetime.today, format='%Y-%m-%d')
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Добавить доход')

    def __init__(self, session, *args, **kwargs):
        super(IncomeForm, self).__init__(*args, **kwargs)
        from application.views import Category
        self.category.choices = [(c.id, c.name) for c in session.query(Category).filter_by(type='income').all()]

class ExpenseForm(FlaskForm):
    amount = FloatField('Сумма', validators=[DataRequired()], render_kw={"placeholder": "Например, 15000"})
    date = DateField('Дата', validators=[DataRequired()], default=datetime.today, format='%Y-%m-%d')
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Добавить расход')

    def __init__(self, session, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        from application.views import Category
        self.category.choices = [(c.id, c.name) for c in session.query(Category).filter_by(type='expense').all()]
