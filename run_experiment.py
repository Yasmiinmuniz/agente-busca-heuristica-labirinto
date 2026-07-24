"""
run_experiment.py
-----------------
Protocolo de avaliação (item 8 do roteiro):
  - Gera N labirintos com sementes diferentes (mesmo tamanho, mesma densidade
    de obstáculos) para reduzir viés de uma única instância.
  - Roda os três agentes (BFS, Greedy Best-First, A*) em cada labirinto.
  - Métricas coletadas: sucesso, custo do caminho (nº de passos), nós
    expandidos, tempo de execução.
  - Compara A* explicitamente com a referência não-informada (BFS) e com
    a versão ingênua (Greedy), respondendo: A* é ótimo como o BFS, mas
    expande menos nós por usar a heurística para guiar a busca.
  - Salva imagens do labirinto com o caminho encontrado (evidência visual,
    itens 5 e 10 do roteiro).

Uso:
    python run_experiment.py
"""

import time
import statistics as stats

from maze_env import MazeEnv
from agents import bfs_search, greedy_best_first_search, astar_search
from visualize import render_maze

N_MAZES = 10          # número de labirintos por rodada de teste
MAZE_SIZE = 15
OBSTACLE_PROB = 0.28
SEEDS = list(range(N_MAZES))

AGENT_FUNCS = {
    "BFS": bfs_search,
    "Greedy": greedy_best_first_search,
    "A*": astar_search,
}


def run_single(env, fn):
    t0 = time.perf_counter()
    result = fn(env)
    result["time_ms"] = (time.perf_counter() - t0) * 1000
    return result


def main():
    results = {name: [] for name in AGENT_FUNCS}

    for seed in SEEDS:
        env = MazeEnv(size=MAZE_SIZE, obstacle_prob=OBSTACLE_PROB, seed=seed)
        for name, fn in AGENT_FUNCS.items():
            r = run_single(env, fn)
            results[name].append(r)

    print("=" * 70)
    print(f"Protocolo de avaliação — {N_MAZES} labirintos {MAZE_SIZE}x{MAZE_SIZE}, "
          f"obstacle_prob={OBSTACLE_PROB}")
    print("=" * 70)
    header = f"{'Agente':<10}{'Sucesso':<10}{'Custo médio':<14}{'Nós expandidos (média)':<24}{'Tempo médio (ms)':<18}"
    print(header)
    print("-" * len(header))

    for name, runs in results.items():
        successes = [r for r in runs if r["success"]]
        success_rate = len(successes) / len(runs) * 100
        avg_cost = stats.mean(r["cost"] for r in successes) if successes else float("nan")
        avg_nodes = stats.mean(r["nodes_expanded"] for r in runs)
        avg_time = stats.mean(r["time_ms"] for r in runs)
        print(f"{name:<10}{success_rate:<10.1f}{avg_cost:<14.2f}{avg_nodes:<24.2f}{avg_time:<18.3f}")

    print("\nConclusão esperada: BFS e A* encontram o caminho de custo mínimo "
          "(mesmo custo médio), mas A* expande menos nós que o BFS por usar "
          "a heurística de Manhattan para guiar a busca. O Greedy expande "
          "poucos nós, mas pode gerar caminhos sub-ótimos (custo maior) ou "
          "falhar ao ficar preso em becos sem saída, pois ignora o custo já "
          "percorrido.")

    # --- Evidência visual (itens 5 e 10) --------------------------------
    demo_env = MazeEnv(size=MAZE_SIZE, obstacle_prob=OBSTACLE_PROB, seed=0)

    greedy_r = greedy_best_first_search(demo_env)
    astar_r = astar_search(demo_env)
    bfs_r = bfs_search(demo_env)

    render_maze(demo_env, path=greedy_r["path"],
                title=f"Greedy Best-First (ingênuo) — custo={greedy_r['cost']}, nós={greedy_r['nodes_expanded']}",
                save_path="output_greedy.png")
    render_maze(demo_env, path=astar_r["path"],
                title=f"A* (final) — custo={astar_r['cost']}, nós={astar_r['nodes_expanded']}",
                save_path="output_astar.png")
    render_maze(demo_env, path=bfs_r["path"],
                title=f"BFS (referência) — custo={bfs_r['cost']}, nós={bfs_r['nodes_expanded']}",
                save_path="output_bfs.png")

    print("\nImagens salvas: output_greedy.png, output_astar.png, output_bfs.png")


if __name__ == "__main__":
    main()
