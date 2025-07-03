import streamlit as st

st.set_page_config(page_title="Simulador de Arremate de Imóvel em Leilão", layout="centered")
st.title("Simulador de Arremate de Imóvel em Leilão")

with st.form("simulador_form"):
    valor_lance = st.number_input("Valor do lance inicial (R$)", min_value=0.0, step=1000.0, format="%.2f")
    valor_mercado = st.number_input("Valor do imóvel no mercado (R$)", min_value=0.0, step=1000.0, format="%.2f")
    area_m2 = st.number_input("Área do imóvel (m²)", min_value=0.0, step=1.0, format="%.2f")
    custo_reforma_m2 = st.number_input("Custo de reforma por m² (R$)", min_value=0.0, step=100.0, format="%.2f")
    iptu_mensal = st.number_input("IPTU mensal (R$)", min_value=0.0, step=10.0, format="%.2f")
    condominio_mensal = st.number_input("Condomínio mensal (R$)", min_value=0.0, step=50.0, format="%.2f")
    agio_percent = st.number_input("Percentual de ágio sobre o lance (%)", min_value=0.0, step=1.0, format="%.2f", value=20.0)
    comissao_venda_percent = st.number_input("Comissão de venda no mercado (%)", min_value=0.0, step=0.5, format="%.2f", value=0.0)
    prazo_venda_meses = st.number_input("Prazo até a venda (meses)", min_value=1, step=1, value=12)
    submitted = st.form_submit_button("Simular")

if submitted:
    # Parâmetros fixos
    irpf_percent = 15.0
    itbi_percent = 3.0
    registro_percent = 1.0
    comissao_leiloeiro_percent = 5.0
    assessoria_percent = 6.0

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

    st.subheader("Resumo da Simulação")
    st.markdown(f"**Valor do Lance Inicial:** R$ {valor_lance:,.2f}")
    st.markdown(f"**Percentual de ágio sobre o lance:** {agio_percent:.1f}%")
    st.markdown(f"**Valor do Arremate no Leilão:** R$ {valor_arremate:,.2f}")
    st.markdown(f"**Valor de Venda do Imóvel no Mercado:** R$ {valor_mercado:,.2f}")
    st.markdown(f"**Área do imóvel:** {area_m2:.2f} m²")

    st.markdown("---")
    st.markdown("### Custos e taxas envolvidas:")
    st.markdown("**Tributos e Registro:**")
    st.markdown(f"- Ganho de Capital (IRPF): R$ {irpf:,.2f} ({irpf_percent:.0f}%)")
    st.markdown(f"- ITBI: R$ {itbi:,.2f} ({itbi_percent:.0f}%)")
    st.markdown(f"- Registro: R$ {registro:,.2f} ({registro_percent:.0f}%)")
    st.markdown(f"- **Total:** R$ {total_tributos:,.2f}")

    st.markdown("**Leiloeiro e Assessoria Jurídica:**")
    st.markdown(f"- Comissão do Leiloeiro: R$ {comissao_leiloeiro:,.2f} ({comissao_leiloeiro_percent:.0f}%)")
    st.markdown(f"- Assessoria Jurídica: R$ {assessoria:,.2f} ({assessoria_percent:.0f}%)")
    st.markdown(f"- **Total:** R$ {total_leiloeiro_assessoria:,.2f}")

    st.markdown("**Custos após Imissão na Posse:**")
    st.markdown(f"- Reforma/Pintura/Ajustes: R$ {custo_reforma:,.2f}")
    st.markdown(f"- Outros: R$ {outros_custos:,.2f}")
    st.markdown(f"- **Total:** R$ {total_reforma:,.2f}")

    st.markdown("**Custos mensais até a venda:**")
    st.markdown(f"- IPTU mensal: R$ {iptu_mensal:,.2f} → Total: R$ {total_iptu:,.2f}")
    st.markdown(f"- Condomínio mensal: R$ {condominio_mensal:,.2f} → Total: R$ {total_condominio:,.2f}")
    st.markdown(f"- **Total:** R$ {total_mensal:,.2f}")

    st.markdown(f"**Comissão pela venda no mercado:** R$ {comissao_venda:,.2f} ({comissao_venda_percent:.1f}%)")

    st.markdown("---")
    st.markdown("### Resumo Final:")
    st.markdown(f"- **Total de Outros Custos:** R$ {total_outros_custos:,.2f}")
    st.markdown(f"- **Total investido (arremate + todos os custos):** R$ {total_investido:,.2f}")
    st.markdown(f"- **Valor de venda:** R$ {valor_mercado:,.2f}")
    st.markdown(f"- **Resultado do investidor:** R$ {resultado:,.2f} ({percentual:.1f}%)")
    st.markdown(f"- **Equivalente de rendimento mensal:** {rendimento_mensal:.2f}% ao mês")
