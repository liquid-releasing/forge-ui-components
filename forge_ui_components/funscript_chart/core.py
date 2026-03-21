"""Framework-agnostic chart logic: data prep, color mapping, Plotly figures."""


def prepare_chart_data(actions: list[dict]) -> dict:
    """Extract timestamps and positions from funscript actions.

    Args:
        actions: List of {"at": ms, "pos": 0-100} dicts.

    Returns:
        Dict with "times" (seconds) and "positions" lists.
    """
    times = [a["at"] / 1000.0 for a in actions]
    positions = [a["pos"] for a in actions]
    return {"times": times, "positions": positions}


def monochrome_figure(chart_data: dict, *, color: str = "#4C8BF5", title: str = ""):
    """Build a monochrome Plotly figure — fast, no assessment needed.

    Args:
        chart_data: Output of prepare_chart_data.
        color: Line color (default blue).
        title: Optional chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=chart_data["times"],
        y=chart_data["positions"],
        mode="lines",
        line=dict(color=color, width=1),
        name="Position",
    ))
    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Position",
        yaxis=dict(range=[0, 100]),
        margin=dict(l=40, r=20, t=40, b=40),
        height=250,
    )
    return fig


def vibrant_figure(chart_data: dict, phrases: list[dict], *, title: str = ""):
    """Build a color-coded Plotly figure — requires assessment phrases.

    Args:
        chart_data: Output of prepare_chart_data.
        phrases: List of phrase dicts with "start", "end", "color", "label".
        title: Optional chart title.

    Returns:
        plotly.graph_objects.Figure
    """
    import plotly.graph_objects as go

    fig = go.Figure()
    for phrase in phrases:
        start_s = phrase["start"] / 1000.0
        end_s = phrase["end"] / 1000.0
        mask = [
            (i, t, p)
            for i, (t, p) in enumerate(zip(chart_data["times"], chart_data["positions"]))
            if start_s <= t <= end_s
        ]
        if mask:
            ts = [m[1] for m in mask]
            ps = [m[2] for m in mask]
            fig.add_trace(go.Scatter(
                x=ts,
                y=ps,
                mode="lines",
                line=dict(color=phrase.get("color", "#4C8BF5"), width=1),
                name=phrase.get("label", ""),
                showlegend=False,
            ))
    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Position",
        yaxis=dict(range=[0, 100]),
        margin=dict(l=40, r=20, t=40, b=40),
        height=250,
    )
    return fig
