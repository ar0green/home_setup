from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import date

Base = declarative_base()

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    type = Column(String(50), nullable=False)  # 'income' или 'expense'
    incomes = relationship("Income", back_populates="category")
    expenses = relationship("Expense", back_populates="category")

class Income(Base):
    __tablename__ = 'income'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=date.today())
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship("Category", back_populates="incomes")

class Expense(Base):
    __tablename__ = 'expense'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=date.today())
    category_id = Column(Integer, ForeignKey('category.id'), nullable=False)
    category = relationship("Category", back_populates="expenses")

class Loan(Base):
    __tablename__ = 'loan'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    balance = Column(Float, nullable=False)
    payment = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)

# Подключение к SQLite
engine = create_engine('sqlite:///finance.db', echo=False)
SessionLocal = sessionmaker(bind=engine)
