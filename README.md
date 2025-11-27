# Crediário – Sistema de Gestão de Clientes, Notas e Pagamentos

![badge-python](https://img.shields.io/badge/Python-3.13-blue)
![badge-django](https://img.shields.io/badge/Django-5.0-green)
![badge-postgres](https://img.shields.io/badge/PostgreSQL-15-blue)
![badge-license](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Sobre o Projeto
O **Crediário** é um sistema completo para gerenciamento de clientes, notas, pagamentos e anexos, ideal para pequenos negócios que trabalham com vendas fiadas.  
Ele controla limites, saldos, itens da nota e impede pagamentos maiores que o valor devido através de validação inteligente + modal no frontend.

---

## 🚀 Funcionalidades
- Cadastro de clientes  
- Criação de notas (aberta, parcial, paga)  
- Itens dentro da nota com cálculo automático  
- Pagamentos com:
  - verificação de saldo pendente
  - modal antes de enviar pagamento inválido
  - botão *"ajustar ao máximo"*
- Atualização automática do saldo do cliente
- Upload de anexos da nota (imagens)
- Interface amigável com Bootstrap 5

---

## 📸 Screenshots

Coloque estes arquivos na pasta `/screenshots`:

```
screenshots/notas.png  
screenshots/pagamento.png  
screenshots/modal_excesso.png  
```

E no README, aparecerão assim:

### Tela de Notas Recentes
![Notas](screenshots/notas.png)

### Tela de Nota Aberta em Detalhes
![Notas](screenshots/NotaAberta.png)

### Registrar Pagamento
![Pagamento](screenshots/pagamento.png)

### Modal de Erro de Pagamento Excedente
![Modal](screenshots/modal_excesso.png)

---

## 🛠️ Instalação e Setup

### 1️⃣ Clonar o repositório
```bash
git clone https://github.com/seu-usuario/crediario.git
cd crediario
```

### 2️⃣ Criar ambiente virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
.\.venv\Scripts\activate  # Windows
```

### 3️⃣ Instalar dependências
```bash
pip install -r requirements.txt
```

### 4️⃣ Criar o arquivo `.env`
```
DB_NAME=crediario
DB_USER=cred_user
DB_PASS=cred_pass
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=SUA_SECRET_KEY
DEBUG=True
```

### 5️⃣ Migrar banco
```bash
python manage.py migrate
```

### 6️⃣ Rodar servidor
```bash
python manage.py runserver
```

---

## ⚙️ Lógica Importante

### ✔ Atualização de Saldo do Cliente
- O saldo muda apenas pela diferença (delta) entre o valor antigo e o novo.

### ✔ Pagamentos com Proteção
- O backend impede salvar pagamentos acima do valor devido.
- O frontend mostra modal antes disso acontecer.

### ✔ Modal Inteligente
Exibe:
> "Falta pagar apenas R$ X,XX"

E tem botão:
> **Ajustar ao máximo**

---

## 📁 Estrutura de Pastas Recomendada
```
/crediario
  /static
  /templates
  /screenshots
  manage.py
  README.md
```

---

## 📝 Licença
MIT – livre para uso, estudo e modificação.

---

Desenvolvido por Vinicius Lima 💙
