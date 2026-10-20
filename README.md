# Sistema de Monitoria — IME-USP 🎓

Modernização e refatoração do **Sistema de Monitoria** do Instituto de Matemática e Estatística da Universidade de São Paulo (**IME-USP**), desenvolvido em **Python 3.12** com **FastAPI**, **SQLAlchemy 2.0** e suporte a **Docker / Portainer**.

---

## 📌 Visão Geral

O sistema gerencia todo o ciclo de vida da monitoria acadêmica no instituto:
- **Gestão de Períodos Letivos e Turmas**: Cadastro e sincronização de semestres, departamentos e disciplinas.
- **Requisições de Monitoria**: Solicitações abertas por docentes para suas respectivas turmas.
- **Inscrições de Estudantes**: Formulários e acompanhamento de inscrições de alunos de graduação e pós-graduação.
- **Seleção e Bolsas**: Alocação de monitores (bolsistas e voluntários) e controle de frequência.
- **Avaliações**: Avaliações de desempenho acadêmico das monitorias.
- **Autenticação Corporativa USP**: Login seguro via **Senha Única USP** (OAuth 1.0a em conformidade com o RFC 5849).

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem**: [Python 3.12](https://www.python.org/)
- **Framework Web**: [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **ORM & Validação**: [SQLAlchemy 2.0](https://www.sqlalchemy.org/) e [Pydantic v2](https://docs.pydantic.dev/)
- **Banco de Dados**:
  - **Produção**: [MariaDB 10.11](https://mariadb.org/) (MySQL) com retry automático e auto-seed
  - **Desenvolvimento Local**: [SQLite](https://www.sqlite.org/)
- **Autenticação & Segurança**: [Authlib](https://authlib.org/) e [HTTPX](https://www.python-httpx.org/) (OAuth 1.0a USP com assinatura em Header)
- **Interface & Templates**: [Jinja2](https://jinja.palletsprojects.com/), [Bootstrap 5.3](https://getbootstrap.com/), [FontAwesome 6](https://fontawesome.com/) e Google Fonts (Inter)
- **Containerização**: [Docker](https://www.docker.com/) e [Docker Compose](https://docs.docker.com/compose/)
- **Orquestração**: [Portainer](https://www.portainer.io/) (Stack via repositório Git)

---

## 🚀 Como Executar o Projeto

### Opção 1: Subir via Portainer Stack (Recomendado / Produção)

Este método permite subir o sistema e o banco de dados diretamente a partir do repositório no GitHub.

1. Acesse o painel do seu **Portainer**.
2. No menu lateral, acerte no ambiente desejado e vá em **Stacks** ➔ **Add stack**.
3. Dê um nome para a stack (ex: `monitoria`).
4. Em **Build method**, selecione a aba **Repository**.
5. Preencha os campos do repositório:
   - **Repository URL**: `https://github.com/luiscarlosdesouza/monitoria-python`
   - **Repository reference**: `refs/heads/main`
   - **Compose path**: `docker-compose.yml`
6. Role a página até **Environment variables** e adicione as variáveis de configuração:

| Variável | Valor Exemplo / Descrição |
| :--- | :--- |
| `APP_PORT` | `8020` (porta externa exposta no host) |
| `DB_EXTERNAL_PORT` | `3307` (porta externa do MariaDB para acesso de manutenção) |
| `DB_ROOT_PASSWORD` | Senha de root do MariaDB |
| `DB_DATABASE` | `monitoria_db` |
| `DB_USERNAME` | `monitoria` |
| `DB_PASSWORD` | Senha do usuário da aplicação |
| `SECRET_KEY` | Chave segura para criptografia de cookies e sessões |
| `SENHAUNICA_KEY` | Chave da aplicação cadastrada na Senha Única USP |
| `SENHAUNICA_SECRET` | Secret da aplicação cadastrado na Senha Única USP |
| `SENHAUNICA_CALLBACK_ID`| ID do callback autorizado no cadastro da Senha Única USP |
| `SENHAUNICA_ADMINS` | Números USP dos administradores do sistema (separados por vírgula) |
| `USP_CALLBACK_URL` | URL de retorno do OAuth (ex: `http://localhost:8020/callback` ou seu domínio) |

> 💡 **Nota de Compatibilidade**: O sistema reconhece tanto as variáveis no padrão do sistema legado em Laravel (`SENHAUNICA_KEY`, `SENHAUNICA_SECRET`, `SENHAUNICA_CALLBACK_ID`) quanto no formato `USP_CLIENT_KEY`, `USP_CLIENT_SECRET`, `USP_CALLBACK_ID`.

7. Clique em **Deploy the stack**.
8. Assim que os containers iniciarem, acesse o sistema pelo navegador:
   ```
   http://localhost:8020
   ```

#### 🔄 Como atualizar a Stack no Portainer após novos commits:
Sempre que novas alterações forem enviadas para o GitHub:
1. Abra a stack `monitoria` no Portainer.
2. Acesse a aba **Editor**.
3. Ative a opção **"Re-pull image and redeploy"**.
4. Clique em **Update the stack**.

---

### Opção 2: Subir via Docker Compose (Linha de Comando)

Para quem prefere rodar via terminal diretamente:

```bash
# 1. Clone o repositório
git clone https://github.com/luiscarlosdesouza/monitoria-python.git
cd monitoria-python

# 2. Crie seu arquivo de ambiente
cp .env.example .env

# 3. Configure suas chaves da Senha Única e portas no .env
# nano .env

# 4. Inicie os containers com build
docker compose up -d --build

# 5. Acompanhe os logs
docker compose logs -f app
```

Acesse em: `http://localhost:8020`

---

### Opção 3: Execução Local para Desenvolvimento (Sem Docker)

Ideal para desenvolvimento de novas telas e testes rápidos com banco SQLite local.

```bash
# 1. Crie e ative um ambiente virtual
python -m venv .venv

# No Windows:
.venv\Scripts\activate
# No Linux/macOS:
source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Configure as variáveis de ambiente no arquivo .env
# (Por padrão, utilizará SQLite local monitoria.db)

# 4. Inicie o servidor em modo recarregamento automático (hot-reload)
uvicorn app.main:app --reload --port 8000
```

Acesse em: `http://localhost:8000` (documentação Swagger interativa em `http://localhost:8000/docs`).

---

## 📂 Estrutura do Projeto

```text
monitoria-python/
├── app/
│   ├── config.py             # Configurações do sistema via Pydantic Settings
│   ├── database.py           # Conexão SQLAlchemy com retry loop resiliente
│   ├── main.py               # Instância do FastAPI, middlewares e rotas
│   ├── seeds.py              # Carga inicial automática de dados essenciais
│   ├── models/               # Modelos relacionais SQLAlchemy
│   │   ├── activity.py       # Registro de atividades de monitoria
│   │   ├── department.py     # Departamentos do IME
│   │   ├── enrollment.py     # Inscrições de alunos
│   │   ├── evaluation.py     # Avaliações de docentes e monitores
│   │   ├── frequency.py      # Frequência mensal de bolsistas
│   │   ├── instructor.py     # Docentes e orientadores
│   │   ├── requisition.py    # Pedidos de monitoria
│   │   ├── school_class.py   # Turmas e disciplinas
│   │   ├── school_term.py    # Períodos letivos
│   │   ├── selection.py      # Seleção e classificação de monitores
│   │   └── user.py           # Usuários do sistema e permissões
│   ├── routers/              # Endpoints da aplicação (Controladores)
│   │   ├── auth.py           # Login, logout e callback Senha Única
│   │   ├── enrollments.py    # Inscrições
│   │   ├── requisitions.py   # Requisições
│   │   ├── school_classes.py # Turmas
│   │   └── school_terms.py   # Períodos letivos
│   ├── schemas/              # Schemas de validação Pydantic
│   ├── services/             # Integrações externas (OAuth USP, etc.)
│   ├── static/               # Arquivos estáticos (CSS, JS, imagens)
│   └── templates/            # Telas renderizadas via Jinja2 (HTML5/Bootstrap)
├── scripts/                  # Scripts de migração de dados e utilitários
├── docker-compose.yml        # Orquestração do app FastAPI + MariaDB
├── Dockerfile                # Imagem de produção Python 3.12
├── requirements.txt          # Dependências do ecossistema Python
└── .env.example              # Exemplo documentado de variáveis de ambiente
```

---

## 🔐 Integração com Senha Única USP (OAuth 1.0a)

A autenticação é realizada diretamente contra o provedor corporativo da USP:
1. **Requisição de Token**: O sistema gera a assinatura HMAC-SHA1 e solicita um token temporário.
2. **Autorização**: O usuário é redirecionado para a página oficial da Senha Única USP com o `callback_id` cadastrado.
3. **Troca do Access Token**: O `oauth_verifier` é processado em estrita conformidade com o **RFC 5849** (assinatura transmitida exclusivamente via cabeçalho HTTP `Authorization`).
4. **Obtenção dos Dados**: Recuperação de dados cadastrais do usuário (Número USP, nome, e-mail institucional e vínculos), criando ou atualizando a sessão do usuário automaticamente.
5. **Nível de Acesso**: Os usuários listados na variável `SENHAUNICA_ADMINS` recebem perfil administrativo imediatamente após o login.

---

## 📄 Licença

Desenvolvido para o **Instituto de Matemática e Estatística da Universidade de São Paulo (IME-USP)**.
