import streamlit as st
import re
import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import quote
import json
import time

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

def search_real_estate_google_legacy(endereco):
    """
    [LEGACY] Busca no Google por anúncios de imóveis, extrai preços, áreas e links.
    NÃO É MAIS UTILIZADA.

    """
    # Prepara a query de busca para o Google
    search_query = f'"{endereco}" venda de apartamento'
    encoded_query = quote(search_query)
    url = f"https://www.google.com.br/search?q={encoded_query}&num=10" # Pedir 10 resultados para ter margem

    st.write(f"Buscando no Google: *{search_query}*")

    # Headers para parecer um navegador normal
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    results = []

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Lança exceção se a requisição falhar

        soup = BeautifulSoup(response.text, 'html.parser')

        # DEBUG: Salva o HTML para análise
        try:
            with open("google_results.html", "w", encoding="utf-8") as f:
                f.write(soup.prettify())
            st.info("Arquivo de depuração 'google_results.html' foi salvo para análise.")
        except Exception as e:
            st.warning(f"Não foi possível salvar o arquivo de depuração: {e}")


        # Encontra todos os contêineres de resultados de busca
        # A estrutura do Google muda, esta é uma tentativa baseada em padrões comuns.
        search_results = soup.find_all('div', class_='g')
        if not search_results:
            # Tenta um seletor alternativo se o primeiro falhar
            search_results = soup.find_all('div', class_='tF2Cxc')

        if not search_results:
            st.warning("Não foi possível encontrar os contêineres de resultados na página do Google. A estrutura pode ter mudado.")
            return []

        # Padrões de preço e área (reutilizados)
        price_patterns = [
            r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
            r'R\$\s*(\d+\.?\d*)'
        ]
        area_patterns = [
            r'(\d+)\s*m²',
            r'(\d+)\s*metros quadrados'
        ]

        for result_div in search_results:
            title_element = result_div.find('h3')
            link_element = result_div.find('a')
            snippet_element = result_div.find('div', class_='VwiC3b') # Classe comum para snippets

            if title_element and link_element:
                title = title_element.get_text()
                link = link_element['href']
                snippet = snippet_element.get_text() if snippet_element else ""
                
                full_text = f"{title} {snippet}".lower()

                # Extrai preço
                price = None
                for pattern in price_patterns:
                    matches = re.findall(pattern, full_text)
                    if matches:
                        try:
                            price_str = matches[0].replace('.', '').replace(',', '.')
                            price_val = float(price_str)
                            if 10000 <= price_val <= 50000000: # Filtro de preço razoável
                                price = price_val
                                break
                        except:
                            continue
                
                # Se não encontrou preço, pula para o próximo resultado
                if price is None:
                    continue

                # Extrai área
                area = None
                for pattern in area_patterns:
                    matches = re.findall(pattern, full_text)
                    if matches:
                        try:
                            area = float(matches[0])
                            if 10 <= area <= 2000: # Filtro de área razoável
                                break
                        except:
                            continue

                results.append({
                    'title': title,
                    'link': link,
                    'price': price,
                    'area': area,
                    'price_per_m2': price / area if area and price else None
                })
        
        # Delay para evitar ser bloqueado
        time.sleep(1)

    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao acessar o Google: {e}")
        st.warning("O Google pode ter bloqueado a requisição. Tente novamente mais tarde.")
        return []
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado durante a busca: {e}")
        return []

    # Remove duplicatas e filtra os 5 melhores resultados com preço
    unique_results = []
    seen_links = set()
    for r in results:
        if r['link'] not in seen_links:
            unique_results.append(r)
            seen_links.add(r['link'])

    final_results = unique_results[:5]

    if final_results:
        st.markdown("### Anúncios Similares Encontrados")
        
        cols = st.columns(min(len(final_results), 5))
        
        prices = []
        areas = []
        prices_per_m2 = []
        
        for idx, (result, col) in enumerate(zip(final_results, cols)):
            with col:
                st.markdown(f"**Anúncio {idx+1}**")
                # Exibe o título como um link clicável
                st.markdown(f"[{result['title']}]({result['link']})")
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
        if prices:
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
        st.warning("Não foram encontrados anúncios com preços nos resultados do Google. Tente um endereço mais específico ou verifique a busca.")
        return []

# Configuração da página

st.set_page_config(page_title="Simulador de Arremate de Imóvel em Leilão", layout="centered")

st.markdown("""
    <style>
        .stTextInput > label {

            padding: 5px 10px;
        }
        .result-value {
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Simulador de Arremate de Imóvel em Leilão")

def prepare_address(endereco):
    # Remove caracteres especiais e palavras comuns que podem atrapalhar a busca
    endereco = endereco.lower()
    endereco = endereco.replace('rua', '').replace('avenida', '').replace('av.', '')
    endereco = endereco.replace('número', '').replace('n°', '').replace('nº', '')
    # Remove espaços extras
    endereco = ' '.join(endereco.split())
    return endereco

def search_real_estate(endereco):
    """Busca preços de imóveis semelhantes usando a SerpApi (Google).

    Para cada portal (Zap, VivaReal, Imovelweb, OLX) executa uma busca
    `site:<portal> "<endereço>" venda apartamento` e extrai o primeiro
    preço que aparecer no título ou snippet.   
    Retorna uma lista de preços (float) únicos e também exibe um resumo
    no Streamlit.
    """

    # ------------------------------------------------------------------
    # Configurações iniciais
    # ------------------------------------------------------------------
    api_key = os.getenv("SERPAPI_KEY", "4d35af028f15b5832f7a07975c1818cbf39adc858aed394c72a83a2dea86c6c5")
    if not api_key:
        st.error("Chave SerpApi não configurada")
        return []

    search_address = prepare_address(endereco)
    sites = [
        "zapimoveis.com.br",
        "vivareal.com.br",
        "imovelweb.com.br",
        "olx.com.br",
    ]
    price_regex = re.compile(r"r\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)", re.IGNORECASE)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    resultados = []  # [{'price': float, 'site': str, 'title': str, 'link': str}]

    for site in sites:
        st.write(f"🔍 Buscando em {site} …")
        params = {
            "engine": "google",
            "q": f'site:{site} "{search_address}" venda apartamento',
            "hl": "pt-BR",
            "num": 10,
            "api_key": api_key,
        }
        try:
            resp = requests.get("https://serpapi.com/search.json", params=params, timeout=20, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.warning(f"⚠️ Erro na SerpApi para {site}: {e}")
            continue

        for item in data.get("organic_results", []):
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            texto = f"{title} {snippet}"
            m = price_regex.search(texto)
            if m:
                try:
                    preco = float(m.group(1).replace(".", "").replace(",", "."))
                    if 10000 <= preco <= 50000000:  # filtro
                        resultados.append({"price": preco, "site": site, "title": title, "link": link})
                        break  # pega apenas primeiro preço por portal
                except ValueError:
                    continue
        time.sleep(1)  # pequeno delay

    # ------------------------------------------------------------------
    # Pós-processamento e exibição
    # ------------------------------------------------------------------
    if not resultados:
        st.warning("Não foram encontrados preços de imóveis similares. Tente um endereço mais específico ou confirme se a SerpApi possui créditos.")
        return []

    # remover duplicados
    precos_unicos = {round(r["price"]): r["price"] for r in resultados}.values()

    st.markdown("### Preços coletados")
    for r in resultados:
        st.write(f"{r['site']}: R$ {r['price']:,.0f} — [{r['title']}]({r['link']})")

    return list(precos_unicos)

    # ------------------------------------------------------------------
    # 1. Consulta SerpApi (Google) e extrai preços do JSON
    # ------------------------------------------------------------------
    search_address = prepare_address(endereco)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    sites = ['zapimoveis.com.br', 'vivareal.com.br', 'imovelweb.com.br', 'olx.com.br']
    price_regex = re.compile(r'r\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', re.IGNORECASE)

    resultados = []  # lista de dicts

    for site in sites:
        st.write(f"Buscando em {site} via SerpApi …")
        params = {
            'engine': 'google',
            'q': f'site:{site} "{search_address}" venda apartamento',
            'hl': 'pt-BR',
            'num': 10,
            'api_key': api_key
        }
        url = 'https://serpapi.com/search.json'
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            st.warning(f"SerpApi falhou para {site}: {e}")
            continue

        results = data.get('organic_results', [])
        if not results:
            continue


        if not hits:
            hits = []  # mantém compatível abaixo
        

            link_tag = hit.find('a', class_='result__a')
            snippet_tag = hit.find('a', class_='result__snippet')
            if not link_tag:
                continue
            titulo = link_tag.get_text(" ", strip=True)
            link = link_tag.get('href')
            snippet = snippet_tag.get_text(" ", strip=True) if snippet_tag else ''
            texto_completo = f"{titulo} {snippet}".lower()

            # 1ª tentativa: preço no snippet
            preco = None
            m = price_regex.search(texto_completo)
            if m:
                try:
                    preco = float(m.group(1).replace('.', '').replace(',', '.'))
                except ValueError:
                    preco = None

            # 2ª tentativa: visitar a página, caso ainda não tenha preço
            if preco is None:
                try:
                    page = requests.get(link, headers=headers, timeout=10)
                    # alguns portais bloqueiam; pulamos se status != 200
                    if page.status_code == 200 and 'text/html' in page.headers.get('Content-Type', ''):
                        texto_html = page.text.lower()
                        m2 = price_regex.search(texto_html)
                        if m2:
                            preco = float(m2.group(1).replace('.', '').replace(',', '.'))
                except Exception:
                    pass  # ignora erro de conexão / timeout
                time.sleep(1)  # pequena pausa para não sobrecarregar

            if preco and 10000 <= preco <= 50000000:
                resultados.append({'price': preco, 'link': link, 'title': titulo, 'site': site})




        # ------------------------------------------------------------------
        if not any(r['site'] == site for r in resultados):
            google_url = f"https://www.google.com/search?q=" + quote(f'site:{site} "{search_address}" venda apartamento') + "&num=10&hl=pt-BR"
            try:
                g_resp = requests.get(google_url, headers=headers, timeout=10)
                if g_resp.status_code == 200:
                    texto_html = g_resp.text.lower()
                    for m in price_regex.finditer(texto_html):
                        try:
                            preco = float(m.group(1).replace('.', '').replace(',', '.'))
                            if 10000 <= preco <= 50000000:
                                resultados.append({'price': preco, 'link': google_url, 'title': 'Google snippet', 'site': site})
                        except ValueError:
                            continue
            except Exception as e:
                st.warning(f"Google fallback falhou para {site}: {e}")

    # ------------------------------------------------------------------
    # 2. Pós-processamento dos resultados
    # ------------------------------------------------------------------
    if not resultados:
        return []

    # remove preços duplicados (variação centavos irrelevante -> arredonda)
    precos_unicos = {}
    for r in resultados:
        chave = round(r['price'])
        if chave not in precos_unicos:
            precos_unicos[chave] = r['price']

    return list(precos_unicos.values())

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
            encoded_query = quote(search_query)
            url = f"https://duckduckgo.com/?q={encoded_query}&format=json&no_html=1&no_redirect=1"

            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    text = response.text
                    price_patterns = [
                        r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
                        r'R\$\s*(\d+\.?\d*)'
                    ]
                    area_patterns = [
                        r'(\d+)\s*m²',
                        r'(\d+)\s*metros quadrados',
                        r'área\s*(?:total|privativa|útil)?\s*(?:de)?\s*(\d+)\s*m²'
                    ]
                    for pattern in price_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            try:
                                price_str = match.replace('.', '').replace(',', '.')
                                price = float(price_str)
                                if 100000 <= price <= 10000000:
                                    area = None
                                    for area_pattern in area_patterns:
                                        area_matches = re.findall(area_pattern, text, re.IGNORECASE)
                                        if area_matches:
                                            try:
                                                area = float(area_matches[0])
                                                if 20 <= area <= 1000:
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
            

            time.sleep(1)
    
    except Exception as e:
        st.error(f"Erro durante a busca: {str(e)}")
        return []
    
    unique_results = []
    seen_prices = set()
    for r in results:
        if r['price'] not in seen_prices:
            unique_results.append(r)
            seen_prices.add(r['price'])
    final_results = unique_results[:5]
    
    if final_results:
        st.markdown("### Anúncios Similares Encontrados")
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