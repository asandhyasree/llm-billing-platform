"""Reusable Plotly chart helpers for the dashboard pages."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def spend_line_chart(daily_data: list[dict]) -> go.Figure:
    """Multi-line chart of daily spend per tenant."""
    if not daily_data:
        return go.Figure()
    df = pd.DataFrame(daily_data)
    fig = px.line(
        df,
        x="date",
        y="billed_cost_usd",
        color="tenant_id",
        title="Daily spend by tenant (last 30 days)",
        labels={"billed_cost_usd": "Billed cost (USD)", "date": "Date"},
    )
    fig.update_layout(legend_title_text="Tenant")
    return fig


def model_bar_chart(model_data: list[dict]) -> go.Figure:
    """Side-by-side bar chart of input vs output tokens per model."""
    if not model_data:
        return go.Figure()
    df = pd.DataFrame(model_data)
    fig = go.Figure(data=[
        go.Bar(name="Input tokens",  x=df["model"], y=df["input_tokens"]),
        go.Bar(name="Output tokens", x=df["model"], y=df["output_tokens"]),
    ])
    fig.update_layout(
        barmode="group",
        title="Token usage by model",
        xaxis_title="Model",
        yaxis_title="Tokens",
    )
    return fig


def forecast_chart(daily_costs: list[float], projected: list[float]) -> go.Figure:
    """Actuals overlaid with projected spend line."""
    actual_x    = list(range(len(daily_costs)))
    projected_x = list(range(len(daily_costs), len(daily_costs) + len(projected)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual_x, y=daily_costs, mode="lines+markers", name="Actual"))
    fig.add_trace(go.Scatter(x=projected_x, y=projected, mode="lines", name="Projected", line=dict(dash="dash")))
    fig.update_layout(title="Spend forecast", xaxis_title="Day", yaxis_title="Cost (USD)")
    return fig
