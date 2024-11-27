from __init__ import app, db
from models import Category

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        default_categories = [
            {'name': 'Зарплата', 'type': 'income'},
            {'name': 'Инвестиции', 'type': 'income'},
            {'name': 'Продукты', 'type': 'expense'},
            {'name': 'Развлечения', 'type': 'expense'}
        ]

        for cat in default_categories:
            category = Category(name=cat['name'], type=cat['type'])
            db.session.add(category)
        db.session.commit()