# Simulador de Arremate de Imóvel em Leilão

Este é um simulador web desenvolvido com Streamlit para calcular custos e retornos em investimentos em leilões de imóveis.

## Funcionalidades

- Cálculo detalhado de custos e retornos
- Formatação automática de números com pontos
- Simulação com diferentes percentuais de ágio (10% a 80%)
- Opções para incluir assessoria jurídica e comissão de venda
- Interface limpa e organizada

## Como usar

1. Instale as dependências:
```
pip install streamlit
```

2. Execute o aplicativo:
```
streamlit run simulador_leilao_web.py
```

3. Acesse no navegador:
- Local: http://localhost:8501
- Rede: http://[seu-ip]:8501

## Valores Padrão

- Lance inicial: R$ 500.000
- Valor de mercado: R$ 1.000.000
- Área: 100 m²
- Custo reforma: R$ 1.000/m²
- IPTU: R$ 100/mês
- Condomínio: R$ 1.500/mês

## Publicando no Streamlit Cloud

1. Faça upload deste projeto para um repositório no GitHub.
2. Acesse [https://share.streamlit.io/](https://share.streamlit.io/).
3. Clique em "New app", selecione o repositório e informe o nome do arquivo principal: `simulador_leilao_web.py`.
4. Clique em Deploy.

## Entradas do simulador
- Valor do lance inicial
- Valor do imóvel no mercado
- Área do imóvel (m²)
- Custo de reforma por m²
- IPTU mensal
- Condomínio mensal
- Percentual de ágio sobre o lance (%)
- Comissão de venda no mercado (%)
- Prazo até a venda (meses)

## Saídas
- Todos os custos, taxas e resultado do investimento detalhados na tela. 