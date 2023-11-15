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
import locale


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

    def real_format(value):
        locale.setlocale(locale.LC_ALL, "pt_BR.utf8")
        float_value = value
        formatted_value = locale.currency(float_value, grouping=True, symbol=None)

        return formatted_value

    def create_sale(total, products):
        commission = total * 0.07
        insertion_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        number = 1
        sale_data = current_app.db.sales.find({"employee_id": user._id})
        for sale in sale_data:
            number += 1

        sale = Sale(
            _id=uuid.uuid4().hex,
            date=insertion_date,
            total=total,
            employee_id=user._id,
            employee_name=user.name,
            commission=round(commission),
            products=products,
            number=number,
        )
        current_app.db.sales.insert_one(asdict(sale))

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
            current_app.db.products.find({"_id": {"$in": enterprise.products}})
            .sort("insertDate", -1)
            .limit(3)
        )
        product = [Product(**product) for product in product_data]

        return render_template(
            "index.html",
            title="StockControl - Início",
            product_data=product,
            user_name=user.name,
            enterprise=enterprise.enterpriseName,
            cargo=user.admin,
        )

    @app.route("/produtos-disponiveis", methods=["GET", "POST"])
    @login_required
    def products(
        confirm_delete=None,
        confirm_edit=None,
        product=None,
        confirm_kart=None,
        erro=None,
        qtdeDispo=None,
        qtdeCarrinho=None,
        sale_kart=None,
    ):
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        enterprise_data = current_app.db.enterprises.find_one(
            {"_id": user.enterprise_id}
        )
        enterprise = Enterprise(**enterprise_data)
        if not product:
            product_data = current_app.db.products.find(
                {"_id": {"$in": enterprise.products}, "quantidadeTotal": {"$gt": 0}}
            )
            product = [Product(**prod) for prod in product_data]

        return render_template(
            "products.html",
            title="Stock Control - Contas a Pagar",
            product_data=product,
            confirm_delete=confirm_delete,
            confirm_edit=confirm_edit,
            confirm_kart=confirm_kart,
            erro=erro,
            qtdeDispo=qtdeDispo,
            qtdeCarrinho=qtdeCarrinho,
            sale_kart=sale_kart,
        )

    @app.route("/add", methods=["GET", "POST"])
    @login_required
    def add_product():
        form = ProductForm()

        if form.validate_on_submit():
            emmit_date = str(form.emmit_date.data)
            emmit_formatted = datetime.strptime(emmit_date, "%Y-%m-%d").strftime(
                "%d-%m-%Y"
            )
            insertion_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
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
                    emmitDate=emmit_formatted,
                    description=description,
                    insertDate=insertion_date,
                    employee_name=user.name,
                    employee_id=user._id,
                    quantidadeTotal=1,
                    quantidadeCarrinho=0,
                    carrinho=False,
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
                            "quantidadeTotal": quantidade + 1,
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

            flash("Usuário registrado com sucesso!")
            return redirect(url_for(".login"))
        return render_template(
            "new_enterprise.html",
            title="Stock Control - Adicionar Empresa",
            form=form,
            message=message,
        )

    @app.route("/produto/<string:_id>", methods=["GET", "POST"])
    @login_required
    def delete_product(_id: str):
        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "excluir":
                current_app.db.products.delete_one({"_id": _id})

            return redirect(url_for(".products"))

        return products(confirm_delete=True)

    @app.route("/edit/<string:_id>", methods=["GET", "POST"])
    @login_required
    def edit_product(_id: str):
        operacao = request.form.get("operacao")
        products_data = current_app.db.products.find({"_id": _id})
        product = [Product(**prod) for prod in products_data]
        if request.method == "POST":
            if operacao == "Confirmar":
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
                if request.form.get("employee"):
                    current_app.db.products.update_one(
                        {"_id": _id},
                        {"$set": {"employee": request.form.get("employee")}},
                    )
                if request.form.get("emmitDate"):
                    emmit_date = str(request.form.get("emmitDate"))
                    emmit_formatted = datetime.strptime(
                        emmit_date, "%Y-%m-%d"
                    ).strftime("%d-%m-%Y")
                    current_app.db.products.update_one(
                        {"_id": _id}, {"$set": {"emmitDate": emmit_formatted}}
                    )

                current_app.db.products.update_one(
                    {"_id": _id},
                    {"$set": {"description": request.form.get("description")}},
                )

            return redirect(url_for(".products"))

        return products(confirm_edit=True, product=product)

    @app.route("/carrinho", methods=["GET", "POST"])
    @login_required
    def shopping_kart(delete_kart=None, confirm_edit=None, sale_kart=None):
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

        return render_template(
            "shopping_kart.html",
            title="Stock Control - Contas a Pagar",
            product_data=product,
            delete_kart=delete_kart,
            confirm_edit=confirm_edit,
            sale_kart=sale_kart,
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
                    {"_id": _id}, {"$set": {"carrinho": False}}
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
                    current_app.db.products.update_one(
                        {"_id": request.args.get("_id")},
                        {
                            "$set": {
                                "quantidadeTotal": product_data["quantidadeTotal"] - 1
                            }
                        },
                    )
                    # Já atualizei a quantidade do produto, preciso pedir pro usuário informar, depois, pegar o valor do produto * quantidade pra calcular sua comissão

                return redirect(url_for(".products"))
            return products(sale_kart=True)

        if request.method == "POST":
            operacao = request.form.get("operacao")
            if operacao == "confirmar":
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
                            "{}({}unid.)".format(
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
                create_sale(total, sale)

            return redirect(url_for(".shopping_kart"))

        return shopping_kart(sale_kart=True)

    @app.route("/your-sales")
    @login_required
    def your_sales():
        user_data = current_app.db.users.find_one({"email": session["email"]})
        user = User(**user_data)
        sale_data = current_app.db.sales.find({"employee_id": user._id})
        sale = [Sale(**sal) for sal in sale_data]

        return render_template("your_sales.html", vendas=sale)

    @app.get("/toggle-theme")
    def toggle_theme():
        current_theme = session.get("theme")
        if current_theme == "dark":
            session["theme"] = "light"
        else:
            session["theme"] = "dark"

        return redirect(request.args.get("current_page"))

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
