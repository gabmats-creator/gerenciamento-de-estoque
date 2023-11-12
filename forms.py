from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, IntegerField, DateField, PasswordField, SelectField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, Email, Length, EqualTo

class ProductForm(FlaskForm):
    product_name = StringField("Nome do produto", validators=[InputRequired(message="Esse campo é obrigatório")])
    product_value = FloatField("Valor do produto", validators=[InputRequired(message="Esse campo é obrigatório")])
    emmit_date = DateField("Data de vencimento", validators=[InputRequired(message="Esse campo é obrigatório")])
    description = StringField("Descrição")
    # opcoes = [('', 'Selecione uma opção'), ('mensal', 'Mensal'), ('anual', 'Anual'), ('uma vez', 'Uma vez')]
    # frequence = SelectField('Recorrência', choices=opcoes)
    submit = SubmitField("Registrar")

class RegisterForm(FlaskForm):
    nome = StringField("Nome completo do usuário", validators=[InputRequired(message="Esse campo é obrigatório")])
    email = StringField("E-mail", validators=[InputRequired(message="Esse campo é obrigatório"), Email()])
    telefone = StringField("Telefone", validators=[InputRequired(message="Esse campo é obrigatório")])
    cnpj = StringField("Cnpj da Empresa", validators=[InputRequired(message="Esse campo é obrigatório")])
    password = PasswordField("Senha", validators=[InputRequired(message="Esse campo é obrigatório"), Length(min=4, max=20, message="Sua senha deve ter entre 4 e 20 caracteres")])
    confirm_password = PasswordField("Confirme sua senha", validators=[InputRequired(message="Esse campo é obrigatório"), EqualTo("password", message="Suas senhas devem ser iguais")])
    submit = SubmitField("Registrar")

class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[InputRequired(message="Esse campo é obrigatório"), Email()])
    password = PasswordField("Senha", validators=[InputRequired(message="Esse campo é obrigatório"), Length(min=4, max=20, message="Sua senha deve ter entre 4 e 20 caracteres")])
    submit = SubmitField("Fazer login")

class StringListField(TextAreaField):
    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""
        
    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = [line.strip() for line in valuelist[0].split("\n")]
        else:
            self.data = []

class ExtendedBillForm(ProductForm):
    submit = SubmitField("Enviar")

class EnterpriseForm(FlaskForm):
    enterprise_name = StringField("Nome da empresa", validators=[InputRequired(message="Esse campo é obrigatório")])
    address = StringField("Endereço", validators=[InputRequired(message="Esse campo é obrigatório")])
    email = StringField("E-mail", validators=[InputRequired(message="Esse campo é obrigatório")])
    phone = StringField("Telefone", validators=[InputRequired(message="Esse campo é obrigatório")])
    submit = SubmitField("Concluir")