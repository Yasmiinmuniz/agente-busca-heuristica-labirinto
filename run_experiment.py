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

Uso (com os valores padrão, iguais aos usados nos testes do projeto):
    python run_experiment.py

Uso com parâmetros escolhidos pelo usuário:
    python run_experiment.py --size 20 --num-mazes 15
    python run_experiment.py --seeds 3,7,42,100
    python run_experiment.py --size 25 --obstacle-prob 0.35 --num-mazes 5

Restrições (ver seção "Limites" abaixo): tamanho do labirinto, quantidade
de labirintos e densidade de obstáculos têm faixas válidas, para evitar
execuções que demorem demais ou labirintos com poucochance de ter solução.
"""

import argparse
import sys
import time
import statistics as stats

from maze_env import MazeEnv
from agents import bfs_search, greedy_best_first_search, astar_search
from visualize import render_maze
from charts import plot_comparison

# ------------------------------------------------------------------ #
# Limites (restrições) para os parâmetros escolhidos pelo usuário
# ------------------------------------------------------------------ #
# - Tamanho mínimo 5: labirintos menores que isso raramente têm obstáculos
#   suficientes para diferenciar BFS/Greedy/A* de forma interessante.
# - Tamanho máximo 40: acima disso, o BFS (busca não-informada) passa a
#   expandir milhares de nós e a geração de imagens fica lenta/pesada —
#   ainda funciona, mas foge do propósito de um experimento rápido.
# - Quantidade de labirintos entre 1 e 50: poucos labirintos (1) ainda são
#   úteis para um teste rápido; mais que 50 deixa de fazer sentido para
#   este protocolo (o ganho estatístico marginal não compensa o tempo).
# - obstacle_prob entre 0.0 e 0.6: acima de ~0.6 a chance de existir um
#   caminho válido cai muito, e o gerador de labirintos pode demorar para
#   encontrar uma configuração solucionável (ver maze_env._regenerate_until_solvable).
MIN_SIZE, MAX_SIZE = 5, 40
MIN_MAZES, MAX_MAZES = 1, 50
MIN_OBSTACLE_PROB, MAX_OBSTACLE_PROB = 0.0, 0.6

AGENT_FUNCS = {
    "BFS": bfs_search,
    "Greedy": greedy_best_first_search,
    "A*": astar_search,
}


def parse_args(argv=None):
    """Lê e valida os parâmetros da linha de comando. Em caso de valor
    fora dos limites, encerra com uma mensagem de erro clara (em vez de
    um traceback), explicando a restrição."""
    parser = argparse.ArgumentParser(
        description="Protocolo de avaliação dos agentes BFS, Greedy e A* no labirinto.")
    parser.add_argument("--size", type=int, default=15,
                         help=f"Tamanho do labirinto NxN (entre {MIN_SIZE} e {MAX_SIZE}). Padrão: 15")
    parser.add_argument("--num-mazes", type=int, default=10,
                         help=f"Quantidade de labirintos testados (entre {MIN_MAZES} e {MAX_MAZES}). Padrão: 10")
    parser.add_argument("--seeds", type=str, default=None,
                         help="Lista de seeds separadas por vírgula (ex: 3,7,42). "
                              "Se omitido, usa 0,1,2,...,num-mazes-1. Se informado, "
                              "a quantidade de seeds deve ser igual a --num-mazes.")
    parser.add_argument("--obstacle-prob", type=float, default=0.28,
                         help=f"Probabilidade de obstáculo por célula (entre {MIN_OBSTACLE_PROB} "
                              f"e {MAX_OBSTACLE_PROB}). Padrão: 0.28")
    args = parser.parse_args(argv)

    if not (MIN_SIZE <= args.size <= MAX_SIZE):
        parser.error(f"--size deve estar entre {MIN_SIZE} e {MAX_SIZE} (recebido: {args.size}). "
                     f"Labirintos menores que {MIN_SIZE} têm poucos obstáculos para comparar os "
                     f"agentes; maiores que {MAX_SIZE} deixam o BFS e a geração de imagens muito lentos.")

    if not (MIN_MAZES <= args.num_mazes <= MAX_MAZES):
        parser.error(f"--num-mazes deve estar entre {MIN_MAZES} e {MAX_MAZES} "
                     f"(recebido: {args.num_mazes}).")

    if not (MIN_OBSTACLE_PROB <= args.obstacle_prob <= MAX_OBSTACLE_PROB):
        parser.error(f"--obstacle-prob deve estar entre {MIN_OBSTACLE_PROB} e {MAX_OBSTACLE_PROB} "
                     f"(recebido: {args.obstacle_prob}). Acima disso, muitos labirintos gerados "
                     f"não têm caminho válido, e o gerador demora para achar um que tenha.")

    if args.seeds:
        try:
            seeds = [int(s.strip()) for s in args.seeds.split(",") if s.strip()]
        except ValueError:
            parser.error("--seeds deve ser uma lista de números inteiros separados por vírgula "
                         "(ex: --seeds 3,7,42)")
        if len(seeds) != args.num_mazes:
            parser.error(f"--seeds tem {len(seeds)} valor(es), mas --num-mazes={args.num_mazes}. "
                         f"A quantidade de seeds deve ser igual à quantidade de labirintos "
                         f"(ajuste um dos dois, ou omita --seeds para gerar automaticamente).")
    else:
        seeds = list(range(args.num_mazes))

    return args.size, args.obstacle_prob, args.num_mazes, seeds


def run_single(env, fn):
    t0 = time.perf_counter()
    result = fn(env)
    result["time_ms"] = (time.perf_counter() - t0) * 1000
    return result


def main(maze_size=15, obstacle_prob=0.28, num_mazes=10, seeds=None):
    """Roda o protocolo de avaliação. Os parâmetros têm os mesmos valores
    padrão usados nos testes originais do projeto, então chamar main()
    sem argumentos reproduz exatamente os resultados já validados."""
    if seeds is None:
        seeds = list(range(num_mazes))

    results = {name: [] for name in AGENT_FUNCS}

    for seed in seeds:
        env = MazeEnv(size=maze_size, obstacle_prob=obstacle_prob, seed=seed)
        for name, fn in AGENT_FUNCS.items():
            r = run_single(env, fn)
            results[name].append(r)

    print("=" * 70)
    print(f"Protocolo de avaliação — {num_mazes} labirintos {maze_size}x{maze_size}, "
          f"obstacle_prob={obstacle_prob}, seeds={seeds}")
    print("=" * 70)
    header = f"{'Agente':<10}{'Sucesso':<10}{'Custo médio':<14}{'Nós expandidos (média)':<24}{'Tempo médio (ms)':<18}"
    print(header)
    print("-" * len(header))

    summary = {}

    for name, runs in results.items():
        successes = [r for r in runs if r["success"]]
        success_rate = len(successes) / len(runs) * 100
        avg_cost = stats.mean(r["cost"] for r in successes) if successes else float("nan")
        avg_nodes = stats.mean(r["nodes_expanded"] for r in runs)
        avg_time = stats.mean(r["time_ms"] for r in runs)
        print(f"{name:<10}{success_rate:<10.1f}{avg_cost:<14.2f}{avg_nodes:<24.2f}{avg_time:<18.3f}")
        summary[name] = {"cost": avg_cost, "nodes": avg_nodes, "time": avg_time}

    print("\nConclusão esperada: BFS e A* encontram o caminho de custo mínimo "
          "(mesmo custo médio), mas A* expande menos nós que o BFS por usar "
          "a heurística de Manhattan para guiar a busca. O Greedy expande "
          "poucos nós, mas pode gerar caminhos sub-ótimos (custo maior) ou "
          "falhar ao ficar preso em becos sem saída, pois ignora o custo já "
          "percorrido.")

    # --- Evidência visual (itens 5 e 10) --------------------------------
    demo_env = MazeEnv(size=maze_size, obstacle_prob=obstacle_prob, seed=seeds[0])

    greedy_r = greedy_best_first_search(demo_env)
    astar_r = astar_search(demo_env)
    bfs_r = bfs_search(demo_env)

    render_maze(demo_env, path=greedy_r["path"],
                title=f"Greedy Best-First (ingênuo) — seed={seeds[0]}, custo={greedy_r['cost']}, nós={greedy_r['nodes_expanded']}",
                save_path="output_greedy.png")
    render_maze(demo_env, path=astar_r["path"],
                title=f"A* (final) — seed={seeds[0]}, custo={astar_r['cost']}, nós={astar_r['nodes_expanded']}",
                save_path="output_astar.png")
    render_maze(demo_env, path=bfs_r["path"],
                title=f"BFS (referência) — seed={seeds[0]}, custo={bfs_r['cost']}, nós={bfs_r['nodes_expanded']}",
                save_path="output_bfs.png")

    print("\nImagens salvas: output_greedy.png, output_astar.png, output_bfs.png "
          f"(labirinto de demonstração: seed={seeds[0]})")

    # --- Gráfico comparativo (custo, nós expandidos, tempo) --------------
    plot_comparison(summary, save_path="comparison_chart.png")
    print("Gráfico comparativo salvo: comparison_chart.png")


if __name__ == "__main__":
    size, obstacle_prob, num_mazes, seeds = parse_args()
    main(maze_size=size, obstacle_prob=obstacle_prob, num_mazes=num_mazes, seeds=seeds)
