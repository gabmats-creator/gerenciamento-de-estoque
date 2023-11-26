from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Tuple


@dataclass
class Product:
    _id: str
    productName: str
    productValue: float
    description: str
    insertDate: str
    employee_name: str
    employee_id: str
    quantidadeTotal: int
    quantidadeCarrinho: int


@dataclass
class User:
    _id: str
    name: str
    email: str
    telefone: str
    cnpj: str
    admin: bool
    enterprise_id: str
    totalCommission: float
    password: str
    products: List[str] = field(default_factory=list)


@dataclass
class Enterprise:
    _id: str
    enterpriseName: str
    email: str
    telefone: str
    cnpj: str
    endereco: str
    products: List[str] = field(default_factory=list)
    sales: List[str] = field(default_factory=list)


@dataclass
class Sale:
    _id: str
    date: str
    total: float
    employee_id: str
    employee_name: str
    commission: float
    number: int
    enterprise_id: str
    cliente: str
    products: List[str] = field(default_factory=list)
