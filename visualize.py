"""
visualize.py
------------
Renderiza o labirinto e o caminho encontrado por um agente em uma imagem PNG.
Usado para:
  - mostrar a "evolução visual" do agente (comportamento inicial vs. final)
  - registrar o resultado final da tarefa (item 10 do roteiro)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches


def render_maze(env, path=None, title="", save_path=None):
    n = env.size
    fig, ax = plt.subplots(figsize=(6, 6))

    for r in range(n):
        for c in range(n):
            color = "black" if env.grid[r][c] == 1 else "white"
            ax.add_patch(patches.Rectangle((c, n - 1 - r), 1, 1, facecolor=color, edgecolor="lightgray"))

    if path:
        for (r, c) in path:
            ax.add_patch(patches.Rectangle((c, n - 1 - r), 1, 1, facecolor="#8ecae6", edgecolor="lightgray"))

    sr, sc = env.start
    gr, gc = env.goal
    ax.add_patch(patches.Rectangle((sc, n - 1 - sr), 1, 1, facecolor="#2a9d8f", edgecolor="black"))
    ax.add_patch(patches.Rectangle((gc, n - 1 - gr), 1, 1, facecolor="#e76f51", edgecolor="black"))

    ax.text(sc + 0.5, n - 1 - sr + 0.5, "S", ha="center", va="center", fontweight="bold")
    ax.text(gc + 0.5, n - 1 - gr + 0.5, "G", ha="center", va="center", fontweight="bold")

    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title)

    if save_path:
        plt.savefig(save_path, dpi=130, bbox_inches="tight")
        plt.close(fig)
    else:
        plt.show()
