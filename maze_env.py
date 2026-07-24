"""
maze_env.py
------------
Ambiente customizado: labirinto em grid NxN.

Representação:
    0 = célula livre
    1 = obstáculo
    S = posição inicial do agente
    G = posição objetivo (destino)

Estado:
    (linha, coluna) do agente na grade.

Ações (4, movimentos ortogonais):
    0 = CIMA
    1 = BAIXO
    2 = ESQUERDA
    3 = DIREITA

Recompensa (usada para caracterizar o problema como MDP, mesmo sendo
resolvido por busca no espaço de estados e não por aprendizado):
    -1   a cada passo (custo de movimentação)
    -10  ao tentar mover para obstáculo ou fora da grade (agente permanece parado)
    +100 ao alcançar o destino

Término:
    - agente alcança a célula objetivo (sucesso)
    - número de passos excede max_steps (falha / timeout)
"""

import random
from dataclasses import dataclass, field

ACTIONS = {
    0: (-1, 0),  # cima
    1: (1, 0),   # baixo
    2: (0, -1),  # esquerda
    3: (0, 1),   # direita
}
ACTION_NAMES = {0: "CIMA", 1: "BAIXO", 2: "ESQUERDA", 3: "DIREITA"}


@dataclass
class MazeEnv:
    size: int = 10
    obstacle_prob: float = 0.25
    max_steps: int = 500
    seed: int | None = None

    grid: list = field(default=None, init=False)
    start: tuple = field(default=None, init=False)
    goal: tuple = field(default=None, init=False)
    agent_pos: tuple = field(default=None, init=False)
    steps_taken: int = field(default=0, init=False)

    def __post_init__(self):
        self._generate_maze()
        self.reset()

    # ------------------------------------------------------------------ #
    # Geração do ambiente
    # ------------------------------------------------------------------ #
    def _generate_maze(self):
        rng = random.Random(self.seed)
        n = self.size
        self.grid = [[0] * n for _ in range(n)]

        for r in range(n):
            for c in range(n):
                if rng.random() < self.obstacle_prob:
                    self.grid[r][c] = 1

        self.start = (0, 0)
        self.goal = (n - 1, n - 1)
        self.grid[self.start[0]][self.start[1]] = 0
        self.grid[self.goal[0]][self.goal[1]] = 0

        # garante que existe pelo menos um caminho válido (BFS de sanidade)
        if not self._path_exists(self.start, self.goal):
            self._regenerate_until_solvable(rng)

    def _regenerate_until_solvable(self, rng, max_tries=200):
        n = self.size
        for _ in range(max_tries):
            self.grid = [[0] * n for _ in range(n)]
            for r in range(n):
                for c in range(n):
                    if rng.random() < self.obstacle_prob:
                        self.grid[r][c] = 1
            self.grid[self.start[0]][self.start[1]] = 0
            self.grid[self.goal[0]][self.goal[1]] = 0
            if self._path_exists(self.start, self.goal):
                return
        raise RuntimeError("Não foi possível gerar labirinto solucionável.")

    def _path_exists(self, start, goal):
        from collections import deque
        visited = {start}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            if cur == goal:
                return True
            for dr, dc in ACTIONS.values():
                nxt = (cur[0] + dr, cur[1] + dc)
                if self._in_bounds(nxt) and nxt not in visited and self.grid[nxt[0]][nxt[1]] == 0:
                    visited.add(nxt)
                    queue.append(nxt)
        return False

    def _in_bounds(self, pos):
        r, c = pos
        return 0 <= r < self.size and 0 <= c < self.size

    def is_free(self, pos):
        return self._in_bounds(pos) and self.grid[pos[0]][pos[1]] == 0

    def neighbors(self, pos):
        """Estados vizinhos válidos (livres e dentro da grade) — usado pelos agentes de busca."""
        result = []
        for a, (dr, dc) in ACTIONS.items():
            nxt = (pos[0] + dr, pos[1] + dc)
            if self.is_free(nxt):
                result.append((a, nxt))
        return result

    # ------------------------------------------------------------------ #
    # Interface estilo "gym" (reset/step) — deixa explícito estado/ação/recompensa
    # ------------------------------------------------------------------ #
    def reset(self):
        self.agent_pos = self.start
        self.steps_taken = 0
        return self.agent_pos

    def step(self, action: int):
        self.steps_taken += 1
        dr, dc = ACTIONS[action]
        nxt = (self.agent_pos[0] + dr, self.agent_pos[1] + dc)

        if not self.is_free(nxt):
            reward = -10
            nxt = self.agent_pos  # permanece parado
        elif nxt == self.goal:
            reward = 100
        else:
            reward = -1

        self.agent_pos = nxt
        done = (self.agent_pos == self.goal) or (self.steps_taken >= self.max_steps)
        info = {"steps": self.steps_taken, "success": self.agent_pos == self.goal}
        return self.agent_pos, reward, done, info

    def render_ascii(self, path=None):
        path = set(path or [])
        lines = []
        for r in range(self.size):
            row = ""
            for c in range(self.size):
                pos = (r, c)
                if pos == self.agent_pos:
                    row += "A "
                elif pos == self.goal:
                    row += "G "
                elif pos == self.start:
                    row += "S "
                elif self.grid[r][c] == 1:
                    row += "# "
                elif pos in path:
                    row += ". "
                else:
                    row += "  "
            lines.append(row)
        return "\n".join(lines)
