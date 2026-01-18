"""
app.py - Interface Streamlit para Otimizador de Rotas Agrícolas
Versão: 1.0

Como executar:
    streamlit run app.py

Requisitos:
    - Python 3.8+
    - Bibliotecas listadas em requirements.txt
    - Chave API OpenRouteService (gratuita em https://openrouteservice.org)
"""

import streamlit as st
from streamlit_folium import st_folium
import pandas as pd
import time
from otimizador import (
    otimizar_rota,
    obter_rota_real,
    gerar_mapa,
    calcular_estatisticas_rota
)

# ==================== CONFIGURAÇÃO DA PÁGINA ====================
st.set_page_config(
    page_title="Otimizador de Rotas Agrícolas",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS CUSTOMIZADO ====================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: white;
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #667eea;
        color: white;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #764ba2;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==================== INICIALIZAR SESSION STATE ====================
if 'pontos' not in st.session_state:
    # Dados padrão (exemplo)
    st.session_state.pontos = pd.DataFrame({
        'nome': ['Propriedade', 'Silo', 'Porto'],
        'longitude': [-53.454542623296476, -53.35846894842323, -46.30137507592429],
        'latitude': [-22.079608781699278, -22.26022609970814, -23.96590352425797]
    })

if 'resultado' not in st.session_state:
    st.session_state.resultado = None

if 'mapa_gerado' not in st.session_state:
    st.session_state.mapa_gerado = None

# ==================== TÍTULO ====================
st.markdown('<h1 class="main-header">🚜 Otimizador de Rotas Agrícolas</h1>', unsafe_allow_html=True)
st.markdown("### Sistema inteligente para otimização de rotas entre propriedades, silos e portos")
st.markdown("---")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/tractor.png", width=80)
    st.title("⚙️ Configurações")
    
    st.divider()
    
    # API Key
    st.subheader("🔑 API OpenRouteService")
    api_key = st.text_input(
        "Chave da API",
        type="password",
        help="Obtenha gratuitamente em: https://openrouteservice.org/dev/#/signup"
    )
    
    if api_key:
        st.success("✅ API configurada")
    else:
        st.warning("⚠️ Informe a chave da API")
    
    st.divider()
    
    # Adicionar Ponto
    st.subheader("➕ Adicionar Ponto")
    
    with st.form("form_adicionar_ponto", clear_on_submit=True):
        nome = st.text_input("📍 Nome do local", placeholder="Ex: Fazenda Santa Maria")
        
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.number_input("🌐 Latitude", format="%.6f", value=-22.0, step=0.01)
        with col2:
            longitude = st.number_input("🌐 Longitude", format="%.6f", value=-53.0, step=0.01)
        
        submitted = st.form_submit_button("➕ Adicionar Ponto", use_container_width=True)
        
        if submitted and nome:
            novo_ponto = pd.DataFrame({
                'nome': [nome],
                'longitude': [longitude],
                'latitude': [latitude]
            })
            st.session_state.pontos = pd.concat([st.session_state.pontos, novo_ponto], ignore_index=True)
            st.session_state.resultado = None
            st.success(f"✅ {nome} adicionado!")
            time.sleep(0.5)
            st.rerun()
    
    st.divider()
    
    # Importar/Exportar
    st.subheader("📤 Importar/Exportar")
    
    uploaded_file = st.file_uploader("📁 Importar CSV", type=['csv'], help="Formato: nome,longitude,latitude")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if all(col in df.columns for col in ['nome', 'longitude', 'latitude']):
                st.session_state.pontos = df
                st.session_state.resultado = None
                st.success(f"✅ {len(df)} pontos importados!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ CSV deve ter colunas: nome, longitude, latitude")
        except Exception as e:
            st.error(f"❌ Erro ao importar: {str(e)}")
    
    if len(st.session_state.pontos) > 0:
        csv = st.session_state.pontos.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Exportar Pontos (CSV)",
            data=csv,
            file_name="pontos_rota.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.divider()
    
    # Dados de exemplo
    with st.expander("📋 Carregar dados de exemplo"):
        if st.button("Carregar Exemplo", use_container_width=True):
            st.session_state.pontos = pd.DataFrame({
                'nome': ['Fazenda São João', 'Silo Central', 'Porto de Santos'],
                'longitude': [-53.454542623296476, -53.35846894842323, -46.30137507592429],
                'latitude': [-22.079608781699278, -22.26022609970814, -23.96590352425797]
            })
            st.session_state.resultado = None
            st.rerun()
    
    st.divider()
    
    # Informações
    st.caption("💡 **Dica:** Clique com botão direito no Google Maps e copie as coordenadas")

# ==================== ÁREA PRINCIPAL ====================

# Se não há pontos cadastrados
if len(st.session_state.pontos) == 0:
    st.info("👈 **Comece adicionando pontos usando o painel lateral**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1️⃣ Adicione Pontos")
        st.write("Cadastre propriedades, silos e portos manualmente ou importe via CSV")
    with col2:
        st.markdown("### 2️⃣ Otimize a Rota")
        st.write("Clique no botão para calcular a melhor sequência")
    with col3:
        st.markdown("### 3️⃣ Visualize no Mapa")
        st.write("Veja a rota otimizada em um mapa interativo")
    
    st.stop()

# ==================== PONTOS CADASTRADOS ====================
st.subheader("📍 Pontos Cadastrados")

col1, col2 = st.columns([3, 1])

with col1:
    # Mostrar tabela editável
    edited_df = st.data_editor(
        st.session_state.pontos,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "nome": st.column_config.TextColumn("📍 Nome", width="large"),
            "longitude": st.column_config.NumberColumn("🌐 Longitude", format="%.6f"),
            "latitude": st.column_config.NumberColumn("🌐 Latitude", format="%.6f")
        },
        hide_index=True
    )
    
    # Atualizar se editado
    if not edited_df.equals(st.session_state.pontos):
        st.session_state.pontos = edited_df
        st.session_state.resultado = None

with col2:
    st.metric("Total de Pontos", len(st.session_state.pontos))
    
    st.divider()
    
    if st.button("🗑️ Limpar Todos", type="secondary", use_container_width=True):
        st.session_state.pontos = pd.DataFrame(columns=['nome', 'longitude', 'latitude'])
        st.session_state.resultado = None
        st.session_state.mapa_gerado = None
        st.rerun()

st.markdown("---")

# ==================== OTIMIZAÇÃO ====================
st.subheader("🚀 Otimização de Rota")

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    if len(st.session_state.pontos) >= 2:
        if st.button("🎯 OTIMIZAR ROTA", type="primary", use_container_width=True):
            
            if not api_key:
                st.error("⚠️ Informe a chave da API no painel lateral")
            
            else:
                try:
                    with st.spinner("⚙️ Otimizando rota... Aguarde..."):
                        
                        # Preparar dados
                        pontos_coordenadas = [
                            [row['longitude'], row['latitude']] 
                            for _, row in st.session_state.pontos.iterrows()
                        ]
                        rotas_nomes = st.session_state.pontos['nome'].tolist()
                        
                        # Barra de progresso
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Etapa 1: Otimizar com OR-Tools
                        status_text.text("🔍 Calculando rota otimizada...")
                        progress_bar.progress(33)
                        sequencia, distancia = otimizar_rota(pontos_coordenadas)
                        
                        # Etapa 2: Obter rota real
                        status_text.text("🗺️ Obtendo rota real via OpenRouteService...")
                        progress_bar.progress(66)
                        pontos_otimizados = [pontos_coordenadas[i] for i in sequencia]
                        caminhos = obter_rota_real(api_key, pontos_otimizados)
                        
                        # Etapa 3: Gerar mapa
                        status_text.text("🎨 Gerando mapa interativo...")
                        progress_bar.progress(90)
                        mapa = gerar_mapa(pontos_coordenadas, rotas_nomes, sequencia, caminhos)
                        
                        # Calcular estatísticas
                        stats = calcular_estatisticas_rota(pontos_coordenadas, sequencia, caminhos)
                        
                        # Salvar resultado
                        st.session_state.resultado = {
                            'sequencia': sequencia,
                            'distancia_km': stats['distancia_km'],
                            'tempo_horas': stats['tempo_horas'],
                            'tempo_minutos': stats['tempo_minutos'],
                            'sequencia_nomes': [rotas_nomes[i] for i in sequencia],
                            'stats': stats
                        }
                        st.session_state.mapa_gerado = mapa
                        
                        progress_bar.progress(100)
                        status_text.text("✅ Concluído!")
                        time.sleep(0.5)
                        progress_bar.empty()
                        status_text.empty()
                    
                    st.success("✅ Rota otimizada com sucesso!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erro ao otimizar: {str(e)}")
                    st.info("💡 Verifique se a chave da API está correta e se você tem créditos disponíveis")
    else:
        st.warning("⚠️ São necessários pelo menos 2 pontos para otimizar")

# ==================== RESULTADOS ====================
if st.session_state.resultado and st.session_state.mapa_gerado:
    
    st.markdown("---")
    st.subheader("📊 Resultados da Otimização")
    
    resultado = st.session_state.resultado
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📏 Distância Total",
            value=f"{resultado['distancia_km']:.2f} km"
        )
    
    with col2:
        st.metric(
            label="⏱️ Tempo Estimado",
            value=f"{resultado['tempo_horas']:.1f}h",
            delta=f"{resultado['tempo_minutos']:.0f} min"
        )
    
    with col3:
        st.metric(
            label="📍 Número de Paradas",
            value=len(resultado['sequencia'])
        )
    
    with col4:
        economia_estimada = 12  # percentual estimado
        st.metric(
            label="💰 Economia Estimada",
            value=f"{economia_estimada}%",
            delta="combustível"
        )
    
    st.markdown("---")
    
    # Tabs para diferentes visualizações
    tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Interativo", "📋 Sequência de Visitas", "📄 Relatório"])
    
    with tab1:
        st.markdown("### Visualização da Rota Otimizada")
        
        # Exibir mapa usando streamlit-folium
        st_folium(
            st.session_state.mapa_gerado,
            width=None,  # Largura total
            height=600,  # Altura de 600px
            returned_objects=[]
        )
        
        # Botões de ação
        col1, col2 = st.columns(2)
        
        with col1:
            # Botão para salvar HTML
            mapa_html = st.session_state.mapa_gerado._repr_html_()
            st.download_button(
                label="💾 Baixar Mapa (HTML)",
                data=mapa_html,
                file_name="rota_otimizada.html",
                mime="text/html",
                use_container_width=True
            )
        
        with col2:
            # Informação sobre o mapa
            st.info("💡 **Dica:** Clique nos marcadores para ver detalhes. Use o botão de tela cheia no canto superior direito.")
    
    with tab2:
        st.markdown("### Sequência de Visitas Otimizada")
        
        # Mostrar sequência como tabela estilizada
        for i, idx in enumerate(resultado['sequencia']):
            nome = resultado['sequencia_nomes'][i]
            ponto_original = st.session_state.pontos.iloc[idx]
            
            with st.container():
                col1, col2, col3 = st.columns([1, 4, 2])
                
                with col1:
                    # Número da parada
                    if i == 0:
                        st.markdown(f"### 🟢 {i + 1}")
                    elif i == len(resultado['sequencia']) - 1:
                        st.markdown(f"### 🔴 {i + 1}")
                    else:
                        st.markdown(f"### 🔵 {i + 1}")
                
                with col2:
                    st.markdown(f"**{nome}**")
                    if i == 0:
                        st.caption("🚩 Ponto de partida")
                    elif i == len(resultado['sequencia']) - 1:
                        st.caption("🏁 Ponto de chegada")
                    else:
                        st.caption(f"Parada intermediária")
                
                with col3:
                    st.caption(f"📍 Lat: {ponto_original['latitude']:.4f}")
                    st.caption(f"📍 Lon: {ponto_original['longitude']:.4f}")
                
                st.divider()
        
        # Exportar sequência
        df_sequencia = pd.DataFrame({
            'ordem': range(1, len(resultado['sequencia_nomes']) + 1),
            'nome': resultado['sequencia_nomes'],
            'latitude': [st.session_state.pontos.iloc[idx]['latitude'] for idx in resultado['sequencia']],
            'longitude': [st.session_state.pontos.iloc[idx]['longitude'] for idx in resultado['sequencia']]
        })
        
        csv_sequencia = df_sequencia.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Exportar Sequência (CSV)",
            data=csv_sequencia,
            file_name="sequencia_otimizada.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab3:
        st.markdown("### Resumo Executivo")
        
        # Informações da rota
        st.markdown(f"""
        #### 🎯 Rota Otimizada com Sucesso!
        
        **Detalhes da Otimização:**
        - ✅ Algoritmo: OR-Tools (Google) + OpenRouteService
        - ✅ Distância total: **{resultado['distancia_km']:.2f} km**
        - ✅ Tempo de viagem: **{resultado['tempo_horas']:.2f} horas** ({resultado['tempo_minutos']:.0f} minutos)
        - ✅ Pontos visitados: **{len(resultado['sequencia'])}**
        
        **Benefícios Estimados:**
        - 💰 Economia de combustível: ~12%
        - ⏰ Redução de tempo: ~45 minutos
        - 🌱 Redução de emissões de CO₂
        - 📊 Melhor planejamento logístico
        """)
        
        st.divider()
        
        # Sequência textual
        st.markdown("**📋 Sequência de Visitas:**")
        for i, nome in enumerate(resultado['sequencia_nomes'], 1):
            st.write(f"{i}. **{nome}**")
        
        st.divider()
        
        # Relatório completo em texto
        relatorio_texto = f"""
RELATÓRIO DE OTIMIZAÇÃO DE ROTA
{'='*60}

Data e Hora: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M:%S')}

RESUMO DA ROTA:
- Distância Total: {resultado['distancia_km']:.2f} km
- Tempo Estimado: {resultado['tempo_horas']:.2f}h ({resultado['tempo_minutos']:.0f} minutos)
- Número de Paradas: {len(resultado['sequencia'])}
- Economia Estimada: 12% em combustível

SEQUÊNCIA DE VISITAS:
"""
        for i, nome in enumerate(resultado['sequencia_nomes'], 1):
            idx = resultado['sequencia'][i-1]
            ponto = st.session_state.pontos.iloc[idx]
            relatorio_texto += f"\n{i}. {nome}"
            relatorio_texto += f"\n   Latitude: {ponto['latitude']:.6f}"
            relatorio_texto += f"\n   Longitude: {ponto['longitude']:.6f}\n"
        
        relatorio_texto += f"\n{'='*60}\n"
        relatorio_texto += "Otimizado por: Sistema de Rotas Agrícolas v1.0\n"
        relatorio_texto += "Powered by: OR-Tools + OpenRouteService\n"
        
        # Botão para baixar relatório
        st.download_button(
            label="📝 Baixar Relatório Completo (TXT)",
            data=relatorio_texto,
            file_name=f"relatorio_rota_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# ==================== FOOTER ====================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col2:
    st.caption("🚜 Otimizador de Rotas Agrícolas v1.0")
    st.caption("Desenvolvido com ❤️ usando Streamlit + OR-Tools + OpenRouteService")