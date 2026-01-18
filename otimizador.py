"""
otimizador.py - Funções de otimização de rotas agrícolas
Versão: 1.0
Autor: Sistema de Otimização de Rotas

Este módulo contém todas as funções necessárias para:
- Calcular distâncias entre pontos
- Otimizar rotas usando OR-Tools
- Obter rotas reais via OpenRouteService
- Gerar mapas interativos com Folium
"""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import folium
import math
import openrouteservice as ors


def distancia_euclidiana(a, b):
    """
    Calcula distância euclidiana entre dois pontos geográficos
    
    Args:
        a: Lista [longitude, latitude] do ponto A
        b: Lista [longitude, latitude] do ponto B
    
    Returns:
        int: Distância aproximada em metros
    
    Exemplo:
        >>> distancia_euclidiana([-53.45, -22.08], [-53.36, -22.26])
        20000  # aproximadamente 20km
    """
    return int(math.hypot(a[0] - b[0], a[1] - b[1]) * 1000)


def otimizar_rota(pontos_coordenadas):
    """
    Otimiza a sequência de visita aos pontos usando OR-Tools
    
    Este algoritmo resolve o problema do Caixeiro Viajante (TSP)
    encontrando a rota mais curta que visita todos os pontos.
    
    Args:
        pontos_coordenadas: Lista de coordenadas no formato [[lon1, lat1], [lon2, lat2], ...]
    
    Returns:
        tuple: (sequencia_otimizada, distancia_total)
            - sequencia_otimizada: Lista de índices na ordem otimizada
            - distancia_total: Distância total em quilômetros
    
    Raises:
        RuntimeError: Se não for possível encontrar uma solução
        ValueError: Se houver menos de 2 pontos
    
    Exemplo:
        >>> pontos = [[-53.45, -22.08], [-53.36, -22.26], [-46.30, -23.97]]
        >>> sequencia, distancia = otimizar_rota(pontos)
        >>> print(sequencia)
        [0, 1, 2, 0]  # Volta ao início
        >>> print(f"{distancia:.2f} km")
        850.45 km
    """
    if len(pontos_coordenadas) < 2:
        raise ValueError("São necessários pelo menos 2 pontos para otimizar")
    
    # Criar matriz de distâncias
    size = len(pontos_coordenadas)
    dist_matrix = [
        [distancia_euclidiana(pontos_coordenadas[i], pontos_coordenadas[j]) 
         for j in range(size)] 
        for i in range(size)
    ]
    
    # Configurar gerenciador de índices OR-Tools
    # Parâmetros: número de nós, número de veículos, ponto de partida
    manager = pywrapcp.RoutingIndexManager(len(dist_matrix), 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    
    # Callback de distância
    def distance_callback(from_index, to_index):
        """Retorna a distância entre dois nós"""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]
    
    # Registrar callback
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Configurar parâmetros de busca
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    # Adicionar limite de tempo para evitar travamentos
    search_parameters.time_limit.seconds = 30
    
    # Resolver o problema
    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        raise RuntimeError("Não foi possível encontrar uma solução otimizada")
    
    # Extrair sequência da solução
    index = routing.Start(0)
    sequencia_otimizada = []
    
    while not routing.IsEnd(index):
        sequencia_otimizada.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    sequencia_otimizada.append(manager.IndexToNode(index))
    
    # Calcular distância total em quilômetros
    distancia_total = solution.ObjectiveValue() / 1000
    
    return sequencia_otimizada, distancia_total


def obter_rota_real(api_key, pontos_otimizados, profile='driving-car'):
    """
    Obtém a rota real pelas estradas usando OpenRouteService
    
    Args:
        api_key: Chave da API OpenRouteService
        pontos_otimizados: Lista de coordenadas na ordem otimizada [[lon, lat], ...]
        profile: Tipo de veículo ('driving-car', 'driving-hgv', 'cycling-regular', etc.)
    
    Returns:
        dict: GeoJSON com a rota ou None em caso de erro
    
    Exemplo:
        >>> rota = obter_rota_real('sua_api_key', pontos_otimizados)
        >>> if rota:
        ...     distancia_real = rota['features'][0]['properties']['summary']['distance']
        ...     print(f"Distância real: {distancia_real/1000:.2f} km")
    """
    try:
        cliente = ors.Client(key=api_key)
        caminhos = cliente.directions(
            coordinates=pontos_otimizados,
            profile=profile,
            format='geojson',
            instructions=True,
            elevation=False
        )
        return caminhos
    except ors.exceptions.ApiError as e:
        print(f"Erro na API OpenRouteService: {e}")
        return None
    except Exception as e:
        print(f"Erro ao obter rota real: {e}")
        return None


def gerar_mapa(pontos_coordenadas, rotas_nomes, sequencia_otimizada, caminhos=None):
    """
    Gera mapa interativo com Folium mostrando a rota otimizada
    
    Args:
        pontos_coordenadas: Lista de coordenadas originais [[lon, lat], ...]
        rotas_nomes: Lista com nomes dos pontos
        sequencia_otimizada: Lista de índices na ordem otimizada
        caminhos: GeoJSON da rota real (opcional)
    
    Returns:
        folium.Map: Objeto mapa do Folium
    
    Exemplo:
        >>> mapa = gerar_mapa(pontos, nomes, sequencia, rota_real)
        >>> mapa.save('mapa_rota.html')
    """
    # Determinar centro do mapa (primeiro ponto da sequência)
    primeiro_idx = sequencia_otimizada[0]
    centro = list(reversed(pontos_coordenadas[primeiro_idx]))
    
    # Criar mapa base
    mapa = folium.Map(
        location=centro,
        zoom_start=6,
        control_scale=True,
        tiles='OpenStreetMap'
    )
    
    # Adicionar marcadores para cada ponto
    for i, idx in enumerate(sequencia_otimizada):
        # Converter coordenadas de [lon, lat] para [lat, lon]
        cordenadas = list(reversed(pontos_coordenadas[idx]))
        nome_ponto = rotas_nomes[idx]
        
        # Determinar cor do marcador baseado na ordem
        if i == 0:
            cor = 'green'  # Início
            icone = 'play'
        elif i == len(sequencia_otimizada) - 1:
            cor = 'red'  # Fim
            icone = 'stop'
        else:
            cor = 'blue'  # Pontos intermediários
            icone = 'info-sign'
        
        # Criar popup com informações
        popup_html = f"""
        <div style="font-family: Arial; min-width: 150px;">
            <h4 style="margin: 0; color: {cor};">Parada #{i + 1}</h4>
            <hr style="margin: 5px 0;">
            <b>{nome_ponto}</b><br>
            <small>Lat: {cordenadas[0]:.6f}<br>
            Lon: {cordenadas[1]:.6f}</small>
        </div>
        """
        
        # Adicionar marcador ao mapa
        folium.Marker(
            cordenadas,
            popup=folium.Popup(popup_html, max_width=200),
            tooltip=f"#{i + 1} - {nome_ponto}",
            icon=folium.Icon(icon=icone, color=cor, prefix='fa')
        ).add_to(mapa)
    
    # Adicionar rota ao mapa
    if caminhos and 'features' in caminhos and len(caminhos['features']) > 0:
        # Usar rota real do OpenRouteService
        coords = caminhos['features'][0]['geometry']['coordinates']
        
        # Extrair informações da rota
        properties = caminhos['features'][0].get('properties', {})
        summary = properties.get('summary', {})
        distancia_m = summary.get('distance', 0)
        duracao_s = summary.get('duration', 0)
        
        # Criar tooltip com informações
        tooltip_text = f"Distância: {distancia_m/1000:.1f} km | Tempo: {duracao_s/3600:.1f}h"
        
        # Desenhar rota
        folium.PolyLine(
            locations=[[coord[1], coord[0]] for coord in coords],
            color='#2E86DE',
            weight=4,
            opacity=0.8,
            tooltip=tooltip_text
        ).add_to(mapa)
    else:
        # Usar linhas retas entre os pontos (fallback)
        pontos_rota = [list(reversed(pontos_coordenadas[i])) for i in sequencia_otimizada]
        folium.PolyLine(
            locations=pontos_rota,
            color='#EE5A6F',
            weight=3,
            opacity=0.6,
            dash_array='10',
            tooltip='Rota aproximada (linha reta)'
        ).add_to(mapa)
    
    # Adicionar camadas de mapa adicionais
    folium.TileLayer('cartodbpositron', name='Mapa Claro').add_to(mapa)
    folium.TileLayer('cartodbdark_matter', name='Mapa Escuro').add_to(mapa)
    
    # Adicionar controles
    folium.LayerControl().add_to(mapa)
    folium.LatLngPopup().add_to(mapa)
    
    # Adicionar medidor de escala
    from folium import plugins
    plugins.MiniMap(toggle_display=True).add_to(mapa)
    plugins.Fullscreen().add_to(mapa)
    
    return mapa


def calcular_estatisticas_rota(pontos_coordenadas, sequencia_otimizada, caminhos=None):
    """
    Calcula estatísticas detalhadas da rota
    
    Args:
        pontos_coordenadas: Lista de coordenadas
        sequencia_otimizada: Sequência de índices
        caminhos: GeoJSON da rota real (opcional)
    
    Returns:
        dict: Dicionário com estatísticas da rota
    """
    stats = {
        'num_pontos': len(pontos_coordenadas),
        'num_paradas': len(sequencia_otimizada),
    }
    
    if caminhos and 'features' in caminhos:
        properties = caminhos['features'][0].get('properties', {})
        summary = properties.get('summary', {})
        
        stats['distancia_km'] = summary.get('distance', 0) / 1000
        stats['tempo_horas'] = summary.get('duration', 0) / 3600
        stats['tempo_minutos'] = summary.get('duration', 0) / 60
    else:
        # Calcular distância euclidiana total
        distancia_total = 0
        for i in range(len(sequencia_otimizada) - 1):
            idx_atual = sequencia_otimizada[i]
            idx_proximo = sequencia_otimizada[i + 1]
            distancia_total += distancia_euclidiana(
                pontos_coordenadas[idx_atual],
                pontos_coordenadas[idx_proximo]
            )
        
        stats['distancia_km'] = distancia_total / 1000
        stats['tempo_horas'] = stats['distancia_km'] / 60  # Aproximação
        stats['tempo_minutos'] = stats['tempo_horas'] * 60
    
    return stats