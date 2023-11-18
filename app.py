from flask import (
    Flask,
    render_template,
    url_for,
    request,
    session,
    redirect,
    flash,
    current_app,
)
from dataclasses import asdict
from forms import ProductForm, RegisterForm, LoginForm, EnterpriseForm
from models import Product, User, Enterprise, Sale
from pymongo import MongoClient
from passlib.hash import pbkdf2_sha256
from datetime import datetime
import uuid
import functools
import os
import re


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "pf9Wkove4IKEAXvy-cQkeDPhv9Cb3Ag-wyJILbq_dFz"
    )
    app.config["MONGODB_URI"] = os.environ.get("MONGODB_URI")
    app.db = MongoClient(app.config["MONGODB_URI"]).get_default_database()

    def login_required(route):
        @functools.wraps(route)
        def route_wrapper(*args, **kwargs):
            if session.get("email") is None:
                return redirect(url_for(".login"))

            return route(*args, **kwargs)

        return route_wrapper

    def formata_reais(valor):
        valor_formatado = f"R$ {float(valor):.2f}"
        return re.sub(re.escape("."), ",", valor_formatado)

    def format_today_date():
        return datetime.now().strftime("%d/%m/%Y %H:%M")

    def calcula_totvendas(sales):
        total = 0
        for sale in sales:
            number = sale.number
            total += sale.total
        return total, number

    def create_sale(total, products, client):
        commission = total * 0.07
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)

        number = 1
        sale_data = current_app.db.sales.find({"employee_id": user._id})
        for sale in sale_data:
            number += 1

        sale = Sale(
            _id=uuid.uuid4().hex,
            date=format_today_date(),
            total=total,
            employee_id=user._id,
            employee_name=user.name,
            commission=commission,
            number=number,
            enterprise_id=user.enterprise_id,
            products=products,
            cliente=client,
        )
        current_app.db.sales.insert_one(asdict(sale))
        current_app.db.users.update_one(
            {"_id": user._id},
            {"$set": {"totalCommission": float(user.totalCommission) + commission}},
        )

    @app.route("/")
    @login_required
    def index():
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        enterprise_data = current_app.db.enterprises.find_one(
            {"_id": user.enterprise_id}
        )
        enterprise = Enterprise(**enterprise_data)
        product_data = (
            current_app.db.products.find(
                {"_id": {"$in": enterprise.products}, "quantidadeTotal": {"$gt": 0}}
            )
            .sort("insertDate", -1)
            .limit(3)
        )
        product = [Product(**product) for product in product_data]
        for produto in product:
            produto.productValue = formata_reais(float(produto.productValue))

        total_reais, total_qtd = 0, 0
        if user.admin:
            sale_data = current_app.db.sales.find({"enterprise_id": enterprise._id})
            sales = [Sale(**sal) for sal in sale_data]
            if sales:
                total_reais, total_qtd = calcula_totvendas(sales)
                total_reais = formata_reais(total_reais)

        return render_template(
            "index.html",
            title="StockControl - Início",
            product_data=product,
            user_name=user.name,
            enterprise=enterprise.enterpriseName,
            cargo=user.admin,
            total_reais=total_reais,
            total_qtd=total_qtd,
            commission=formata_reais(user.totalCommission),
        )

    @app.route("/produtos", methods=["GET", "POST"])
    @login_required
    def products(
        confirm_edit=None,
        product=None,
        confirm_kart=None,
        erro=None,
        qtdeDispo=None,
        qtdeCarrinho=None,
        sale_kart=None,
        error=None,
    ):
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        enterprise_data = current_app.db.enterprises.find_one(
            {"_id": user.enterprise_id}
        )
        enterprise = Enterprise(**enterprise_data)
        indisp = None
        if not product:
            product_data = current_app.db.products.find(
                {"_id": {"$in": enterprise.products}, "quantidadeTotal": {"$gt": 0}}
            )
            product = [Product(**prod) for prod in product_data]
            for produto in product:
                produto.productValue = formata_reais(float(produto.productValue))

            indisp_data = current_app.db.products.find(
                {"_id": {"$in": enterprise.products}, "quantidadeTotal": 0}
            )
            indisp = [Product(**ind) for ind in indisp_data]

        return render_template(
            "products.html",
            title="Stock Control - Produtos",
            product_data=product,
            indisp=indisp,
            confirm_kart=confirm_kart,
            erro=erro,
            qtdeDispo=qtdeDispo,
            qtdeCarrinho=qtdeCarrinho,
            sale_kart=sale_kart,
            confirm_edit=confirm_edit,
            error=error,
        )

    @app.route("/add", methods=["GET", "POST"])
    @login_required
    def add_product():
        form = ProductForm()

        if form.validate_on_submit():
            description = "" if not form.description.data else form.description.data
            user_data = current_app.db.users.find_one({"email": session["email"]})
            user = User(**user_data)
            enterprise_data = current_app.db.enterprises.find_one(
                {"_id": user.enterprise_id}
            )
            enterprise = Enterprise(**enterprise_data)
            products_data_name = current_app.db.products.find(
                {"_id": {"$in": enterprise.products}}
            )
            found = False
            for produto in products_data_name:
                if form.product_name.data == produto["productName"]:
                    _id = produto["_id"]
                    quantidade = produto["quantidadeTotal"]
                    found = True

            if not found:
                product = Product(
                    _id=uuid.uuid4().hex,
                    productName=form.product_name.data,
                    productValue=form.product_value.data,
                    description=description,
                    insertDate=format_today_date(),
                    employee_name=user.name,
                    employee_id=user._id,
                    quantidadeTotal=form.amount.data,
                    quantidadeCarrinho=0,
                )
                current_app.db.products.insert_one(asdict(product))
                current_app.db.enterprises.update_one(
                    {"_id": user.enterprise_id}, {"$push": {"products": product._id}}
                )

            else:
                current_app.db.products.update_one(
                    {"_id": _id},
                    {
                        "$set": {
                            "quantidadeTotal": quantidade + form.amount.data,
                            "employee_name": user.name,
                            "productValue": form.product_value.data,
                        }
                    },
                )

            return redirect(url_for(".index"))

        return render_template(
            "new_product.html", title="Stock Control - Adicionar Conta", form=form
        )

    @app.route("/add_enterprise", methods=["GET", "POST"])
    def add_enterprise():
        user_id = request.args.get("user_id")
        cnpj = request.args.get("cnpj")
        message = request.args.get("message")
        form = EnterpriseForm()
        if form.validate_on_submit():
            enterprise = Enterprise(
                _id=uuid.uuid4().hex,
                enterpriseName=form.enterprise_name.data,
                endereco=form.address.data,
                cnpj=cnpj,
                email=form.email.data,
                telefone=form.phone.data,
            )
            current_app.db.enterprises.insert_one(asdict(enterprise))
            current_app.db.users.update_one(
                {"_id": user_id}, {"$set": {"enterprise_id": enterprise._id}}
            )

            return redirect(url_for(".login"))
        return render_template(
            "new_enterprise.html",
            title="Stock Control - Adicionar Empresa",
            form=form,
            message=message,
        )

    @app.route("/edit/<string:_id>", methods=["GET", "POST"])
    @login_required
    def edit_product(_id: str):
        operacao = request.form.get("operacao")
        products_data = current_app.db.products.find({"_id": _id})
        product = [Product(**prod) for prod in products_data]
        if request.method == "POST":
            if operacao == "Confirmar":
                user_data = current_app.db.users.find_one({"email": session["email"]})
                user = User(**user_data)
                current_app.db.products.update_one(
                    {"_id": _id},
                    {
                        "$set": {
                            "employee_name": user.name,
                            "employee_id": user._id,
                            "insertDate": format_today_date(),
                        }
                    },
                )
                if request.form.get("productName"):
                    current_app.db.products.update_one(
                        {"_id": _id},
                        {"$set": {"productName": request.form.get("productName")}},
                    )
                if request.form.get("productValue"):
                    current_app.db.products.update_one(
                        {"_id": _id},
                        {"$set": {"productValue": request.form.get("productValue")}},
                    )
                qtdeTotal = int(request.form.get("quantidadeTotal"))
                if qtdeTotal >= 0:
                    current_app.db.products.update_one(
                        {"_id": _id},
                        {"$set": {"quantidadeTotal": qtdeTotal}},
                    )
                    if qtdeTotal < product[0].quantidadeCarrinho:
                        current_app.db.products.update_one(
                            {"_id": _id},
                            {"$set": {"quantidadeCarrinho": qtdeTotal}},
                        )

                current_app.db.products.update_one(
                    {"_id": _id},
                    {"$set": {"description": request.form.get("description")}},
                )

            return redirect(url_for(".products"))

        return products(confirm_edit=True, product=product)

    @app.route("/carrinho", methods=["GET", "POST"])
    @login_required
    def shopping_kart(delete_kart=None, confirm_edit=None, sale_kart=None, error=None):
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        enterprise_data = current_app.db.enterprises.find_one(
            {"_id": user.enterprise_id}
        )
        enterprise = Enterprise(**enterprise_data)

        product_data = current_app.db.products.find(
            {"_id": {"$in": enterprise.products}, "quantidadeCarrinho": {"$ne": 0}}
        )
        product = [Product(**prod) for prod in product_data]
        for produto in product:
            produto.productValue = formata_reais(produto.productValue)

        return render_template(
            "shopping_kart.html",
            title="Stock Control - Carrinho",
            product_data=product,
            delete_kart=delete_kart,
            confirm_edit=confirm_edit,
            sale_kart=sale_kart,
            error=error,
        )

    @app.route("/carrinho-confirmar/<string:_id>", methods=["GET", "POST"])
    @login_required
    def confirm_kart(_id: str):
        erro = None
        product_data = current_app.db.products.find_one({"_id": _id})
        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "confirmar":
                amount = (
                    int(request.form.get("amount")) if request.form.get("amount") else 0
                )
                qtde = product_data["quantidadeCarrinho"] + amount
                if qtde <= product_data["quantidadeTotal"]:
                    current_app.db.products.update_one(
                        {"_id": _id}, {"$set": {"quantidadeCarrinho": qtde}}
                    )
                else:
                    erro = "A quantidade inserida no carrinho não pode ser maior que a quantidade total em estoque"
                    return products(
                        confirm_kart=True,
                        qtdeDispo=product_data["quantidadeTotal"]
                        - product_data["quantidadeCarrinho"],
                        qtdeCarrinho=product_data["quantidadeCarrinho"],
                        erro=erro,
                    )

            return redirect(url_for(".products"))

        return products(
            confirm_kart=True,
            qtdeDispo=product_data["quantidadeTotal"]
            - product_data["quantidadeCarrinho"],
            qtdeCarrinho=product_data["quantidadeCarrinho"],
        )

    @app.route("/carrinho-remover/<string:_id>", methods=["GET", "POST"])
    @login_required
    def remove_kart(_id: str):
        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "remove_kart":
                current_app.db.products.update_one(
                    {"_id": _id}, {"$set": {"quantidadeCarrinho": 0}}
                )

            return redirect(url_for(".shopping_kart"))

        return shopping_kart(delete_kart=True)

    @app.route("/carrinho-confirmar-venda/", methods=["GET", "POST"])
    @login_required
    def sale():
        if request.args.get("_id"):
            if request.method == "POST":
                operacao = request.form.get("operacao")
                if operacao == "confirmar":
                    if not request.form.get("client"):
                        error = "Insira o nome do cliente"
                        return products(sale_kart=True, error=error)
                    user_data = current_app.db.users.find_one(
                        {"email": session["email"]}
                    )
                    user = User(**user_data)
                    enterprise_data = current_app.db.enterprises.find_one(
                        {"_id": user.enterprise_id}
                    )
                    enterprise = Enterprise(**enterprise_data)
                    product_data = current_app.db.products.find_one(
                        {"_id": request.args.get("_id")}
                    )
                    if product_data["quantidadeTotal"] > 0:
                        if (
                            product_data["quantidadeTotal"] - 1
                            < product_data["quantidadeCarrinho"]
                        ):
                            current_app.db.products.update_one(
                                {"_id": request.args.get("_id")},
                                {
                                    "$set": {
                                        "quantidadeCarrinho": product_data[
                                            "quantidadeTotal"
                                        ]
                                        - 1,
                                    }
                                },
                            )

                        current_app.db.products.update_one(
                            {"_id": request.args.get("_id")},
                            {
                                "$set": {
                                    "quantidadeTotal": product_data["quantidadeTotal"]
                                    - 1
                                }
                            },
                        )
                        prod_name = "{}({}un.)".format(product_data["productName"], 1)
                        create_sale(
                            float(product_data["productValue"]),
                            [prod_name],
                            request.form.get("client"),
                        )

                return redirect(url_for(".products"))
            return products(sale_kart=True)

        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "confirmar":
                if not request.form.get("client"):
                    error = "Insira o nome do cliente"
                    return shopping_kart(sale_kart=True, error=error)
                user_data = current_app.db.users.find_one({"email": session["email"]})
                user = User(**user_data)
                enterprise_data = current_app.db.enterprises.find_one(
                    {"_id": user.enterprise_id}
                )
                enterprise = Enterprise(**enterprise_data)
                product_data = current_app.db.products.find(
                    {"_id": {"$in": enterprise.products}}
                )
                sale = []
                total = 0.0
                for produto in product_data:
                    if produto["quantidadeCarrinho"]:
                        sale.append(
                            "{}({}un.)".format(
                                produto["productName"], produto["quantidadeCarrinho"]
                            )
                        )
                        total += float(produto["productValue"]) * int(
                            produto["quantidadeCarrinho"]
                        )
                        current_app.db.products.update_one(
                            {"_id": produto["_id"]},
                            {
                                "$set": {
                                    "quantidadeCarrinho": 0,
                                    "quantidadeTotal": produto["quantidadeTotal"]
                                    - produto["quantidadeCarrinho"],
                                }
                            },
                        )
                create_sale(total, sale, request.form["client"])

            return redirect(url_for(".shopping_kart"))

        return shopping_kart(sale_kart=True)

    @app.route("/suas-vendas")
    @login_required
    def your_sales():
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        sale_data = current_app.db.sales.find({"employee_id": user._id})
        sale = [Sale(**sal) for sal in sale_data]
        for venda in sale:
            venda.commission = formata_reais(float(venda.commission))
            venda.total = formata_reais(float(venda.total))

        return render_template("your_sales.html", vendas=sale)

    @app.route("/vendas")
    @login_required
    def all_sales():
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        enterprise_data = current_app.db.enterprises.find_one(
            {"_id": user.enterprise_id}
        )
        enterprise = Enterprise(**enterprise_data)
        sale_data = current_app.db.sales.find({"enterprise_id": enterprise._id})
        sales = [Sale(**sal) for sal in sale_data]
        for venda in sales:
            venda.commission = formata_reais(float(venda.commission))
            venda.total = formata_reais(venda.total)
        return render_template("all_sales.html", sale_data=sales)

    @app.get("/toggle-theme")
    def toggle_theme():
        current_theme = session.get("theme")
        if current_theme == "dark":
            session["theme"] = "light"
        else:
            session["theme"] = "dark"

        return redirect(request.args.get("current_page"))

    @app.route("/novo-funcionario", methods=["GET", "POST"])
    @login_required
    def new_employee():
        form = RegisterForm()

        if request.method == "POST":
            if current_app.db.users.find_one({"email": form.email.data}):
                flash("Este email já está em uso", category="danger")
                return redirect(url_for(".new_employee"))
            else:
                user_data = current_app.db.users.find_one({"email": session["email"]})
                _user = User(**user_data)
                user = User(
                    _id=uuid.uuid4().hex,
                    name=form.nome.data,
                    email=form.email.data,
                    telefone=form.telefone.data,
                    cnpj=_user.cnpj,
                    admin=False,
                    enterprise_id=_user.enterprise_id,
                    totalCommission=0,
                    password=pbkdf2_sha256.hash(form.password.data),
                )
                current_app.db.users.insert_one(asdict(user))

                return redirect(url_for(".index"))

        return render_template(
            "new_employee.html", title="StockControl - Novo Funcionário", form=form
        )

    @app.route("/funcionários")
    @login_required
    def employees(confirm_edit=None, employee_data=None, confirm_delete=None):
        if not employee_data:
            _user_data = current_app.db.users.find_one({"email": session["email"]})
            _user = User(**_user_data)
            user_data = current_app.db.users.find(
                {"enterprise_id": _user.enterprise_id}
            )
            employee_data = [User(**us) for us in user_data]
            for emp in employee_data:
                emp.totalCommission = formata_reais(emp.totalCommission)

        return render_template(
            "employees.html",
            employee_data=employee_data,
            confirm_edit=confirm_edit,
            confirm_delete=confirm_delete,
        )

    @app.route("/edit-employee/<string:_id>", methods=["GET", "POST"])
    @login_required
    def edit_employee(_id: str):
        operacao = request.form.get("operacao")
        user_data = current_app.db.users.find({"_id": _id})
        user = [User(**us) for us in user_data]
        if request.method == "POST":
            if operacao == "Confirmar":
                if request.form.get("name"):
                    current_app.db.users.update_one(
                        {"_id": _id},
                        {"$set": {"name": request.form.get("name")}},
                    )
                if request.form.get("email"):
                    found = False
                    if user[0].email == session["email"]:
                        found = True
                    current_app.db.users.update_one(
                        {"_id": _id},
                        {"$set": {"email": request.form.get("email")}},
                    )
                    if found:
                        session["email"] = request.form.get("email")

                if request.form.get("telefone"):
                    current_app.db.users.update_one(
                        {"_id": _id},
                        {"$set": {"telefone": request.form.get("telefone")}},
                    )

            return redirect(url_for(".employees"))

        return employees(confirm_edit=True, employee_data=user)

    @app.route("/delete-employee/<string:_id>", methods=["GET", "POST"])
    @login_required
    def delete_employee(_id: str):
        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "excluir":
                user_data = current_app.db.users.find_one({"email": session["email"]})
                user = User(**user_data)
                current_app.db.users.delete_one({"_id": _id})
                if _id == user._id:
                    current_app.db.enterprises.delete_one({"_id": user.enterprise_id})
                    session.clear()

            return redirect(url_for(".employees"))

        return employees(confirm_delete=True)

    @app.route("/registrar", methods=["GET", "POST"])
    def register():
        if session.get("email"):
            return redirect(url_for(".index"))
        form = RegisterForm()

        if form.validate_on_submit():
            if current_app.db.users.find_one({"email": form.email.data}):
                flash("Este email já está em uso", category="danger")
                return redirect(url_for(".register"))
            else:
                enterprises = current_app.db.enterprises.find({})
                admin = True
                enterprise_id = ""
                for enterprise in enterprises:
                    if form.cnpj.data == enterprise["cnpj"]:
                        admin = False
                        enterprise_id = enterprise["_id"]
                        break

                user = User(
                    _id=uuid.uuid4().hex,
                    name=form.nome.data,
                    email=form.email.data,
                    telefone=form.telefone.data,
                    cnpj=form.cnpj.data,
                    admin=admin,
                    enterprise_id=enterprise_id,
                    totalCommission=0,
                    password=pbkdf2_sha256.hash(form.password.data),
                )
                current_app.db.users.insert_one(asdict(user))

                if not enterprise_id:
                    return redirect(
                        url_for(".add_enterprise", user_id=user._id, cnpj=user.cnpj)
                    )

                flash("Usuário registrado com sucesso!!")

                return redirect(url_for(".login"))

        return render_template(
            "register.html", title="StockControl - Registrar", form=form
        )

    @app.route("/logout")
    def logout():
        current_theme = session.get("theme")
        session["theme"] = current_theme
        del session["user_id"]
        del session["email"]

        return redirect(url_for(".login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("email"):
            return redirect(url_for(".index"))

        form = LoginForm()

        if form.validate_on_submit():
            user_data = current_app.db.users.find_one({"email": form.email.data})
            if not user_data:
                flash("Dados de login incorretos", category="danger")
                return redirect(url_for(".login"))
            user = User(**user_data)

            if not user.enterprise_id:
                return redirect(
                    url_for(
                        ".add_enterprise",
                        user_id=user._id,
                        cnpj=user.cnpj,
                        message=True,
                    )
                )

            if user and pbkdf2_sha256.verify(form.password.data, user.password):
                session["user_id"] = user._id
                session["email"] = user.email

                return redirect(url_for(".index"))
            flash("Dados de login incorretos", category="danger")
        return render_template("login.html", title="Stock Control - Login", form=form)

    return app
