############################################################
# 🚀 INSTALAR UV (caso ainda não tenha)
############################################################
curl -LsSf https://astral.sh/uv/install.sh | sh

# depois recarregue o terminal ou rode:
source ~/.bashrc
# ou
source ~/.zshrc



############################################################
# 📦 CRIAR UM NOVO PROJETO PYTHON MODERNO
############################################################
uv init meu_projeto
cd meu_projeto

# cria:
# - pyproject.toml (configuração moderna)
# - estrutura básica do projeto



############################################################
# 🐍 CRIAR AMBIENTE VIRTUAL (.venv)
############################################################
uv venv

# ativar ambiente:
source .venv/bin/activate      # Linux / Mac
# OU
.venv\Scripts\activate         # Windows



############################################################
# 📥 INSTALAR PACOTE (substitui pip install)
############################################################
uv add requests

# já:
# - instala pacote
# - atualiza pyproject.toml
# - cria lock automático



############################################################
# 📥 INSTALAR PACOTE COM VERSÃO
############################################################
uv add fastapi==0.115.0
uv add "pandas>=2.0"



############################################################
# 🧪 INSTALAR DEPENDÊNCIA DE DESENVOLVIMENTO
############################################################
uv add --dev pytest
uv add --dev ruff
uv add --dev black

# usado para:
# testes, lint, formatadores etc.



############################################################
# ❌ REMOVER PACOTE
############################################################
uv remove requests



############################################################
# 🔄 INSTALAR TODAS DEPENDÊNCIAS DO PROJETO
############################################################
uv sync

# equivalente a:
# pip install -r requirements.txt
# poetry install



############################################################
# ▶️ RODAR SCRIPT PYTHON SEM ATIVAR VENV
############################################################
uv run python main.py

# exemplo FastAPI:
uv run uvicorn app:app --reload



############################################################
# ⚡ EXECUTAR FERRAMENTA ISOLADA (tipo pipx)
############################################################
uvx ruff check .
uvx black .
uvx httpie https://google.com

# instala temporário e roda



############################################################
# 🐍 INSTALAR UMA VERSÃO DO PYTHON
############################################################
uv python install 3.12

# usar versão específica no venv:
uv venv --python 3.12



############################################################
# 🔎 LISTAR PACOTES INSTALADOS
############################################################
uv pip list



############################################################
# 🌳 VER ÁRVORE DE DEPENDÊNCIAS
############################################################
uv tree



############################################################
# 🔒 GERAR LOCKFILE (reprodutibilidade)
############################################################
uv lock

# cria uv.lock
# essencial para Docker/produção



############################################################
# 🔄 ATUALIZAR DEPENDÊNCIAS
############################################################
uv update



############################################################
# 🧹 RECRIAR AMBIENTE COMPLETO
############################################################
rm -rf .venv
uv sync



############################################################
# 💡 ALIAS ÚTIL (opcional)
############################################################
alias ur="uv run"

# depois basta:
ur python main.py
