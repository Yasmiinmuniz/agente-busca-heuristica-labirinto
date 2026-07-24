"""
pygame_compare.py
------------------
Roda BFS, Greedy Best-First e A* AO MESMO TEMPO no mesmo labirinto,
cada um em um painel lado a lado, para comparar visualmente como cada
estratégia de busca explora o espaço de estados.

Como funciona (sem alterar a lógica de nenhum algoritmo):
  - Cada algoritmo roda em sua própria thread, chamando a função de
    busca original (bfs_search / greedy_best_first_search / astar_search)
    com o mesmo `on_expand` já usado em pygame_visualize.py.
  - Cada thread só ESCREVE seu próprio estado (Open/Closed List atuais)
    em um dicionário compartilhado; a thread principal (pygame) apenas
    LÊ esse estado a ~60 quadros/s para desenhar os três painéis.
  - Como os três algoritmos têm ritmos e números de expansão diferentes
    (ex.: Greedy expande poucos nós e termina rápido; BFS expande muitos
    e demora mais), eles terminam em momentos diferentes — isso é
    justamente o que queremos evidenciar: a eficiência de cada busca.

Uso:
    python pygame_compare.py
"""

import sys
import threading
import time

import pygame

from maze_env import MazeEnv
from agents import bfs_search, greedy_best_first_search, astar_search
import pygame_visualize as pv

# ------------------------------------------------------------------ #
# Configuração
# ------------------------------------------------------------------ #
CELL_SIZE = 18          # menor que no modo single-view, para caber 3 lado a lado
PANEL_GAP = 12          # espaço entre painéis
STEP_DELAY_S = 0.03     # atraso entre expansões, por thread (mesma ideia de ANIMATION_DELAY_MS)

ALGORITHMS = [
    ("BFS", bfs_search),
    ("GREEDY", greedy_best_first_search),
    ("A*", astar_search),
]


class PanelState:
    """Estado compartilhado de um painel (um algoritmo). A thread do
    algoritmo escreve; a thread principal (pygame) só lê para desenhar."""

    def __init__(self):
        self.lock = threading.Lock()
        self.closed = set()
        self.open_nodes = set()
        self.path = []
        self.done = False
        self.result = None

    def update(self, closed, open_nodes):
        with self.lock:
            self.closed = closed
            self.open_nodes = open_nodes

    def snapshot(self):
        with self.lock:
            return set(self.closed), set(self.open_nodes), list(self.path)

    def finish(self, result):
        with self.lock:
            self.result = result
            self.path = result["path"]
            self.done = True


def _make_worker(fn, env, state):
    """Cria a função que roda em thread: chama a busca original com o
    hook on_expand, apenas observando e pausando um pouco a cada passo
    para a animação ficar visível. A lógica da busca não é tocada."""

    def worker():
        def on_expand(current, closed_set, open_set):
            state.update(closed_set, open_set)
            time.sleep(STEP_DELAY_S)

        result = fn(env, on_expand=on_expand)
        state.finish(result)

    return worker


def run_comparison(env=None):
    if env is None:
        env = MazeEnv(size=15, obstacle_prob=0.28, seed=0)

    panel_w = env.size * CELL_SIZE
    panel_h = pv.HUD_HEIGHT + env.size * CELL_SIZE
    width = len(ALGORITHMS) * panel_w + (len(ALGORITHMS) - 1) * PANEL_GAP
    height = panel_h

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("BFS vs Greedy vs A* — comparação ao vivo")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("couriernew", 16, bold=True)
    font_small = pygame.font.SysFont("couriernew", 12, bold=True)

    states = [PanelState() for _ in ALGORITHMS]
    threads = []
    for (name, fn), state in zip(ALGORITHMS, states):
        # cada thread busca sobre o MESMO env (só leitura: neighbors/grid),
        # sem escrever nele — por isso é seguro compartilhar entre threads.
        t = threading.Thread(target=_make_worker(fn, env, state), daemon=True)
        threads.append(t)
        t.start()

    def draw_frame():
        screen.fill(pv.COLOR_BG)
        for i, ((name, _), state) in enumerate(zip(ALGORITHMS, states)):
            ox = i * (panel_w + PANEL_GAP)
            closed, open_nodes, path = state.snapshot()
            pv._draw_grid(screen, env, closed=closed, open_nodes=open_nodes,
                           path=path, origin=(ox, pv.HUD_HEIGHT), cell_size=CELL_SIZE)
            status = "CONCLUIDO" if state.done else "BUSCANDO..."
            cost = state.result["cost"] if state.done and state.result else None
            pv._draw_hud(screen, font_big, font_small, panel_w, status,
                         nodes_expanded=len(closed), cost=cost,
                         origin=(ox, 0), title=name)
        pygame.display.flip()

    # Loop principal: só redesenha o estado mais recente de cada thread,
    # até todas terminarem, e depois mantém a tela final visível.
    while not all(s.done for s in states):
        pv._pump_events()
        draw_frame()
        clock.tick(60)

    print("Comparação concluída:")
    for (name, _), state in zip(ALGORITHMS, states):
        r = state.result
        print(f"  {name:<8} custo={r['cost']}  nós_expandidos={r['nodes_expanded']}")

    print("Feche a janela para encerrar.")
    while True:
        pv._pump_events()
        draw_frame()
        clock.tick(30)


if __name__ == "__main__":
    run_comparison()
