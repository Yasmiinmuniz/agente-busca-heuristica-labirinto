"""
charts.py
---------
Gera gráficos comparativos entre os agentes (custo, nós expandidos e
tempo de execução), no mesmo tema visual retrô/arcade usado em
pygame_visualize.py — só para consistência estética entre a animação
ao vivo e os gráficos do relatório final.

Usado por run_experiment.py ao final do protocolo de avaliação (item 8
do roteiro: métricas e comparação com estratégia de referência).
"""

import matplotlib.pyplot as plt

# Mesma paleta neon/arcade usada em pygame_visualize.py, para manter a
# identidade visual entre a animação em tempo real e os gráficos.
BG_DARK = "#06061a"
PANEL_DARK = "#0f0f2a"
TEXT_COLOR = "#ffdd00"        # amarelo, cor do Pac-Man
GRID_COLOR = "#2a2a55"

AGENT_COLORS = {
    "BFS": "#ff40b4",       # magenta (mesma cor da Closed List)
    "Greedy": "#1e3cdc",    # azul (mesma cor das paredes)
    "A*": "#00e5ff",        # ciano (mesma cor da Open List)
}


def _style_axis(ax, title, ylabel):
    ax.set_facecolor(PANEL_DARK)
    ax.set_title(title, color=TEXT_COLOR, fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel, color="white", fontsize=9)
    ax.tick_params(colors="white", labelsize=9)
    ax.grid(axis="y", color=GRID_COLOR, linestyle="--", linewidth=0.7)
    for spine in ax.spines.values():
        spine.set_color(GRID_COLOR)


def plot_comparison(summary, save_path="comparison_chart.png"):
    """
    Gera uma figura com 3 subgráficos de barra (custo médio, nós
    expandidos médios, tempo médio) comparando os agentes.

    `summary` deve ser um dicionário no formato:
        {"BFS": {"cost": .., "nodes": .., "time": ..}, "Greedy": {...}, "A*": {...}}
    """
    names = list(summary.keys())
    colors = [AGENT_COLORS.get(n, "#ffffff") for n in names]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    fig.patch.set_facecolor(BG_DARK)
    fig.suptitle("Comparação de Agentes — A* Maze Arcade", color=TEXT_COLOR,
                 fontsize=15, fontweight="bold")

    metrics = [
        ("cost", "Custo médio do caminho", "passos"),
        ("nodes", "Nós expandidos (média)", "nós"),
        ("time", "Tempo médio (ms)", "ms"),
    ]

    for ax, (key, title, ylabel) in zip(axes, metrics):
        values = [summary[n][key] for n in names]
        bars = ax.bar(names, values, color=colors, edgecolor="white", linewidth=0.8)
        _style_axis(ax, title, ylabel)
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    f"{value:.1f}", ha="center", va="bottom", color="white", fontsize=9)

    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(save_path, dpi=130, facecolor=BG_DARK)
    plt.close(fig)
