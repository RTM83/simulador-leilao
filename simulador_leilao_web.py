import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

def format_number(value):
    """Formata número com pontos a cada 3 dígitos durante digitação"""
    if not value:
        return ""
    try:
        # Remove pontos e vírgulas existentes
        clean_value = value.replace(".", "").replace(",", "")
        # Converte para número
        number = int(clean_value)
        # Formata com pontos manualmente
        str_number = str(number)
        parts = []
        for i in range(len(str_number) - 1, -1, -3):
            start = max(0, i - 2)
            parts.append(str_number[start:i + 1])
        return ".".join(reversed(parts))
    except:
        return value

def parse_number(value):
    """Converte string formatada para número"""
    if not value:
        return 0.0
    return float(value.replace(".", "").replace(",", "."))

def extract_prices_from_search(search_results):
    """Extrai preços dos resultados da busca"""
    prices = []
    for result in search_results:
        # Procura por padrões de preço nos snippets
        snippet = result.get('snippet', '').lower()
        title = result.get('title', '').lower()
        link = result.get('link', '').lower()
        full_text = f"{title} {snippet} {link}"
        
        # Procura por padrões de preço (R$ XXX.XXX,XX ou R$ X.XXX.XXX)
        price_patterns = [
            r'r\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'r\$\s*(\d+\.?\d*)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, full_text)
            for match in matches:
                try:
                    # Remove pontos e vírgulas e converte para float
                    price = float(match.replace(".", "").replace(",", "."))
                    if 100000 <= price <= 10000000:  # Filtra preços improváveis
                        prices.append(price)
                except:
                    continue
    
    return sorted(list(set(prices)))  # Remove duplicatas e ordena

def prepare_address(endereco):
    # Remove caracteres especiais e palavras comuns que podem atrapalhar a busca
    endereco = endereco.lower()
    endereco = endereco.replace('rua', '').replace('avenida', '').replace('av.', '')
    endereco = endereco.replace('número', '').replace('n°', '').replace('nº', '')
    # Remove espaços extras
    endereco = ' '.join(endereco.split())
    return endereco

def search_real_estate(endereco):
    import urllib.parse
    import json
    
    # Prepara o endereço para busca
    search_address = prepare_address(endereco)
    
    # Headers para parecer um navegador normal
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # Lista para armazenar os resultados
    results = []
    
    try:
        # Usa a API do DuckDuckGo para buscar
        sites = ['zapimoveis.com.br', 'vivareal.com.br', 'imovelweb.com.br']
        
        for site in sites:
            st.write(f"Buscando em {site}...")
            
            # Monta a URL de busca
            search_query = f"site:{site} {search_address}"
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://duckduckgo.com/?q={encoded_query}&format=json&no_html=1&no_redirect=1"
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    # Procura por padrões de preço no texto retornado
                    text = response.text
                    
                    # Padrões de preço
                    price_patterns = [
                        r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                        r'R\$\s*(\d+\.?\d*)'
                    ]
                    
                    # Padrões de área
                    area_patterns = [
                        r'(\d+)\s*m²',
                        r'(\d+)\s*metros quadrados',
                        r'área\s*(?:total|privativa|útil)?\s*(?:de)?\s*(\d+)\s*m²'
                    ]
                    
                    # Extrai preços
                    for pattern in price_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            try:
                                price_str = match.replace('.', '').replace(',', '.')
                                price = float(price_str)
                                
                                if 100000 <= price <= 10000000:  # Filtra valores improváveis
                                    # Procura por área próxima ao preço
                                    area = None
                                    for area_pattern in area_patterns:
                                        area_matches = re.findall(area_pattern, text, re.IGNORECASE)
                                        if area_matches:
                                            try:
                                                area = float(area_matches[0])
                                                if 20 <= area <= 1000:  # Filtra áreas improváveis
                                                    break
                                            except:
                                                continue
                                    
                                    results.append({
                                        'price': price,
                                        'area': area,
                                        'price_per_m2': price/area if area else None,
                                        'site': site
                                    })
                            except:
                                continue
                
                else:
                    st.warning(f"Não foi possível acessar resultados de {site}")
                
            except Exception as e:
                st.warning(f"Erro ao buscar em {site}: {str(e)}")
                continue
            
            # Pequeno delay entre requisições
            import time
            time.sleep(1)
    
    except Exception as e:
        st.error(f"Erro durante a busca: {str(e)}")
        return []
    
    # Remove duplicatas baseado no preço
    unique_results = []
    seen_prices = set()
    
    for r in results:
        if r['price'] not in seen_prices:
            unique_results.append(r)
            seen_prices.add(r['price'])
    
    # Pega os 5 resultados mais relevantes
    final_results = unique_results[:5]
    
    if final_results:
        st.markdown("### Anúncios Similares Encontrados")
        
        # Mostra cada anúncio em colunas
        cols = st.columns(min(len(final_results), 5))
        
        prices = []
        areas = []
        prices_per_m2 = []
        
        for idx, (result, col) in enumerate(zip(final_results, cols)):
            with col:
                st.markdown(f"**Anúncio {idx+1}**")
                st.markdown(f"Fonte: {result['site']}")
                st.markdown(f"Preço: R$ {result['price']:,.2f}")
                if result['area']:
                    st.markdown(f"Área: {result['area']:.0f} m²")
                if result['price_per_m2']:
                    st.markdown(f"R$/m²: {result['price_per_m2']:,.2f}")
                
                prices.append(result['price'])
                if result['area']:
                    areas.append(result['area'])
                if result['price_per_m2']:
                    prices_per_m2.append(result['price_per_m2'])
        
        # Mostra médias
        st.markdown("### Médias Calculadas")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_price = sum(prices) / len(prices)
            st.metric("Preço Médio", f"R$ {avg_price:,.2f}")
        
        with col2:
            if areas:
                avg_area = sum(areas) / len(areas)
                st.metric("Área Média", f"{avg_area:.0f} m²")
        
        with col3:
            if prices_per_m2:
                avg_price_per_m2 = sum(prices_per_m2) / len(prices_per_m2)
                st.metric("R$/m² Médio", f"R$ {avg_price_per_m2:,.2f}")
        
        return prices
    else:
        st.warning("Não foram encontrados anúncios similares. Tente um endereço mais específico.")
        return []

# Configuração da página
st.set_page_config(page_title="Simulador de Arremate de Imóvel em Leilão", layout="centered")

# Título
st.title("Simulador de Arremate de Imóvel em Leilão")

# Cálculos
valor_arremate = valor_lance * (1 + agio/100)
custo_total_reforma = area * custo_reforma
custo_assessoria = 5000 if assessoria else 0
custo_condominio = condominio * prazo_venda
custo_iptu = iptu * prazo_venda
custo_total = valor_arremate + custo_total_reforma + custo_assessoria + custo_condominio + custo_iptu
comissao_valor = valor_mercado * (comissao/100)
resultado = valor_mercado - comissao_valor - custo_total

# Resultados
st.markdown("### Resultados")

# Primeira linha de resultados
col5, col6, col7 = st.columns(3)

with col5:
    st.metric("Valor do arremate", f"R$ {format_number(valor_arremate)}")
    st.metric("Custo da reforma", f"R$ {format_number(custo_total_reforma)}")
    
with col6:
    st.metric("Assessoria jurídica", f"R$ {format_number(custo_assessoria)}")
    st.metric("Condomínio total", f"R$ {format_number(custo_condominio)}")
    
with col7:
    st.metric("IPTU total", f"R$ {format_number(custo_iptu)}")
    st.metric("Comissão de venda", f"R$ {format_number(comissao_valor)}")

# Segunda linha de resultados
col8, col9, col10 = st.columns(3)

with col8:
    st.metric("Custo total", f"R$ {format_number(custo_total)}")
    
with col9:
    st.metric("Valor de venda", f"R$ {format_number(valor_mercado)}")
    
with col10:
    st.metric("Resultado", f"R$ {format_number(resultado)}")

# Cálculo de rentabilidade
rentabilidade = (resultado / custo_total) * 100
rentabilidade_mensal = ((1 + rentabilidade/100) ** (1/prazo_venda) - 1) * 100

st.markdown("### Análise de Rentabilidade")
col11, col12 = st.columns(2)

with col11:
    st.metric("Rentabilidade total", f"{rentabilidade:.1f}%")
    
with col12:
    st.metric("Rentabilidade mensal", f"{rentabilidade_mensal:.2f}%")

# Configuração para reduzir o espaçamento e melhorar formatação
st.markdown("""
    <style>
        .stTextInput > label {
            font-size: 14px;
            margin-bottom: 0px;
        }
        .stNumberInput > label {
            font-size: 14px;
            margin-bottom: 0px;
        }
        .stForm > label {
            margin-bottom: 0px;
        }
        div[data-testid="stForm"] {
            padding-top: 0px;
        }
        .section-title {
            text-decoration: underline;
            font-weight: bold;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        .result-table {
            font-family: monospace;
            font-size: 14px;
        }
        .result-table th, .result-table td {
            text-align: right;
            padding: 5px 10px;
        }
        .result-value {
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

with st.form("simulador_form"):
    # Seção de Endereço
    st.markdown("### Endereço do Imóvel")
    endereco = st.text_input("Endereço completo", placeholder="Ex: Rua Example, 123, Bairro, Cidade - Estado")
    col_busca1, col_busca2 = st.columns([3, 1])
    with col_busca1:
        analisar_ofertas = st.checkbox("Analisar ofertas similares neste endereço", value=False)
    
    st.markdown("### Valores e Características")
    col1, col2 = st.columns(2)
    
    with col1:
        valor_lance_str = st.text_input("Valor do lance inicial (R$)", value="500.000", key="lance")
        valor_lance = parse_number(valor_lance_str)
        
        valor_mercado_str = st.text_input("Valor do imóvel no mercado (R$)", value="1.000.000", key="mercado")
        valor_mercado = parse_number(valor_mercado_str)
        
        area_m2_str = st.text_input("Área do imóvel (m²)", value="100", key="area")
        area_m2 = parse_number(area_m2_str)
        
        custo_reforma_m2_str = st.text_input("Custo de reforma por m² (R$)", value="1.000", key="reforma")
        custo_reforma_m2 = parse_number(custo_reforma_m2_str)

    with col2:
        iptu_mensal_str = st.text_input("IPTU mensal (R$)", value="100", key="iptu")
        iptu_mensal = parse_number(iptu_mensal_str)
        
        condominio_mensal_str = st.text_input("Condomínio mensal (R$)", value="1.500", key="condominio")
        condominio_mensal = parse_number(condominio_mensal_str)
        
        prazo_venda_meses = st.number_input("Prazo até a venda (meses)", min_value=1, step=1, value=12)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("##### Assessoria Jurídica")
        incluir_assessoria = st.checkbox("Incluir Assessoria Jurídica?", value=True)
        if incluir_assessoria:
            assessoria_percent = st.number_input("Percentual da assessoria (%)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f", value=6.0)
        else:
            assessoria_percent = 0.0

    with col4:
        st.markdown("##### Comissão de Venda")
        incluir_comissao_venda = st.checkbox("Incluir Comissão de Venda?", value=False)
        if incluir_comissao_venda:
            comissao_venda_percent = st.number_input("Percentual da comissão (%)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f", value=3.0)
        else:
            comissao_venda_percent = 0.0

    submitted = st.form_submit_button("Simular")

if submitted:
    # Se marcou para analisar ofertas, faz a busca
    if analisar_ofertas and endereco:
        st.markdown("### Análise de Ofertas Similares")
        with st.spinner('Buscando ofertas similares...'):
            try:
                st.write("Iniciando busca de preços...")  # Debug: indica início da busca
                prices = search_real_estate(endereco)
                
                if prices:
                    avg_price = sum(prices) / len(prices)
                    st.markdown("#### Preços encontrados na região:")
                    
                    # Mostra até 5 preços em colunas
                    price_cols = st.columns(min(5, len(prices)))
                    for i, price in enumerate(prices[:5]):
                        with price_cols[i]:
                            st.markdown(f"**R$ {price:,.2f}**")
                    
                    st.markdown(f"**Média dos preços:** R$ {avg_price:,.2f}")
                    st.markdown(f"**Total de preços encontrados:** {len(prices)}")
                    
                    if valor_mercado > 0:
                        diff_percent = ((valor_mercado - avg_price) / avg_price) * 100
                        st.markdown(f"**Diferença para valor estimado:** {diff_percent:+.1f}%")
                else:
                    st.warning("Não foram encontrados preços de imóveis similares. Tente fornecer um endereço mais específico.")
            except Exception as e:
                st.error(f"Erro ao buscar ofertas similares: {str(e)}")
                st.write("Detalhes do erro para debug:", str(e))  # Debug: mostra detalhes do erro

    # Parâmetros fixos
    irpf_percent = 15.0
    itbi_percent = 3.0
    registro_percent = 1.0
    comissao_leiloeiro_percent = 5.0

    # Primeiro, mostrar os resultados detalhados para o lance inicial (ágio 0%)
    agio_percent = 0.0
    valor_arremate = valor_lance * (1 + agio_percent / 100)
    ganho_capital = max(valor_mercado - valor_arremate, 0)
    irpf = ganho_capital * (irpf_percent / 100)
    itbi = valor_arremate * (itbi_percent / 100)
    registro = valor_arremate * (registro_percent / 100)
    total_tributos = irpf + itbi + registro

    comissao_leiloeiro = valor_arremate * (comissao_leiloeiro_percent / 100)
    assessoria = valor_arremate * (assessoria_percent / 100)
    total_leiloeiro_assessoria = comissao_leiloeiro + assessoria

    custo_reforma = area_m2 * custo_reforma_m2
    outros_custos = 0.0
    total_reforma = custo_reforma + outros_custos

    total_iptu = iptu_mensal * prazo_venda_meses
    total_condominio = condominio_mensal * prazo_venda_meses
    total_mensal = total_iptu + total_condominio

    comissao_venda = valor_mercado * (comissao_venda_percent / 100)

    total_outros_custos = total_tributos + total_leiloeiro_assessoria + total_reforma + total_mensal + comissao_venda
    total_investido = valor_arremate + total_outros_custos
    resultado = valor_mercado - total_investido
    percentual = (resultado / total_investido) * 100 if total_investido > 0 else 0
    rendimento_mensal = ((1 + percentual / 100) ** (1 / prazo_venda_meses) - 1) * 100 if prazo_venda_meses > 0 and percentual > -100 else 0

    # Exibição dos resultados em colunas para economizar espaço
    st.subheader("Resultados para o Lance Inicial")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="section-title">Valores Principais</p>', unsafe_allow_html=True)
        st.markdown(f"**Lance Inicial:** R$ {valor_lance:,.2f}")
        st.markdown(f"**Valor do Arremate:** R$ {valor_arremate:,.2f}")
        st.markdown(f"**Valor de Mercado:** R$ {valor_mercado:,.2f}")
        st.markdown(f"**Área:** {area_m2:.2f} m²")

        st.markdown('<p class="section-title">Tributos e Registro</p>', unsafe_allow_html=True)
        st.markdown(f"IRPF: R$ {irpf:,.2f}")
        st.markdown(f"ITBI: R$ {itbi:,.2f}")
        st.markdown(f"Registro: R$ {registro:,.2f}")
        st.markdown(f"**Total:** R$ {total_tributos:,.2f}")

    with col2:
        st.markdown('<p class="section-title">Custos e Comissões</p>', unsafe_allow_html=True)
        st.markdown(f"**Leiloeiro:** R$ {comissao_leiloeiro:,.2f}")
        if incluir_assessoria:
            st.markdown(f"**Assessoria:** R$ {assessoria:,.2f}")
        st.markdown(f"**Reforma:** R$ {custo_reforma:,.2f}")
        
        st.markdown('<p class="section-title">Custos Mensais</p>', unsafe_allow_html=True)
        st.markdown(f"IPTU: R$ {total_iptu:,.2f}")
        st.markdown(f"Condomínio: R$ {total_condominio:,.2f}")
        
        if incluir_comissao_venda:
            st.markdown(f"**Comissão Venda:** R$ {comissao_venda:,.2f}")

    # Resumo final em destaque
    st.markdown("---")
    st.subheader("Resumo Final do Lance Inicial")
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown(f"**Total Custos:** R$ {total_outros_custos:,.2f}")
        st.markdown(f"**Total Investido:** R$ {total_investido:,.2f}")
    
    with col4:
        st.markdown(f"**Resultado:** R$ {resultado:,.2f}")
        st.markdown(f"**Retorno:** {percentual:.1f}%")
        st.markdown(f"**Rendimento Mensal:** {rendimento_mensal:.2f}%")

    # Agora, mostrar a tabela de simulações com diferentes percentuais de ágio
    st.markdown("---")
    st.subheader("Simulações com Diferentes Percentuais de Ágio")
    
    # Estilo da tabela com fonte monoespaçada para alinhamento uniforme
    st.markdown('<div class="result-table">', unsafe_allow_html=True)
    st.markdown("""
    | Ágio % | Valor Final | Resultado | Retorno % | Rend. Mensal % |
    |---------|------------|-----------|-----------|----------------|""")

    # Lista de percentuais de ágio para simular
    agios_percent = [10, 20, 30, 40, 50, 60, 70, 80]
    
    # Calcular resultados para cada percentual de ágio
    for agio_percent in agios_percent:
        # Cálculos
        valor_arremate = valor_lance * (1 + agio_percent / 100)
        ganho_capital = max(valor_mercado - valor_arremate, 0)
        irpf = ganho_capital * (irpf_percent / 100)
        itbi = valor_arremate * (itbi_percent / 100)
        registro = valor_arremate * (registro_percent / 100)
        total_tributos = irpf + itbi + registro

        comissao_leiloeiro = valor_arremate * (comissao_leiloeiro_percent / 100)
        assessoria = valor_arremate * (assessoria_percent / 100)
        total_leiloeiro_assessoria = comissao_leiloeiro + assessoria

        custo_reforma = area_m2 * custo_reforma_m2
        outros_custos = 0.0
        total_reforma = custo_reforma + outros_custos

        total_iptu = iptu_mensal * prazo_venda_meses
        total_condominio = condominio_mensal * prazo_venda_meses
        total_mensal = total_iptu + total_condominio

        comissao_venda = valor_mercado * (comissao_venda_percent / 100)

        total_outros_custos = total_tributos + total_leiloeiro_assessoria + total_reforma + total_mensal + comissao_venda
        total_investido = valor_arremate + total_outros_custos
        resultado = valor_mercado - total_investido
        percentual = (resultado / total_investido) * 100 if total_investido > 0 else 0
        rendimento_mensal = ((1 + percentual / 100) ** (1 / prazo_venda_meses) - 1) * 100 if prazo_venda_meses > 0 and percentual > -100 else 0

        # Exibir linha da tabela com formatação uniforme
        st.markdown(f"| {agio_percent:>3} | {valor_arremate:>11,.0f} | **{resultado:>9,.0f}** | {percentual:>8.1f} | {rendimento_mensal:>13.2f} |")
    
    st.markdown('</div>', unsafe_allow_html=True) 