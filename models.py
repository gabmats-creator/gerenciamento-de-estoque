from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Product:
    _id: str
    productName: str
    productValue: float
    emmitDate: str
    description: str
    insertDate: str
    employee_name: str
    employee_id: str
    quantidade: int

@dataclass
class User:
    _id: str
    name: str
    email: str
    telefone: str
    cnpj: str
    admin: bool
    enterprise_id: str
    password: str
    products: list[str] = field(default_factory=list)

@dataclass
class Enterprise:
    _id: str
    enterpriseName: str
    email: str
    telefone: str
    cnpj: str
    endereco: str
    products: list[str] = field(default_factory=list)