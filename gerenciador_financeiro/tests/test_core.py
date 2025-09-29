import pytest
from pydantic import ValidationError
from datetime import date
from src.core import Expense, ExpenseRepository, FinancialManager, get_expense_in_usd
import responses

def test_criar_despesa_valida():
    expense = Expense(
        id=1,
        description="Café da manhã",
        amount=15.50,
        category="Alimentação",
        date=date(2025, 9, 21)
    )
    assert expense.id == 1
    assert expense.description == "Café da manhã"
    assert expense.amount == 15.50

def test_nao_criar_despesa_com_valor_negativo():
    with pytest.raises(ValidationError) as excinfo:
        Expense(id=2, description="Invalido", amount=-100, category="Teste", date=date.today())
    assert "Input should be greater than 0" in str(excinfo.value)

def test_nao_criar_despesa_com_descricao_curta():
    with pytest.raises(ValidationError):
        Expense(id=3, description="ab", amount=20, category="Teste", date=date.today())

def test_nao_criar_despesa_com_categoria_vazia():
    with pytest.raises(ValueError) as excinfo:
        Expense(id=4, description="Teste categoria", amount=50, category="   ", date=date.today())
    assert "A categoria não pode ser vazia" in str(excinfo.value)

@pytest.fixture
def repo():
    return ExpenseRepository()

def test_adicionar_despesa_ao_repositorio(repo):
    expense_data = {
        "description": "Almoço", "amount": 35.0, "category": "Alimentação", "date": date.today()
    }
    new_expense = repo.add(expense_data)
    
    assert new_expense.id == 1
    assert len(repo.get_all()) == 1
    assert repo.get_by_id(1) == new_expense

def test_buscar_despesa_por_id_existente(repo):
    expense_data = {"description": "Cinema", "amount": 50.0, "category": "Lazer", "date": date.today()}
    repo.add(expense_data)
    
    found_expense = repo.get_by_id(1)
    assert found_expense is not None
    assert found_expense.id == 1
    assert found_expense.description == "Cinema"

def test_buscar_despesa_por_id_inexistente(repo):
    assert repo.get_by_id(999) is None

def test_adicionar_multiplas_despesas_incrementa_id(repo):
    repo.add({"description": "Uber", "amount": 22.0, "category": "Transporte", "date": date.today()})
    repo.add({"description": "Livro", "amount": 80.0, "category": "Educação", "date": date.today()})
    
    despesa_2 = repo.get_by_id(2)
    assert len(repo.get_all()) == 2
    assert despesa_2 is not None
    assert despesa_2.description == "Livro"

def test_financial_manager_adiciona_despesa(mocker):
    mock_repo = mocker.MagicMock(spec=ExpenseRepository)
    manager = FinancialManager(repository=mock_repo)
    
    expense_data = {"description": "Jantar", "amount": 120.0, "category": "Alimentação", "date": date.today()}
    manager.add_expense(expense_data)
    
    mock_repo.add.assert_called_once_with(expense_data)

def test_get_total_expenses_com_varias_despesas(mocker):
    mock_repo = mocker.MagicMock(spec=ExpenseRepository)
    mock_repo.get_all.return_value = [
        Expense(id=1, description="aaa", amount=10.50, category="c", date=date.today()),
        Expense(id=2, description="bbb", amount=20.00, category="c", date=date.today()),
        Expense(id=3, description="ccc", amount=0.50, category="c", date=date.today()),
    ]
    
    manager = FinancialManager(repository=mock_repo)
    total = manager.get_total_expenses()
    
    assert total == 31.00


def test_get_total_expenses_sem_despesas(mocker):
    mock_repo = mocker.MagicMock(spec=ExpenseRepository)
    mock_repo.get_all.return_value = []
    
    manager = FinancialManager(repository=mock_repo)
    total = manager.get_total_expenses()
    
    assert total == 0.0

@pytest.mark.parametrize(
    "amount, expected_category",
    [
        (15.0, "Baixo"),
        (20.0, "Baixo"),
        (20.01, "Médio"),
        (100.0, "Médio"),
        (100.01, "Alto"),
        (5000.0, "Alto"),
    ]
)
def test_categorize_expense_by_cost(amount, expected_category):
    manager = FinancialManager(repository=None)
    expense = Expense(id=1, description="Teste", amount=amount, category="cat", date=date.today())
    
    result = manager.categorize_expense_by_cost(expense)
    
    assert result == expected_category

@responses.activate
def test_get_expense_in_usd_sucesso():
    responses.add(
        responses.GET,
        "https://api.exchangerate-api.com/v4/latest/BRL",
        json={"rates": {"USD": 0.20}},
        status=200
    )
    
    expense = Expense(id=1, description="Teste", amount=100.0, category="cat", date=date.today())
    usd_amount = get_expense_in_usd(expense)
    assert usd_amount == 20.00

@responses.activate
def test_get_expense_in_usd_api_falha():
    responses.add(
        responses.GET,
        "https://api.exchangerate-api.com/v4/latest/BRL",
        status=500
    )
    
    expense = Expense(id=1, description="Teste", amount=100.0, category="cat", date=date.today())
    usd_amount = get_expense_in_usd(expense)
    assert usd_amount is None

@responses.activate
def test_get_expense_in_usd_formato_invalido():
    responses.add(
        responses.GET,
        "https://api.exchangerate-api.com/v4/latest/BRL",
        json={"invalid_key": "some_value"},
        status=200
    )
    
    expense = Expense(id=1, description="Teste", amount=100.0, category="cat", date=date.today())
    usd_amount = get_expense_in_usd(expense)
    assert usd_amount is None
 #Comentario#