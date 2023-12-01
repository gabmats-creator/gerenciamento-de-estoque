# Projeto PI Stock Control

## Objetivo:

Nosso projeto, desenvolvido para as unidades curriculares de Projeto Interdisciplinar e Desenvolvimento Web, baseia-se em um sistema de controle de estoque, onde funcionários de uma empresa podem cadastrar a entrada e a saída de produtos do sistema.         

## Tecnologias:

Este projeto foi desenvolvido em Python através do framework para web Flask, utilizando o banco de dados MongoDB.

## Overview:
### Cadastro e acesso
Nosso projeto é abrangente a nível de empresa, no cadastro, o usuário irá informar o CNPJ da empresa da qual ele faz parte, se essa empresa já estiver previamente cadastrada no sistema, o usuário será cadastrado como um funcionário dessa empresa, caso contrário, o usuário precisará cadastrar sua empresa, informando mais alguns dados sobre ela para que o cadastro seja realizado com sucesso, nesse caso o usuário que cadastrou a empresa será o gerente dela.

### Permissões: Funcionário
Poderá cadastrar novos produtos no sistema, acessar todos os produtos cadastrados dentro da empresa, apresentando informaçõe, entre elas o valor e o nome do funcionário que cadastrou aquele produto no sistema, poderá acessar suas próprias vendas, adicionar produtos ao carrinho e vendê-los.

### Permissões: Gerente
Possui todas as permissões que um funcionário, além disso, pode acessar todas as vendas realizadas pela empresa, incluindo informações como nome do funcionário, comissão calculada da venda, valor da venda. Também pode visualizar todos os funcionários cadastrados na sua empresa, tendo informações como a comissão total das vendas realizadas por aquele funcionário. Além de tudo isso, também tem permissão editar informações, excluir e adicionar outros funcionários no sistema, inserindo suas informações de cadastro.

## Funcionalidades principais:

O fluxo básico do sistema inclui cadastrar produtos (se dois produtos de mesmo nome forem inseridos, apenas a quantidade é alterada), registrar a entrada ou a saída de produtos do sistema, controlar vendas, comissões e desempenho profissional (pessoal se for funcionário, todos os funcionários se for gerente).

Para melhor visualização, nosso projeto está disponível em: [StockControl](https://stockcontrol-jwq1.onrender.com)
