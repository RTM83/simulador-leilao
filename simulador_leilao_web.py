import streamlit as st
import re
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
            r'r\$\s*(\d+(?:\.\d{3})*)',
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

st.set_page_config(page_title="Simulador de Arremate de Imóvel em Leilão", layout="centered")

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

st.title("Simulador de Arremate de Imóvel em Leilão")

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
            # Prepara a busca
            search_query = f"{endereco} venda apartamento preço"
            
            # Faz a busca web usando a função correta
            try:
                results = st.web_search(
                    search_term=search_query,
                    explanation="Buscando preços de imóveis similares na região informada."
                )
                
                # Extrai e mostra os preços encontrados
                if results:
                    prices = extract_prices_from_search(results)
                    if prices:
                        st.markdown("#### Preços encontrados na região:")
                        price_cols = st.columns(min(5, len(prices)))
                        for i, price in enumerate(prices[:5]):  # Mostra até 5 preços
                            with price_cols[i]:
                                st.markdown(f"**R$ {price:,.2f}**")
                        
                        avg_price = sum(prices) / len(prices)
                        st.markdown(f"**Média dos preços:** R$ {avg_price:,.2f}")
                        
                        if valor_mercado > 0:
                            diff_percent = ((valor_mercado - avg_price) / avg_price) * 100
                            st.markdown(f"**Diferença para valor estimado:** {diff_percent:+.1f}%")
                    else:
                        st.warning("Não foram encontrados preços de imóveis similares.")
                else:
                    st.warning("Não foram encontrados resultados para este endereço.")
            except Exception as e:
                st.error(f"Erro ao buscar ofertas similares: {str(e)}")

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