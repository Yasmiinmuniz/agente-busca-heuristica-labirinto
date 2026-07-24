"""
visualize.py
------------
Renderiza o labirinto e o caminho encontrado por um agente em uma imagem
PNG, na mesma estética retrô/arcade (anos 90, estilo Pac-Man) usada em
pygame_visualize.py e charts.py — fundo escuro, paredes azul-elétrico,
pac-dots nas células livres e caminho final em amarelo.

Usado para:
  - mostrar a "evolução visual" do agente (comportamento inicial vs. final)
  - registrar o resultado final da tarefa (item 10 do roteiro)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Mesma paleta neon/arcade usada em pygame_visualize.py e charts.py
COLOR_BG = "#06061a"          # fundo do labirinto (quase preto/azulado)
COLOR_PANEL = "#0a0a1e"       # fundo da figura (fora do grid)
COLOR_WALL = "#1e3cdc"        # azul elétrico - paredes
COLOR_WALL_EDGE = "#6e96ff"   # contorno neon das paredes
COLOR_PELLET = "#ffd75a"      # pac-dot nas células livres
COLOR_PATH = "#ffdd00"        # amarelo - caminho final (cor do Pac-Man)
COLOR_START = "#3cdc64"       # verde - início
COLOR_GOAL = "#ff4646"        # vermelho - objetivo
COLOR_TEXT = "#ffdd00"        # amarelo - título (mesma cor do HUD do Pygame)


def render_maze(env, path=None, title="", save_path=None):
    n = env.size
    path = set(path or [])
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor(COLOR_PANEL)
    ax.set_facecolor(COLOR_BG)

    for r in range(n):
        for c in range(n):
            pos = (r, c)
            y = n - 1 - r

            if env.grid[r][c] == 1:
                # parede: bloco azul elétrico com contorno neon (estilo Pac-Man)
                ax.add_patch(patches.FancyBboxPatch(
                    (c + 0.08, y + 0.08), 0.84, 0.84,
                    boxstyle="round,pad=0,rounding_size=0.08",
                    facecolor=COLOR_WALL, edgecolor=COLOR_WALL_EDGE, linewidth=1.4))
                continue

            if pos in path:
                ax.add_patch(patches.FancyBboxPatch(
                    (c + 0.06, y + 0.06), 0.88, 0.88,
                    boxstyle="round,pad=0,rounding_size=0.1",
                    facecolor=COLOR_PATH, edgecolor="none"))
            else:
                # pac-dot: célula livre "normal"
                ax.add_patch(plt.Circle((c + 0.5, y + 0.5), 0.07, facecolor=COLOR_PELLET, edgecolor="none"))

    sr, sc = env.start
    gr, gc = env.goal
    ax.add_patch(plt.Circle((sc + 0.5, n - 1 - sr + 0.5), 0.42, facecolor=COLOR_START, edgecolor="black", linewidth=1))
    ax.add_patch(plt.Circle((gc + 0.5, n - 1 - gr + 0.5), 0.42, facecolor=COLOR_GOAL, edgecolor="black", linewidth=1))

    ax.text(sc + 0.5, n - 1 - sr + 0.5, "S", ha="center", va="center", fontweight="bold", color="black", fontsize=11)
    ax.text(gc + 0.5, n - 1 - gr + 0.5, "G", ha="center", va="center", fontweight="bold", color="black", fontsize=11)

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(COLOR_WALL_EDGE)
    ax.set_title(title, color=COLOR_TEXT, fontsize=13, fontweight="bold", fontfamily="monospace")

    if save_path:
        plt.savefig(save_path, dpi=130, bbox_inches="tight", facecolor=COLOR_PANEL)
        plt.close(fig)
    else:
        plt.show()
