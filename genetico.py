# genetico.py
import os
import random
import math
import json
import csv
import argparse
import pygame

# ----------------- Ambiente (alinhado com main.py) -----------------
LARGURA, ALTURA = 800, 600
JOGADOR_W, JOGADOR_H = 48, 48
RAIO_MOEDA = 10
QTD_MOEDAS = 7
OBS_W, OBS_H = 80, 20
QTD_OBS_INICIAL = 4
QTD_OBS_MAX = 10

# Simulação headless (rápida)
STEPS_POR_AVALIACAO = 600   # ~ 60s com dt=0.1
DT = 0.1
VEL_OBS_BASE = 4.0

# Espaço de genes
ALC_MIN, ALC_MAX = 60.0, 200.0
PESO_MIN, PESO_MAX = 0.3, 3.0
VEL_MIN, VEL_MAX = 4.0, 9.0

ARQ_MELHOR = "melhor_agente.json"
ARQ_EVOLUCAO = "evolucao.csv"

# ----------------- Utils numéricos -----------------
def _norm(vx, vy):
    m = math.hypot(vx, vy)
    if m == 0.0:
        return 0.0, 0.0
    return vx / m, vy / m

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _moeda_alvo(px, py, moedas):
    if not moedas:
        return None
    return min(moedas, key=lambda m: math.hypot(px - (m.x + RAIO_MOEDA), py - (m.y + RAIO_MOEDA)))

def criar_moedas(rng):
    moedas = []
    for _ in range(QTD_MOEDAS):
        x = rng.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10) - RAIO_MOEDA
        y = rng.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10) - RAIO_MOEDA
        moedas.append(pygame.Rect(x, y, RAIO_MOEDA*2, RAIO_MOEDA*2))
    return moedas

def criar_obstaculos(qtd, vel_base, rng):
    obs = []
    for i in range(qtd):
        x = rng.randint(0, LARGURA - OBS_W)
        y = rng.randint(60, ALTURA - 60)
        rect = pygame.Rect(x, y, OBS_W, OBS_H)
        velx = vel_base if (i % 2 == 0) else -vel_base
        obs.append({"rect": rect, "velx": velx})
    return obs

def step_ambiente(jx, jy, vel_jogador, moedas, obstaculos, alc, peso, rng):
    # direção para moeda
    px, py = jx + JOGADOR_W / 2, jy + JOGADOR_H / 2
    alvo = _moeda_alvo(px, py, moedas)
    if alvo:
        tx, ty = (alvo.x + RAIO_MOEDA) - px, (alvo.y + RAIO_MOEDA) - py
        ax, ay = _norm(tx, ty)
    else:
        ax, ay = 0.0, 0.0

    # repulsão de obstáculos
    rx, ry = 0.0, 0.0
    for o in obstaculos:
        rect = o["rect"]
        qx = _clamp(px, rect.left, rect.right)
        qy = _clamp(py, rect.top, rect.bottom)
        d = math.hypot(px - qx, py - qy)
        if 0.0 < d < alc:
            f = (alc - d) / alc
            nx, ny = _norm(px - qx, py - qy)
            rx += nx * f
            ry += ny * f
    mag = math.hypot(rx, ry)
    if mag > 1.0:
        rx, ry = rx / mag, ry / mag

    vx, vy = ax + rx * peso, ay + ry * peso
    vx, vy = _norm(vx, vy)
    if vx == 0.0 and vy == 0.0:
        vx = 1.0  # fallback

    # move jogador
    jx += vx * vel_jogador
    jy += vy * vel_jogador
    jx = _clamp(jx, 0.0, LARGURA - JOGADOR_W)
    jy = _clamp(jy, 0.0, ALTURA - JOGADOR_H)
    jrect = pygame.Rect(int(jx), int(jy), JOGADOR_W, JOGADOR_H)

    # move obstáculos
    for o in obstaculos:
        o["rect"].x += o["velx"]
        if o["rect"].left <= 0 or o["rect"].right >= LARGURA:
            o["velx"] *= -1

    # recompensa
    reward = 0
    for m in moedas:
        if jrect.colliderect(m):
            reward += 1
            m.x = rng.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10) - RAIO_MOEDA
            m.y = rng.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10) - RAIO_MOEDA
    for o in obstaculos:
        if jrect.colliderect(o["rect"]):
            reward -= 2

    return jx, jy, moedas, obstaculos, reward

# ----------------- AG -----------------
def cromossomo_aleatorio(rng):
    return {
        "alcance_repulsao": rng.uniform(ALC_MIN, ALC_MAX),
        "peso_repulsao": rng.uniform(PESO_MIN, PESO_MAX),
        "vel_jogador": rng.uniform(VEL_MIN, VEL_MAX)
    }

def limitar_genes(g):
    g["alcance_repulsao"] = _clamp(g["alcance_repulsao"], ALC_MIN, ALC_MAX)
    g["peso_repulsao"] = _clamp(g["peso_repulsao"], PESO_MIN, PESO_MAX)
    g["vel_jogador"] = _clamp(g["vel_jogador"], VEL_MIN, VEL_MAX)
    return g

def fitness_do_cromossomo(g, seed_base=0):
    rng = random.Random(seed_base)
    jx = LARGURA/2 - JOGADOR_W/2
    jy = ALTURA/2 - JOGADOR_H/2
    moedas = criar_moedas(rng)
    obstaculos = criar_obstaculos(QTD_OBS_INICIAL, VEL_OBS_BASE, rng)
    vel_obs = VEL_OBS_BASE
    proximo_marco = 10.0
    tempo = 0.0
    pontuacao = 0

    for _ in range(STEPS_POR_AVALIACAO):
        jx, jy, moedas, obstaculos, reward = step_ambiente(
            jx, jy, g["vel_jogador"], moedas, obstaculos,
            g["alcance_repulsao"], g["peso_repulsao"], rng
        )
        pontuacao += reward
        tempo += DT
        if tempo >= proximo_marco:
            proximo_marco += 10.0
            vel_obs += 0.8
            for o in obstaculos:
                o["velx"] = (vel_obs if o["velx"] > 0 else -vel_obs)
            if len(obstaculos) < QTD_OBS_MAX:
                obstaculos += criar_obstaculos(1, vel_obs, rng)

    return pontuacao

def selecao(pop, k_elite):
    pop_ordenada = sorted(pop, key=lambda x: x[1], reverse=True)
    elite = pop_ordenada[:k_elite]
    return elite, pop_ordenada[0]

def cruzar(g1, g2, rng):
    a = rng.random()
    return {
        "alcance_repulsao": a * g1["alcance_repulsao"] + (1-a) * g2["alcance_repulsao"],
        "peso_repulsao": a * g1["peso_repulsao"] + (1-a) * g2["peso_repulsao"],
        "vel_jogador": a * g1["vel_jogador"] + (1-a) * g2["vel_jogador"],
    }

def mutar(g, rng, taxa=0.3, sigma_rel=0.12):
    if rng.random() < taxa:
        g["alcance_repulsao"] += rng.gauss(0, (ALC_MAX-ALC_MIN) * sigma_rel)
    if rng.random() < taxa:
        g["peso_repulsao"] += rng.gauss(0, (PESO_MAX-PESO_MIN) * sigma_rel * 0.5)
    if rng.random() < taxa:
        g["vel_jogador"] += rng.gauss(0, (VEL_MAX-VEL_MIN) * sigma_rel)
    return limitar_genes(g)

# ----------------- Plot helpers (interativo, suave e animação) -----------------
def _moving_average(vals, k):
    if k <= 1 or not vals:
        return vals[:]
    out = []
    s = 0.0
    q = []
    for v in vals:
        q.append(v)
        s += v
        if len(q) > k:
            s -= q.pop(0)
        out.append(s / len(q))
    return out

def _plotar_estatico(csv_path, smooth=0):
    try:
        import matplotlib
        backend = matplotlib.get_backend().lower()
        if any(b in backend for b in ["agg", "pdf", "svg", "ps", "cairo"]):
            for bk in ["TkAgg", "Qt5Agg", "QtAgg", "WXAgg", "GTK3Agg"]:
                try:
                    matplotlib.use(bk, force=True)
                    break
                except Exception:
                    continue
        import matplotlib.pyplot as plt
    except Exception as e:
        print(f"[AVISO] matplotlib interativo indisponível: {e}")
        print("Instale um backend (tkinter/pyqt5/wxPython).")
        return

    if not os.path.exists(csv_path):
        print(f"[AVISO] '{csv_path}' não encontrado.")
        return

    ger, bests, meds = [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                ger.append(int(row["geracao"]))
                bests.append(float(row["melhor_fitness"]))
                meds.append(float(row["media_fitness"]))
            except Exception:
                pass

    if not ger:
        print("[AVISO] CSV vazio; gráfico não gerado.")
        return

    bests_s = _moving_average(bests, smooth)
    meds_s  = _moving_average(meds, smooth)

    import matplotlib.pyplot as plt
    plt.figure(figsize=(9,5))
    plt.plot(ger, bests, label="Melhor Fitness", alpha=0.35)
    plt.plot(ger, meds,  label="Média Fitness",  alpha=0.35)
    if smooth and smooth > 1:
        plt.plot(ger, bests_s, label=f"Melhor (média móvel k={smooth})")
        plt.plot(ger, meds_s,  label=f"Média (média móvel k={smooth})")
    plt.title("Evolução do Fitness por Geração")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    print("[GRÁFICO] Exibindo janela (feche para continuar)...")
    plt.show()

def _plotar_animado(csv_path, smooth=0, interval_ms=200):
    try:
        import matplotlib
        backend = matplotlib.get_backend().lower()
        if any(b in backend for b in ["agg", "pdf", "svg", "ps", "cairo"]):
            for bk in ["TkAgg", "Qt5Agg", "QtAgg", "WXAgg", "GTK3Agg"]:
                try:
                    matplotlib.use(bk, force=True)
                    break
                except Exception:
                    continue
        import matplotlib.pyplot as plt
        from matplotlib.animation import FuncAnimation
    except Exception as e:
        print(f"[AVISO] matplotlib interativo indisponível: {e}")
        return

    if not os.path.exists(csv_path):
        print(f"[AVISO] '{csv_path}' não encontrado.")
        return

    ger, bests, meds = [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                ger.append(int(row["geracao"]))
                bests.append(float(row["melhor_fitness"]))
                meds.append(float(row["media_fitness"]))
            except Exception:
                pass

    if not ger:
        print("[AVISO] CSV vazio; gráfico não gerado.")
        return

    fig, ax = plt.subplots(figsize=(9,5))
    ax.set_title("Evolução do Fitness por Geração (Animação)")
    ax.set_xlabel("Geração")
    ax.set_ylabel("Fitness")
    ax.grid(True, alpha=0.3)

    (ln_best,) = ax.plot([], [], label="Melhor Fitness")
    (ln_mean,) = ax.plot([], [], label="Média Fitness")
    if smooth and smooth > 1:
        (ln_best_s,) = ax.plot([], [], label=f"Melhor (média móvel k={smooth})")
        (ln_mean_s,) = ax.plot([], [], label=f"Média (média móvel k={smooth})")
    else:
        ln_best_s = ln_mean_s = None

    ax.legend()
    ax.set_xlim(min(ger), max(ger))
    y_min = min(min(bests), min(meds))
    y_max = max(max(bests), max(meds))
    pad = max(5, (y_max - y_min) * 0.1)
    ax.set_ylim(y_min - pad, y_max + pad)

    def update(frame):
        g = ger[:frame+1]
        b = bests[:frame+1]
        m = meds[:frame+1]
        ln_best.set_data(g, b)
        ln_mean.set_data(g, m)
        if ln_best_s is not None:
            bs = _moving_average(b, smooth)
            ms = _moving_average(m, smooth)
            ln_best_s.set_data(g, bs)
            ln_mean_s.set_data(g, ms)
        return [ln_best, ln_mean] + ([ln_best_s, ln_mean_s] if ln_best_s else [])

    anim = FuncAnimation(fig, update, frames=len(ger), interval=interval_ms, blit=False, repeat=False)
    print("[ANIMAÇÃO] Exibindo janela (feche para continuar)...")
    plt.tight_layout()
    plt.show()

# ----------------- Evolução -----------------
def evoluir(geracoes=15, pop_size=40, seed=42, elitismo_frac=0.2, log_csv=ARQ_EVOLUCAO,
            smooth=0, animate=False):
    # modo headless para pygame
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()

    rng = random.Random(seed)
    k_elite = max(1, int(pop_size * elitismo_frac))

    # Reinicia CSV a cada treino (para gráfico apenas do treino atual)
    with open(log_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["geracao", "melhor_fitness", "media_fitness"])

    # População inicial
    populacao = [cromossomo_aleatorio(rng) for _ in range(pop_size)]
    melhor_global = None  # (genes, fitness)

    for gen in range(geracoes):
        aval = []
        seed_base = 1000 + gen
        for g in populacao:
            fit = fitness_do_cromossomo(g, seed_base=seed_base)
            aval.append((g, fit))

        elite, best = selecao(aval, k_elite)
        media = sum(f for _, f in aval) / len(aval)

        with open(log_csv, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([gen, best[1], media])

        if (melhor_global is None) or (best[1] > melhor_global[1]):
            melhor_global = best

        # próxima geração
        nova_pop = [e[0] for e in elite]  # elitismo
        while len(nova_pop) < pop_size:
            p1 = rng.choice(elite)[0]
            p2 = rng.choice(aval)[0]
            filho = cruzar(p1, p2, rng)
            filho = mutar(filho, rng, taxa=0.3, sigma_rel=0.12)
            nova_pop.append(limitar_genes(filho))
        populacao = nova_pop

        print(f"[GERAÇÃO {gen:02d}] melhor={best[1]:.2f} média={media:.2f} genes={best[0]}")

    # salva melhor global
    if melhor_global:
        genes, fit = melhor_global
        with open(ARQ_MELHOR, "w", encoding="utf-8") as f:
            json.dump({
                "alcance_repulsao": genes["alcance_repulsao"],
                "peso_repulsao": genes["peso_repulsao"],
                "vel_jogador": genes["vel_jogador"]
            }, f, ensure_ascii=False, indent=2)
        print(f"[SALVO] {ARQ_MELHOR} | melhor_fitness={fit:.2f} | genes={genes}")

    pygame.quit()

    # Gráfico pós-treino (estático ou animado)
    if animate:
        _plotar_animado(csv_path=log_csv, smooth=smooth, interval_ms=220)
    else:
        _plotar_estatico(csv_path=log_csv, smooth=smooth)

# ----------------- CLI -----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--geracoes", type=int, default=15, help="Número de gerações")
    parser.add_argument("--pop", type=int, default=40, help="Tamanho da população")
    parser.add_argument("--seed", type=int, default=42, help="Seed para reprodutibilidade")
    parser.add_argument("--smooth", type=int, default=0, help="Janela da média móvel (0 = sem suavizar)")
    parser.add_argument("--animate", action="store_true", help="Mostra animação da evolução ao invés de gráfico estático")
    args = parser.parse_args()

    evoluir(
        geracoes=args.geracoes,
        pop_size=args.pop,
        seed=args.seed,
        smooth=args.smooth,
        animate=args.animate
    )
