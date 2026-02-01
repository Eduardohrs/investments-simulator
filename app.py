import streamlit as st
import plotly.graph_objects as go


# -----------------------------
# Simulador (baseado na engine)
# -----------------------------
def newinvestment(t, a, travelgoals, travelbudget, limit, initial_balance=15000):
    """
    t = taxa mensal (%)
    a = aporte mensal
    travelgoals = lista de patrimônios-alvo que disparam saques
    travelbudget = valor fixo sacado a cada evento
    limit = número de meses simulados
    """
    x0 = 0
    y0 = int(initial_balance)
    y = []
    y_start = []

    # Evita mutação perigosa da lista de entrada
    goals = list(travelgoals)
    withdraw_months = []

    while x0 < limit:
        # Patrimônio no início do mês (antes de rendimento/aporte)
        y_start.append(int(y0))
        y0 = int(y0 * (1 + t / 100) + a)
        for goal in list(goals):
            if y0 > goal:
                if travelbudget > y0:
                    raise ValueError(
                        "Saque inválido: o valor do saque é maior que o patrimônio no mês."
                    )
                y0 = y0 - travelbudget
                goals.remove(goal)
                withdraw_months.append(x0 + 1)  # meses são 1-based
        y.append(int(y0))
        x0 += 1

    return y, y_start, withdraw_months


# -----------------------------
# UI
# -----------------------------
st.set_page_config(page_title="Simulador de Investimentos", layout="centered")
st.title("Simulador de Investimentos (projeção)")
st.caption("Simulação simples de investimentos")

if "travelgoals" not in st.session_state:
    st.session_state.travelgoals = [30000, 50000, 80000]

tab_inputs, tab_chart, tab_summary = st.tabs(["Inputs", "Gráfico", "Resumo"])


with tab_inputs:
    st.subheader("Parâmetros")
    t = st.number_input("Taxa mensal (%)", min_value=-100.0, max_value=100.0, value=1.0, step=0.1)
    limit = st.number_input("Horizonte (meses)", min_value=1, max_value=600, value=120, step=1)
    initial_balance = st.number_input(
        "Patrimônio inicial (R$)",
        min_value=0,
        max_value=100_000_000,
        value=15000,
        step=1000,
    )
    monthly_contribution = st.number_input(
        "Aporte mensal (R$)",
        min_value=0,
        max_value=10_000_000,
        value=1000,
        step=100,
    )
    travel_budget = st.number_input(
        "Valor de cada saque (R$)",
        min_value=0,
        max_value=10_000_000,
        value=5000,
        step=100,
    )

    st.markdown("---")
    st.subheader("Saques por meta")
    st.caption(
        "Aqui você define valores de patrimônio-alvo. Quando o patrimônio ultrapassa uma meta, "
        "um saque de valor fixo é feito automaticamente."
    )
    col_add, col_btn = st.columns([2, 1])
    with col_add:
        new_goal = st.number_input(
            "Adicionar meta de saque (patrimônio-alvo)",
            min_value=1,
            max_value=10_000_000,
            value=60000,
            step=1000,
        )
    with col_btn:
        if st.button("Adicionar saque"):
            st.session_state.travelgoals.append(int(new_goal))

    if st.session_state.travelgoals:
        st.write("Metas atuais:", sorted(st.session_state.travelgoals))
        if st.button("Limpar metas"):
            st.session_state.travelgoals = []
    else:
        st.info("Nenhuma meta adicionada.")


def validate_inputs(rate, horizon, goals, initial, contribution, budget):
    if rate < 0:
        return "A taxa mensal não pode ser negativa."
    if horizon <= 0:
        return "O horizonte deve ser maior que zero."
    if any(g <= 0 for g in goals):
        return "Todas as metas devem ser maiores que zero."
    if initial < 0 or contribution < 0 or budget < 0:
        return "Valores monetários não podem ser negativos."
    return None


validation_error = validate_inputs(
    t, limit, st.session_state.travelgoals, initial_balance, monthly_contribution, travel_budget
)

if validation_error:
    st.error(validation_error)
    sim_data = None
else:
    try:
        sim_data = newinvestment(
            t=t,
            a=monthly_contribution,
            travelgoals=st.session_state.travelgoals,
            travelbudget=travel_budget,
            limit=int(limit),
            initial_balance=initial_balance,
        )
    except ValueError as exc:
        st.error(str(exc))
        sim_data = None


with tab_chart:
    st.subheader("Patrimônio ao longo do tempo")
    if sim_data is None:
        st.info("Corrija os inputs para visualizar o gráfico.")
    else:
        y, y_start, withdraw_months = sim_data
        months = list(range(1, len(y_start) + 1))

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=months,
                y=y_start,
                mode="lines",
                name="Patrimônio",
                line=dict(width=3),
            )
        )

        if withdraw_months:
            withdraw_values = [y_start[m - 1] for m in withdraw_months]
            fig.add_trace(
                go.Scatter(
                    x=withdraw_months,
                    y=withdraw_values,
                    mode="markers",
                    name="Saques",
                    marker=dict(size=10, symbol="x"),
                )
            )

        fig.update_layout(
            xaxis_title="Mês",
            yaxis_title="Patrimônio (R$)",
            hovermode="x unified",
            dragmode=False,
            height=480,
        )

        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": False, "displayModeBar": False, "doubleClick": False},
        )


with tab_summary:
    st.subheader("Resumo da simulação")
    if sim_data is None:
        st.info("Corrija os inputs para visualizar o resumo.")
    else:
        y, y_start, withdraw_months = sim_data
        total_withdrawals = len(withdraw_months) * travel_budget
        final_balance = y[-1] if y else initial_balance

        st.write(f"Patrimônio final: R$ {final_balance:,.0f}".replace(",", "."))
        st.write(f"Total sacado: R$ {total_withdrawals:,.0f}".replace(",", "."))
        st.write(f"Número de saques: {len(withdraw_months)}")
        if withdraw_months:
            st.write("Meses dos saques:", ", ".join(map(str, withdraw_months)))
        else:
            st.write("Meses dos saques: nenhum")
