import pygame
import random
import sys
import os
import math
import argparse
import csv
from datetime import datetime

from agente import carregar_melhor_agente  # usa melhor_agente.json quando --play-best

# =============================
# CONFIGURAÇÕES
# =============================
LARGURA, ALTURA = 800, 600
FPS = 60

# Cores (fallback quando não houver sprites)
BG_COR = (18, 22, 28)
HUD = (235, 235, 235)
JOGADOR_COR = (64, 160, 255)
MOEDA_COR = (255, 215, 0)
OBS_COR = (255, 80, 80)
SOMBRA = (0, 0, 0)

# Jogador
JOGADOR_W, JOGADOR_H = 48, 48
VEL_JOGADOR_BASE = 6.0  # pode ser sobrescrito quando --play-best (pelo JSON)

# Moedas (retângulo de colisão continua igual; só aumentamos o desenho)
RAIO_MOEDA = 10                  # colisão
QTD_MOEDAS = 7
COIN_BASE_SIZE = 25              # tamanho base da sprite carregada
COIN_ROT_SPEED = 180.0           # graus/seg
COIN_PULSE_SPEED = 4.0           # Hz ~ “batimento”
COIN_PULSE_MIN_SCALE = 1.25      # escala base maior (moeda “aumentada”)
COIN_PULSE_AMP = 0.12            # amplitude do pulso (+-)

# Obstáculos
OBS_W, OBS_H = 80, 40
QTD_OBS_INICIAL = 4
VEL_OBS_BASE = 4
QTD_OBS_MAX = 10

# Tempo
TEMPO_MAX_SEG = 60

# Persistência
ARQUIVO_SCORE = "score.txt"
ARQUIVO_CSV = "placar.csv"   # placar por partida
ARQ_MELHOR = "melhor_agente.json"  # usado para ajustar vel_jogador no modo play-best

# Caminhos de assets (opcionais)
ASSETS_DIR = "assets"
PATH_BG = os.path.join(ASSETS_DIR, "bg.png")
PATH_PLAYER = os.path.join(ASSETS_DIR, "player.png")
PATH_COIN = os.path.join(ASSETS_DIR, "coin.png")
PATH_OBS = os.path.join(ASSETS_DIR, "obstacle.png")

# Estados
ESTADO_MENU = "menu"
ESTADO_JOGANDO = "jogando"
ESTADO_PAUSA = "pausa"
ESTADO_GAMEOVER = "gameover"

# =============================
# CSV / Placar
# =============================
def init_csv(caminho=ARQUIVO_CSV):
    if not os.path.exists(caminho):
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["nome", "pontos", "data_hora"])

def registrar_placar(nome, pontos, caminho=ARQUIVO_CSV):
    init_csv(caminho)
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([nome, int(pontos), agora])
    print(f"[PLACAR] nome={nome} pontos={pontos} data_hora={agora}")

# =============================
# HELPERS
# =============================
def fonte(tam, negrito=True):
    return pygame.font.SysFont(None, tam, bold=negrito)

def desenhar_texto(surface, txt, tam, cor, x, y, centro=False):
    f = fonte(tam)
    img = f.render(txt, True, cor)
    r = img.get_rect()
    if centro:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    surface.blit(img, r)

def sombra_texto(surface, txt, tam, x, y, cor=HUD, dx=2, dy=2, centro=False):
    desenhar_texto(surface, txt, tam, SOMBRA, x+dx, y+dy, centro)
    desenhar_texto(surface, txt, tam, cor, x, y, centro)

def criar_moedas():
    moedas = []
    for _ in range(QTD_MOEDAS):
        x = random.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10) - RAIO_MOEDA
        y = random.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10) - RAIO_MOEDA
        moedas.append(pygame.Rect(x, y, RAIO_MOEDA*2, RAIO_MOEDA*2))
    return moedas

def criar_obstaculos(qtd, vel_base):
    obs = []
    for i in range(qtd):
        x = random.randint(0, LARGURA - OBS_W)
        y = random.randint(60, ALTURA - 60)
        rect = pygame.Rect(x, y, OBS_W, OBS_H)
        velx = vel_base if i % 2 == 0 else -vel_base
        obs.append({"rect": rect, "velx": velx})
    return obs

def load_image(path, size=None):
    try:
        if not os.path.exists(path):
            return None
        img = pygame.image.load(path).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None

def carregar_recorde():
    try:
        if os.path.exists(ARQUIVO_SCORE):
            with open(ARQUIVO_SCORE, "r", encoding="utf-8") as f:
                return int(f.read().strip() or "0")
    except Exception:
        pass
    return 0

def salvar_recorde(valor):
    try:
        with open(ARQUIVO_SCORE, "w", encoding="utf-8") as f:
            f.write(str(int(valor)))
    except Exception:
        pass

def _carregar_vel_playbest(default_vel):
    # Se existir JSON do melhor agente, use a velocidade evoluída
    try:
        import json
        if os.path.exists(ARQ_MELHOR):
            with open(ARQ_MELHOR, "r", encoding="utf-8") as f:
                data = json.load(f)
                return float(data.get("vel_jogador", default_vel))
    except Exception:
        pass
    return default_vel

# =============================
# JOGO
# =============================
def main(play_best=False, nome_jogador="Jogador"):
    pygame.init()
    pygame.display.set_caption("Coleta & Desvio (AG)")
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    clock = pygame.time.Clock()

    bg_img = load_image(PATH_BG, (LARGURA, ALTURA))
    player_img = load_image(PATH_PLAYER, (JOGADOR_W, JOGADOR_H))
    # Carrega sprite base da moeda (vamos rotacionar e pulsar no desenho)
    coin_base_img = load_image(PATH_COIN, (COIN_BASE_SIZE, COIN_BASE_SIZE))
    obs_img = load_image(PATH_OBS, (OBS_W, OBS_H))

    recorde = carregar_recorde()

    estado = ESTADO_JOGANDO if play_best else ESTADO_MENU
    pontuacao = 0
    tempo = 0.0

    jogador = pygame.Rect(LARGURA//2 - JOGADOR_W//2, ALTURA//2 - JOGADOR_H//2, JOGADOR_W, JOGADOR_H)
    jx, jy = float(jogador.x), float(jogador.y)
    vel_jogador = VEL_JOGADOR_BASE
    if play_best:
        vel_jogador = _carregar_vel_playbest(vel_jogador)

    moedas = criar_moedas()
    vel_obs = VEL_OBS_BASE
    obstaculos = criar_obstaculos(QTD_OBS_INICIAL, vel_obs)

    proximo_marco = 10

    # --- animação de dano (flash) ---
    flash_t = 0.0
    FLASH_DUR = 0.15

    # --- animação das moedas ---
    coin_angle = 0.0
    coin_pulse_t = 0.0

    # AGENTE (se play_best)
    agente = carregar_melhor_agente() if play_best else None

    # CSV placar
    init_csv()

    rodando = True
    while rodando:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False

            if estado == ESTADO_MENU and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    estado = ESTADO_JOGANDO  # manual
                    pontuacao = 0
                    tempo = 0.0
                    proximo_marco = 10
                    vel_obs = VEL_OBS_BASE
                    jogador.topleft = (LARGURA//2 - JOGADOR_W//2, ALTURA//2 - JOGADOR_H//2)
                    jx, jy = float(jogador.x), float(jogador.y)
                    moedas = criar_moedas()
                    obstaculos = criar_obstaculos(QTD_OBS_INICIAL, vel_obs)
                    agente = None
                    flash_t = 0.0
                    vel_jogador = VEL_JOGADOR_BASE
                    # reset animação das moedas
                    coin_angle = 0.0
                    coin_pulse_t = 0.0
                if event.key == pygame.K_ESCAPE:
                    rodando = False

            if estado == ESTADO_GAMEOVER and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    estado = ESTADO_JOGANDO if play_best else ESTADO_MENU
                    pontuacao = 0
                    tempo = 0.0
                    proximo_marco = 10
                    vel_obs = VEL_OBS_BASE
                    jogador.topleft = (LARGURA//2 - JOGADOR_W//2, ALTURA//2 - JOGADOR_H//2)
                    jx, jy = float(jogador.x), float(jogador.y)
                    moedas = criar_moedas()
                    obstaculos = criar_obstaculos(QTD_OBS_INICIAL, vel_obs)
                    agente = carregar_melhor_agente() if play_best else None
                    flash_t = 0.0
                    vel_jogador = _carregar_vel_playbest(VEL_JOGADOR_BASE) if play_best else VEL_JOGADOR_BASE
                    # reset animação das moedas
                    coin_angle = 0.0
                    coin_pulse_t = 0.0
                if event.key == pygame.K_ESCAPE:
                    rodando = False

            if estado == ESTADO_JOGANDO and event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                estado = ESTADO_PAUSA
            elif estado == ESTADO_PAUSA and event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                estado = ESTADO_JOGANDO

        # ----------- LÓGICA -----------
        if estado == ESTADO_JOGANDO:
            tempo += dt
            if tempo >= TEMPO_MAX_SEG:
                estado = ESTADO_GAMEOVER
                if pontuacao > recorde:
                    recorde = pontuacao
                    salvar_recorde(recorde)
                registrar_placar(nome_jogador, pontuacao)

            if estado == ESTADO_JOGANDO:
                if tempo >= proximo_marco:
                    proximo_marco += 10
                    vel_obs += 0.8
                    for o in obstaculos:
                        o["velx"] = (vel_obs if o["velx"] > 0 else -vel_obs)
                    if len(obstaculos) < QTD_OBS_MAX:
                        obstaculos += criar_obstaculos(1, vel_obs)

                # movimento
                if agente is not None:
                    vx, vy = agente.decidir(jogador, moedas, [o["rect"] for o in obstaculos])
                    if vx == 0.0 and vy == 0.0:
                        vx = 1.0
                    jx += vx * vel_jogador
                    jy += vy * vel_jogador
                else:
                    teclas = pygame.key.get_pressed()
                    dx = dy = 0.0
                    if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:   dx -= vel_jogador
                    if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:  dx += vel_jogador
                    if teclas[pygame.K_UP] or teclas[pygame.K_w]:     dy -= vel_jogador
                    if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:   dy += vel_jogador
                    jx += dx
                    jy += dy

                jx = max(0.0, min(LARGURA - JOGADOR_W, jx))
                jy = max(0.0, min(ALTURA - JOGADOR_H, jy))
                jogador.x = int(round(jx))
                jogador.y = int(round(jy))

                for o in obstaculos:
                    o["rect"].x += o["velx"]
                    if o["rect"].left <= 0 or o["rect"].right >= LARGURA:
                        o["velx"] *= -1

                # colisões
                for o in obstaculos:
                    if jogador.colliderect(o["rect"]):
                        pontuacao = max(0, pontuacao - 2)
                        flash_t = FLASH_DUR

                for m in moedas:
                    if jogador.colliderect(m):
                        pontuacao += 1
                        m.x = random.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10) - RAIO_MOEDA
                        m.y = random.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10) - RAIO_MOEDA

                if flash_t > 0.0:
                    flash_t = max(0.0, flash_t - dt)

                # animação das moedas
                coin_angle = (coin_angle + COIN_ROT_SPEED * dt) % 360.0
                coin_pulse_t += dt

        # ----------- DESENHO -----------
        if bg_img:
            tela.blit(bg_img, (0, 0))
        else:
            tela.fill(BG_COR)

        if estado in (ESTADO_JOGANDO, ESTADO_PAUSA, ESTADO_GAMEOVER):
            # desenhar moedas com rotação + pulso, centralizando no rect da colisão
            for m in moedas:
                if coin_base_img:
                    scale = COIN_PULSE_MIN_SCALE + COIN_PULSE_AMP * math.sin(coin_pulse_t * COIN_PULSE_SPEED)
                    coin_scaled = pygame.transform.rotozoom(coin_base_img, coin_angle, scale)
                    rect_img = coin_scaled.get_rect(center=(m.centerx, m.centery))
                    tela.blit(coin_scaled, rect_img.topleft)
                else:
                    pygame.draw.circle(tela, MOEDA_COR, (m.centerx, m.centery), int(RAIO_MOEDA * 1.4))

            for o in obstaculos:
                if obs_img:
                    tela.blit(obs_img, (o["rect"].x, o["rect"].y))
                else:
                    pygame.draw.rect(tela, OBS_COR, o["rect"])

            if player_img:
                tela.blit(player_img, (jogador.x, jogador.y))
            else:
                pygame.draw.rect(tela, JOGADOR_COR, jogador)

            if (estado == ESTADO_JOGANDO) and (flash_t > 0.0):
                overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                alpha = int(180 * (flash_t / FLASH_DUR))
                overlay.fill((255, 50, 50, alpha))
                tela.blit(overlay, (0, 0))

            tempo_rest = 0 if estado == ESTADO_GAMEOVER else max(0, int(TEMPO_MAX_SEG - tempo))
            sombra_texto(tela, f"Pontos: {pontuacao}", 28, 12, 10)
            sombra_texto(tela, f"Tempo: {tempo_rest}s", 28, 12, 42)
            sombra_texto(tela, f"Recorde: {recorde}", 28, LARGURA-12-160, 10)

            if play_best and estado != ESTADO_MENU:
                desenhar_texto(tela, "AGENTE: ON (--play-best)", 20, (200, 230, 255), 12, 74)

        if estado == ESTADO_MENU:
            sombra_texto(tela, "COLETA & DESVIO (AG)", 72, LARGURA//2, ALTURA//2 - 80, centro=True)
            desenhar_texto(tela, "Colete moedas, desvie dos obstáculos e faça pontos em 60s!", 26, HUD, LARGURA//2, ALTURA//2 - 10, centro=True)
            desenhar_texto(tela, "ENTER/ESPAÇO para jogar (manual) | ESC para sair", 22, HUD, LARGURA//2, ALTURA//2 + 40, centro=True)
            desenhar_texto(tela, "Dica: rode 'genetico.py' para evoluir e depois use --play-best", 20, (180, 220, 255), LARGURA//2, ALTURA//2 + 80, centro=True)

        elif estado == ESTADO_GAMEOVER:
            sombra_texto(tela, "FIM DE JOGO!", 64, LARGURA//2, ALTURA//2 - 60, centro=True)
            desenhar_texto(tela, f"Pontuação: {pontuacao}", 30, HUD, LARGURA//2, ALTURA//2 - 10, centro=True)
            desenhar_texto(tela, "R para reiniciar | ESC para sair", 24, HUD, LARGURA//2, ALTURA//2 + 70, centro=True)
            desenhar_texto(tela, "Placar salvo em 'placar.csv'", 20, (180, 220, 255), LARGURA//2, ALTURA//2 + 110, centro=True)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--play-best", action="store_true",
                        help="Inicia o jogo com o agente treinado (pula o menu).")
    parser.add_argument("--nome", type=str, default="Jogador",
                        help="Nome do jogador (usado no placar.csv)")
    args = parser.parse_args()

    if args.play_best:
        print("[INFO] Modo --play-best ATIVO (usa melhor_agente.json).")
    else:
        print("[INFO] Modo manual. Dica: execute 'python genetico.py' para treinar o agente.")

    main(play_best=args.play_best, nome_jogador=args.nome)
