from pydantic import BaseModel, validator, ValidationError, condecimal
from datetime import date
from typing import List, Optional
import requests

class Expense(BaseModel):
    id: int
    description: str
    amount: condecimal(gt=0)
    category: str
    date: date

    @validator('description')
    def description_min_length(cls, v):
        if len(v) < 3:
            raise ValueError("A descrição deve ter pelo menos 3 caracteres")
        return v

    @validator('category')
    def category_not_empty(cls, v):
        if not v.strip():
            raise ValueError("A categoria não pode ser vazia")
        return v

class ExpenseRepository:
    def __init__(self):
        self._expenses: List[Expense] = []
        self._next_id = 1

    def add(self, expense_data: dict) -> Expense:
        expense = Expense(id=self._next_id, **expense_data)
        self._expenses.append(expense)
        self._next_id += 1
        return expense

    def get_all(self) -> List[Expense]:
        return self._expenses

    def get_by_id(self, expense_id: int) -> Optional[Expense]:
        for expense in self._expenses:
            if expense.id == expense_id:
                return expense
        return None

class FinancialManager:
    def __init__(self, repository: ExpenseRepository):
        self.repository = repository

    def add_expense(self, expense_data: dict) -> Expense:
        return self.repository.add(expense_data)

    def get_total_expenses(self) -> float:
        return float(sum(exp.amount for exp in self.repository.get_all()))

    def categorize_expense_by_cost(self, expense: Expense) -> str:
        if expense.amount <= 20.0:
            return "Baixo"
        elif expense.amount <= 100.0:
            return "Médio"
        else:
            return "Alto"

def get_expense_in_usd(expense: Expense) -> Optional[float]:
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/BRL")
        if response.status_code != 200:
            return None
        data = response.json()
        rate = data.get("rates", {}).get("USD")
        if rate is None:
            return None
        return round(float(expense.amount) * rate, 2)
    except Exception:
        return None
