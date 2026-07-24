"""
agents.py
---------
Agentes de busca no espaço de estados do labirinto.

Todos recebem o MazeEnv (conhecimento completo do ambiente — busca é
feita "offline", sobre o modelo do ambiente, e depois o caminho encontrado
é executado passo a passo via env.step()).

Formulação computacional (comum aos três agentes):
    Estado:      (linha, coluna) do agente na grade
    Ações:       CIMA, BAIXO, ESQUERDA, DIREITA
    Objetivo:    estado == goal
    Custo:       1 por movimento (g(n))
    Heurística:  distância de Manhattan até o objetivo (h(n))
    f(n) = g(n) + h(n)   -> usado apenas pelo A*
    f(n) = h(n)          -> usado apenas pelo Greedy Best-First (ignora custo)
    f(n) = ordem FIFO    -> usado pelo BFS (ignora custo e heurística)

Cada função de busca retorna um dicionário com:
    path            lista de estados do caminho encontrado (vazio se falhou)
    actions         lista de ações correspondentes ao caminho
    nodes_expanded  quantidade de nós expandidos (métrica de eficiência)
    success         bool
    cost            custo total do caminho (len(path)-1)
"""

import heapq
import itertools
from collections import deque


def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(came_from, action_from, start, goal):
    if goal not in came_from and goal != start:
        return [], []
    path = [goal]
    actions = []
    cur = goal
    while cur != start:
        actions.append(action_from[cur])
        cur = came_from[cur]
        path.append(cur)
    path.reverse()
    actions.reverse()
    return path, actions


# --------------------------------------------------------------------- #
# 1) BFS — busca não-informada (referência / baseline do item 8)
# --------------------------------------------------------------------- #
def bfs_search(env, on_expand=None):
    """
    Parâmetro opcional `on_expand`: mesma finalidade e assinatura descrita
    em astar_search — apenas instrumentação/visualização, não afeta a
    lógica de busca.
    """
    start, goal = env.start, env.goal
    frontier = deque([start])
    came_from = {}
    action_from = {}
    visited = {start}
    nodes_expanded = 0

    while frontier:
        cur = frontier.popleft()
        nodes_expanded += 1

        if on_expand is not None:
            # Aqui a Open List é a fila FIFO `frontier` (ordem de chegada,
            # sem custo nem heurística) e a Closed List é `visited`.
            on_expand(cur, set(visited), set(frontier))

        if cur == goal:
            path, actions = _reconstruct(came_from, action_from, start, goal)
            return {"path": path, "actions": actions, "nodes_expanded": nodes_expanded,
                    "success": True, "cost": len(path) - 1}
        for a, nxt in env.neighbors(cur):
            if nxt not in visited:
                visited.add(nxt)
                came_from[nxt] = cur
                action_from[nxt] = a
                frontier.append(nxt)

    return {"path": [], "actions": [], "nodes_expanded": nodes_expanded, "success": False, "cost": None}


# --------------------------------------------------------------------- #
# 2) Greedy Best-First — versão "ingênua": só olha a heurística,
#    ignora o custo já percorrido. É o comportamento inicial/naive
#    que pode ficar preso em becos sem saída ou achar caminhos ruins.
# --------------------------------------------------------------------- #
def greedy_best_first_search(env, on_expand=None):
    """
    Parâmetro opcional `on_expand`: mesma finalidade e assinatura descrita
    em astar_search — apenas instrumentação/visualização, não afeta a
    lógica de busca.
    """
    start, goal = env.start, env.goal
    counter = itertools.count()
    frontier = [(manhattan(start, goal), next(counter), start)]
    came_from = {}
    action_from = {}
    visited = {start}
    nodes_expanded = 0

    while frontier:
        _, _, cur = heapq.heappop(frontier)
        nodes_expanded += 1

        if on_expand is not None:
            # Open List: nós na fila de prioridade, ordenados só por h(n)
            # (ignora o custo já percorrido — por isso é "ingênuo").
            # Closed List: nós já expandidos (visited).
            open_nodes = {item[2] for item in frontier}
            on_expand(cur, set(visited), open_nodes)

        if cur == goal:
            path, actions = _reconstruct(came_from, action_from, start, goal)
            return {"path": path, "actions": actions, "nodes_expanded": nodes_expanded,
                    "success": True, "cost": len(path) - 1}
        for a, nxt in env.neighbors(cur):
            if nxt not in visited:
                visited.add(nxt)
                came_from[nxt] = cur
                action_from[nxt] = a
                heapq.heappush(frontier, (manhattan(nxt, goal), next(counter), nxt))

    return {"path": [], "actions": [], "nodes_expanded": nodes_expanded, "success": False, "cost": None}


# --------------------------------------------------------------------- #
# 3) A* — versão final/robusta: combina custo já percorrido (g) com a
#    heurística (h). Garante caminho ótimo (heurística de Manhattan é
#    admissível para movimentos ortogonais de custo 1).
# --------------------------------------------------------------------- #
def astar_search(env, on_expand=None):
    """
    Parâmetro opcional `on_expand` (instrumentação/visualização):
        Callback chamado a cada nó expandido, no formato
        on_expand(current, closed_set, open_set), onde:
          - closed_set: cópia da Closed List (nós já expandidos até agora)
          - open_set:   cópia da Open List (nós na fronteira, aguardando expansão)
        Não afeta a lógica, os critérios de expansão nem o resultado da
        busca — serve apenas para permitir observar/animar o algoritmo
        externamente (ver pygame_visualize.py). Quando None (padrão), o
        comportamento é idêntico ao original.
    """
    start, goal = env.start, env.goal
    counter = itertools.count()
    g_score = {start: 0}
    frontier = [(manhattan(start, goal), next(counter), start)]
    came_from = {}
    action_from = {}
    visited = set()
    nodes_expanded = 0

    while frontier:
        _, _, cur = heapq.heappop(frontier)
        if cur in visited:
            continue
        visited.add(cur)
        nodes_expanded += 1

        if on_expand is not None:
            # Open List: nós já descobertos mas ainda não expandidos —
            # são os "candidatos" que o A* pode escolher visitar em
            # seguida, ordenados por f(n) = g(n) + h(n) no heap `frontier`.
            # Closed List: nós já expandidos (visited) — o algoritmo não
            # os reconsidera, o que evita retrabalho e garante progresso.
            # Esses dois conjuntos são o que faz o A* "decidir" o caminho:
            # a Open List indica para onde olhar a seguir, e a Closed List
            # registra o que já foi decidido/descartado.
            open_nodes = {item[2] for item in frontier}
            on_expand(cur, set(visited), open_nodes)

        if cur == goal:
            path, actions = _reconstruct(came_from, action_from, start, goal)
            return {"path": path, "actions": actions, "nodes_expanded": nodes_expanded,
                    "success": True, "cost": len(path) - 1}

        for a, nxt in env.neighbors(cur):
            tentative_g = g_score[cur] + 1
            if nxt not in g_score or tentative_g < g_score[nxt]:
                g_score[nxt] = tentative_g
                came_from[nxt] = cur
                action_from[nxt] = a
                f = tentative_g + manhattan(nxt, goal)
                heapq.heappush(frontier, (f, next(counter), nxt))

    return {"path": [], "actions": [], "nodes_expanded": nodes_expanded, "success": False, "cost": None}


AGENTS = {
    "BFS (referência, não-informado)": bfs_search,
    "Greedy Best-First (ingênuo, só heurística)": greedy_best_first_search,
    "A* (final, custo + heurística)": astar_search,
}
