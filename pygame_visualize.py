"""
pygame_visualize.py
--------------------
Visualização animada do PROCESSO de busca do A*, não apenas do caminho
final, com estética retrô inspirada em jogos de arcade dos anos 90
(paleta e labirinto no estilo Pac-Man).

Este módulo NÃO altera a lógica do algoritmo (agents.astar_search): ele
apenas se conecta ao gancho opcional `on_expand`, que o A* já expõe (ver
agents.py), recebendo uma cópia do estado do algoritmo a cada nó
expandido, e desenha esse estado na tela. Toda a estética abaixo é só
renderização — não influencia em nada a busca.

Conceitos exibidos (explicabilidade para a apresentação da disciplina):

  - Open List (fronteira, ciano): conjunto de nós já descobertos, mas
    ainda não expandidos. É a fila de prioridade do A*, ordenada por
    f(n) = g(n) + h(n). Representa os candidatos que o algoritmo ainda
    pode escolher visitar em seguida.

  - Closed List (explorados, rosa/magenta): conjunto de nós que já foram
    expandidos — todos os seus vizinhos já foram processados. Evita que o
    algoritmo reprocesse o mesmo nó e mostra, ao final, toda a "área de
    busca" que o A* precisou visitar até encontrar o objetivo.

  - Por que importam: a Open List guia PARA ONDE o algoritmo olha a
    seguir (guiada por custo + heurística), e a Closed List registra O QUE
    já foi decidido. Comparando a área varrida (magenta) com o caminho
    final (amarelo), fica visualmente evidente que o A* não explora o
    grid inteiro como uma busca cega (BFS) faria — ele é guiado pela
    heurística de Manhattan em direção ao objetivo.

Uso:
    python pygame_visualize.py
"""

import sys
import pygame

from maze_env import MazeEnv
from agents import astar_search

# ------------------------------------------------------------------ #
# Configuração da animação — ajuste aqui para acelerar/desacelerar
# ------------------------------------------------------------------ #
ANIMATION_DELAY_MS = 30       # atraso (ms) entre cada expansão de nó exibida
CELL_SIZE = 32                # tamanho de cada célula do grid, em pixels
HUD_HEIGHT = 56               # altura do painel de estatísticas (estilo placar de arcade)

# ------------------------------------------------------------------ #
# Paleta retrô (estilo arcade anos 90 / Pac-Man)
#   - fundo bem escuro, paredes azul-elétrico, "pac-dots" nas células
#     livres, cores neon para Open/Closed List.
#   - Nota de design: como as paredes do labirinto (estilo Pac-Man) usam
#     azul, o caminho final foi definido em AMARELO (a cor do próprio
#     Pac-Man) para não conflitar visualmente com as paredes.
# ------------------------------------------------------------------ #
COLOR_BG = (6, 6, 20)              # fundo do labirinto (quase preto/azulado)
COLOR_OBSTACLE = (30, 60, 220)     # azul elétrico - paredes (estilo Pac-Man)
COLOR_OBSTACLE_EDGE = (110, 150, 255)  # contorno mais claro, dá efeito "neon"
COLOR_PELLET = (255, 215, 90)       # pac-dot nas células livres
COLOR_OPEN = (0, 229, 255)         # ciano   - Open List (fronteira)
COLOR_CLOSED = (255, 64, 180)      # magenta - Closed List (já explorados)
COLOR_PATH = (255, 221, 0)         # amarelo - caminho final (cor do Pac-Man)
COLOR_START = (60, 220, 100)       # verde   - posição inicial
COLOR_GOAL = (255, 70, 70)         # vermelho- objetivo (estilo "fantasma")
COLOR_HUD_BG = (10, 10, 30)
COLOR_HUD_TEXT = (255, 221, 0)
COLOR_HUD_TEXT_DIM = (140, 140, 170)


def _draw_grid(screen, env, closed=(), open_nodes=(), path=(), origin=(0, HUD_HEIGHT), cell_size=None):
    """Desenha o labirinto: paredes estilo arcade, pac-dots nas células
    livres, Open List, Closed List e caminho final (quando houver), com
    início/objetivo sempre visíveis por cima.

    `origin` é o canto superior esquerdo (em pixels) onde o labirinto
    começa a ser desenhado — permite posicionar múltiplos labirintos lado
    a lado na mesma janela (ver pygame_compare.py), sem duplicar a lógica
    de desenho."""
    closed = set(closed)
    open_nodes = set(open_nodes)
    path = set(path)
    cell = cell_size or CELL_SIZE
    ox, oy = origin

    for r in range(env.size):
        for c in range(env.size):
            pos = (r, c)
            x, y = ox + c * cell, oy + r * cell
            rect = pygame.Rect(x, y, cell, cell)

            # fundo escuro em toda célula (estética de labirinto de arcade)
            pygame.draw.rect(screen, COLOR_BG, rect)

            if env.grid[r][c] == 1:
                # parede: bloco azul elétrico com contorno neon
                pygame.draw.rect(screen, COLOR_OBSTACLE, rect.inflate(-4, -4), border_radius=3)
                pygame.draw.rect(screen, COLOR_OBSTACLE_EDGE, rect.inflate(-4, -4), width=1, border_radius=3)
                continue

            if pos in path:
                color = COLOR_PATH
            elif pos in closed:
                color = COLOR_CLOSED
            elif pos in open_nodes:
                color = COLOR_OPEN
            else:
                color = None  # célula livre "normal" -> só o pac-dot

            if color is not None:
                pygame.draw.rect(screen, color, rect.inflate(-3, -3), border_radius=3)
            else:
                # pac-dot: pequeno círculo central, como os pontos do Pac-Man
                center = (x + cell // 2, y + cell // 2)
                pygame.draw.circle(screen, COLOR_PELLET, center, max(1, cell // 10))

    # Início e objetivo desenhados por cima, como círculos (estilo Pac-Man/fantasma)
    for pos, color in ((env.start, COLOR_START), (env.goal, COLOR_GOAL)):
        r, c = pos
        x, y = ox + c * cell, oy + r * cell
        center = (x + cell // 2, y + cell // 2)
        pygame.draw.circle(screen, color, center, max(2, cell // 2 - 2))


def _draw_hud(screen, font_big, font_small, width, status, nodes_expanded, cost=None,
              origin=(0, 0), title="A* MAZE ARCADE"):
    """Painel superior estilo placar de fliperama: nome do algoritmo,
    contagem de nós expandidos (Open/Closed List) e status da busca.

    `origin` posiciona o painel (permite um HUD por algoritmo, lado a
    lado, em pygame_compare.py)."""
    ox, oy = origin
    pygame.draw.rect(screen, COLOR_HUD_BG, pygame.Rect(ox, oy, width, HUD_HEIGHT))
    pygame.draw.line(screen, COLOR_OBSTACLE_EDGE, (ox, oy + HUD_HEIGHT - 2), (ox + width, oy + HUD_HEIGHT - 2), 2)

    title_surf = font_big.render(title, True, COLOR_HUD_TEXT)
    screen.blit(title_surf, (ox + 8, oy + 4))

    info_parts = [f"NOS: {nodes_expanded}"]
    if cost is not None:
        info_parts.append(f"CUSTO: {cost}")
    info_parts.append(status)
    info_text = " | ".join(info_parts)
    info = font_small.render(info_text, True, COLOR_HUD_TEXT_DIM)
    screen.blit(info, (ox + 8, oy + 30))


def _pump_events():
    """Processa eventos da janela do Pygame durante os atrasos da
    animação (evita que o SO marque a janela como 'not responding') e
    permite fechar a janela a qualquer momento pelo X."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


def run_astar_visualization(env=None):
    """Executa o A* (sua lógica original, inalterada) e anima cada
    expansão de nó em tempo real usando o callback on_expand, com HUD
    de estatísticas ao vivo estilo placar de arcade."""
    if env is None:
        env = MazeEnv(size=15, obstacle_prob=0.28, seed=0)

    pygame.init()
    width = env.size * CELL_SIZE
    height = HUD_HEIGHT + env.size * CELL_SIZE
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("A* Maze Arcade — Open List (ciano) e Closed List (magenta)")
    clock = pygame.time.Clock()

    font_big = pygame.font.SysFont("couriernew", 20, bold=True)
    font_small = pygame.font.SysFont("couriernew", 14, bold=True)

    # Guarda o último snapshot de Open/Closed List para redesenhar o
    # estado final junto com o caminho encontrado (ver abaixo).
    last_state = {"closed": set(), "open": set()}

    def on_expand(current, closed_set, open_set):
        """Callback passado ao A* (agents.astar_search). É chamado uma vez
        por nó expandido, com cópias da Closed List e da Open List naquele
        instante — apenas observa e desenha, não interfere na busca."""
        last_state["closed"] = closed_set
        last_state["open"] = open_set

        _pump_events()
        _draw_grid(screen, env, closed=closed_set, open_nodes=open_set)
        _draw_hud(screen, font_big, font_small, width,
                  status="BUSCANDO...", nodes_expanded=len(closed_set))
        pygame.display.flip()
        pygame.time.delay(ANIMATION_DELAY_MS)
        clock.tick(60)

    result = astar_search(env, on_expand=on_expand)

    # Estado final: mantém Open List e Closed List visíveis (para
    # evidenciar como o algoritmo tomou sua decisão) e destaca o caminho
    # encontrado em amarelo por cima de tudo.
    _pump_events()
    _draw_grid(screen, env, closed=last_state["closed"],
               open_nodes=last_state["open"], path=result["path"])
    status = "CAMINHO ENCONTRADO!" if result["success"] else "SEM SOLUCAO"
    _draw_hud(screen, font_big, font_small, width, status=status,
              nodes_expanded=result["nodes_expanded"], cost=result["cost"])
    pygame.display.flip()

    print(f"Busca concluída — sucesso={result['success']}, "
          f"custo={result['cost']}, nós expandidos={result['nodes_expanded']}")
    print("Feche a janela para encerrar.")

    while True:
        _pump_events()
        clock.tick(30)


if __name__ == "__main__":
    run_astar_visualization()
