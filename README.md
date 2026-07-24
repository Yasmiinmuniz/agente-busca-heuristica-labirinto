# Agente de Busca Heurística em Labirinto (A*)

Estudo Dirigido — IA 2026.1
Integrante: Yasmin da Silva Muniz

## 1. Contexto e objetivo

Contexto I — Ambiente próprio. Foi desenvolvido um ambiente de labirinto em
grade (grid NxN) no qual um agente deve encontrar o caminho de menor custo
entre a posição inicial e a posição objetivo, desviando de obstáculos.

Foram implementados três agentes de busca no espaço de estados, para permitir
comparação teórica e empírica:

| Agente | Tipo | Papel no projeto |
|---|---|---|
| BFS | busca não-informada | referência / baseline (custo mínimo garantido) |
| Greedy Best-First | busca informada (só heurística) | versão "ingênua" inicial, mostra falhas/sub-otimalidade |
| **A\*** | busca informada (custo + heurística) | agente final, robusto e ótimo |

## 2. Ambiente (`maze_env.py`)

- **Estado**: posição `(linha, coluna)` do agente na grade.
- **Ações**: `CIMA`, `BAIXO`, `ESQUERDA`, `DIREITA`.
- **Recompensa**: -1 por passo, -10 ao colidir com obstáculo/borda, +100 ao
  atingir o objetivo (o ambiente expõe uma interface `reset()`/`step()` no
  estilo Gym, deixando explícitos estado, ação e recompensa, mesmo a busca
  sendo feita sobre o modelo do ambiente).
- **Término**: chegada ao destino (sucesso) ou número de passos excede
  `max_steps` (timeout/falha).
- O labirinto é gerado aleatoriamente (com seed) e há verificação de que
  existe pelo menos um caminho válido entre início e fim.

## 3. Agentes (`agents.py`)

Formulação computacional comum:

- **Estado**: posição na grade.
- **Ações**: 4 movimentos ortogonais.
- **Objetivo**: estado == posição de destino.
- **Custo `g(n)`**: 1 por movimento.
- **Heurística `h(n)`**: distância de Manhattan até o destino (admissível
  para movimentos ortogonais de custo unitário, o que garante otimalidade
  do A*).
- `f(n) = g(n) + h(n)` no A*; `f(n) = h(n)` no Greedy; ordem FIFO no BFS.

## 4. Como instalar

```bash
git clone <https://github.com/Yasmiinmuniz/agente-busca-heuristica-labirinto.git>
cd <agente-busca-heuristica-labirinto>
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 5. Como executar

Rodar o protocolo de avaliação completo (10 labirintos, 3 agentes, métricas
comparativas e imagens do resultado):

```bash
python run_experiment.py
```

Saída esperada no terminal: tabela com taxa de sucesso, custo médio, nós
expandidos e tempo médio por agente. Também são salvas três imagens:
`output_bfs.png`, `output_greedy.png`, `output_astar.png`, mostrando o
labirinto e o caminho encontrado por cada agente.

Para gerar e visualizar um labirinto único em modo texto (debug rápido):

```python
from maze_env import MazeEnv
from agents import astar_search

env = MazeEnv(size=10, obstacle_prob=0.25, seed=42)
result = astar_search(env)
print(env.render_ascii(path=result["path"]))
print("Custo:", result["cost"], "| Nós expandidos:", result["nodes_expanded"])
```

## 6. Protocolo de avaliação e métricas

- **N execuções**: 10 labirintos gerados com seeds diferentes (mesmo
  tamanho e densidade de obstáculos), para reduzir viés de instância única.
- **Métricas**: taxa de sucesso, custo médio do caminho, nós expandidos
  (eficiência da busca) e tempo médio de execução.
- **Comparação com referência**: BFS (busca não-informada) é usado como
  baseline de custo mínimo garantido. A* deve igualar o custo do BFS
  expandindo menos nós. Greedy expande ainda menos nós, mas pode gerar
  custo maior (sub-ótimo).

## 7. Limitações e possibilidades de melhoria

- O ambiente assume observabilidade total (o agente "vê" o mapa inteiro
  para planejar); uma extensão natural seria observação parcial (sensor de
  vizinhança) com replanejamento.
- A geração aleatória de obstáculos não garante controle fino de
  dificuldade; poderia ser substituída por geração via DFS/backtracking
  para labirintos "perfeitos" (um único caminho).
- Não há tratamento de custo de movimento diferenciado (ex.: diagonais,
  terrenos com custo variável).

## 8. Uso de IA generativa

O Claude (Anthropic) foi utilizado para: (1) comparar os contextos do
roteiro do estudo dirigido e ajudar a estruturar o plano inicial; (2) gerar
a implementação inicial do ambiente, dos agentes de busca e do script de
comparação de métricas, a partir da especificação definida pela dupla.
Todo o código foi executado, testado e revisado pela integrante antes da
entrega — a formulação de estado/ação/heurística/recompensa e a escolha dos
três agentes comparativos foram decisões da desenvolvedora, validadas com base na
teoria estudada em sala.

## 9. Estrutura de arquivos

```
maze_env.py         # ambiente (grid, estado, ações, recompensa, término)
agents.py           # BFS, Greedy Best-First e A*
visualize.py        # renderização do labirinto e do caminho em PNG
run_experiment.py   # protocolo de avaliação, métricas e geração de imagens
requirements.txt
README.md
```
