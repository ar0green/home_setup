from models import Base, engine, SessionLocal, Category

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if session.query(Category).count() == 0:
        default_categories = [
            {'name': 'Зарплата', 'type': 'income'},
            {'name': 'Инвестиции', 'type': 'income'},
            {'name': 'Продукты', 'type': 'expense'},
            {'name': 'Развлечения', 'type': 'expense'}
        ]
        for cat in default_categories:
            c = Category(name=cat['name'], type=cat['type'])
            session.add(c)
        session.commit()
    session.close()

if __name__ == '__main__':
    init_db()
