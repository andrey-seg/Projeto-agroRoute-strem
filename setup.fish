#!/usr/bin/env fish

# Ir para o projeto
cd ~/Documentos/projeto-agro-route-flet

# Remover venv antigo se existir
rm -rf venv

# Criar novo venv
echo "📦 Criando ambiente virtual..."
python3.12 -m venv venv

# Ativar venv (Fish)
echo "🔓 Ativando ambiente virtual..."
source venv/bin/activate.fish

# Verificar
echo "📍 Verificando Python:"
which python
python --version

# Atualizar pip
echo "⬆️ Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "📥 Instalando dependências..."
pip install streamlit
pip install streamlit-folium
pip install openrouteservice
pip install ortools
pip install folium
pip install pandas

# Verificar
echo "✅ Pacotes instalados:"
pip list | grep -E "streamlit|folium|ortools|openrouteservice"

# Testar
echo "🧪 Testando importações..."
python -c "from streamlit_folium import st_folium; print('✅ streamlit-folium OK')"

echo ""
echo "✅ Pronto! Execute:"
echo "  source venv/bin/activate.fish"
echo "  streamlit run app.py"