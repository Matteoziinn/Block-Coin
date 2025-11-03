import pygame
import random
import sys
import os
import math

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
VEL_JOGADOR_BASE = 6

# Moedas
RAIO_MOEDA = 10
QTD_MOEDAS = 7

# Obstáculos
OBS_W, OBS_H = 80, 20
QTD_OBS_INICIAL = 4
VEL_OBS_BASE = 4
QTD_OBS_MAX = 10

# Tempo
TEMPO_MAX_SEG = 60

# Arquivos persistência
ARQUIVO_SCORE = "score.txt"

# Caminhos de assets
ASSETS_DIR = "assets"
PATH_BG = os.path.join(ASSETS_DIR, "bg.png")
PATH_PLAYER = os.path.join(ASSETS_DIR, "player.png")
PATH_COIN = os.path.join(ASSETS_DIR, "coin.png")
PATH_OBS = os.path.join(ASSETS_DIR, "obstacle.png")
PATH_SFX_COIN = os.path.join(ASSETS_DIR, "sfx_coin.wav")
PATH_SFX_HIT = os.path.join(ASSETS_DIR, "sfx_hit.wav")
PATH_MUSIC = os.path.join(ASSETS_DIR, "music.ogg")

# Estados
ESTADO_MENU = "menu"
ESTADO_JOGANDO = "jogando"
ESTADO_PAUSA = "pausa"
ESTADO_GAMEOVER = "gameover"


# =============================
# UTILIDADES
# =============================
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
        x = random.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10)
        y = random.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10)
        moedas.append(pygame.Rect(x - RAIO_MOEDA, y - RAIO_MOEDA, RAIO_MOEDA*2, RAIO_MOEDA*2))
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
    """Carrega imagem com segurança. Retorna Surface ou None se falhar."""
    try:
        if not os.path.exists(path):
            return None
        img = pygame.image.load(path).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        return img
    except Exception:
        return None

def load_sound(path):
    """Carrega som com segurança. Retorna Sound ou None."""
    try:
        if not os.path.exists(path):
            return None
        return pygame.mixer.Sound(path)
    except Exception:
        return None


# =============================
# JOGO
# =============================
def main():
    # mixer pré-init para latência melhor (ignora se falhar)
    try:
        pygame.mixer.pre_init(44100, -16, 2, 256)
    except Exception:
        pass

    pygame.init()
    pygame.display.set_caption("Coleta & Desvio")
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    clock = pygame.time.Clock()

    # Carregar sprites e sons (com fallback)
    bg_img = load_image(PATH_BG, (LARGURA, ALTURA))
    player_img = load_image(PATH_PLAYER, (JOGADOR_W, JOGADOR_H))
    coin_base_img = load_image(PATH_COIN, (32, 32))  # base para animar
    obs_img = load_image(PATH_OBS, (OBS_W, OBS_H))

    sfx_coin = load_sound(PATH_SFX_COIN)
    sfx_hit = load_sound(PATH_SFX_HIT)

    # Música de fundo (opcional)
    try:
        if os.path.exists(PATH_MUSIC):
            pygame.mixer.music.load(PATH_MUSIC)
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)  # loop infinito
    except Exception:
        pass

    # Recorde
    recorde = carregar_recorde()

    # Estado inicial
    estado = ESTADO_MENU
    pontuacao = 0
    tempo = 0.0

    jogador = pygame.Rect(LARGURA//2 - JOGADOR_W//2, ALTURA//2 - JOGADOR_H//2, JOGADOR_W, JOGADOR_H)
    vel_jogador = VEL_JOGADOR_BASE
    moedas = criar_moedas()
    vel_obs = VEL_OBS_BASE
    obstaculos = criar_obstaculos(QTD_OBS_INICIAL, vel_obs)

    # Dificuldade
    proximo_marco = 10

    # Animação da moeda
    coin_angle = 0.0  # rotação
    coin_pulse_t = 0.0  # “pulso” leve de escala

    # Flash de dano
    flash_t = 0.0  # segundos restantes de flash

    rodando = True
    while rodando:
        dt = clock.tick(FPS) / 1000.0

        # ---------------------------
        # Eventos
        # ---------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                rodando = False

            if estado == ESTADO_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        estado = ESTADO_JOGANDO
                        # reset
                        pontuacao = 0
                        tempo = 0.0
                        proximo_marco = 10
                        vel_jogador = VEL_JOGADOR_BASE
                        vel_obs = VEL_OBS_BASE
                        jogador = pygame.Rect(LARGURA//2 - JOGADOR_W//2, ALTURA//2 - JOGADOR_H//2, JOGADOR_W, JOGADOR_H)
                        moedas = criar_moedas()
                        obstaculos = criar_obstaculos(QTD_OBS_INICIAL, vel_obs)
                        flash_t = 0.0
                        coin_angle = 0.0
                        coin_pulse_t = 0.0
                    elif event.key == pygame.K_ESCAPE:
                        rodando = False

            elif estado == ESTADO_JOGANDO:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    estado = ESTADO_PAUSA

            elif estado == ESTADO_PAUSA:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                    estado = ESTADO_JOGANDO

            elif estado == ESTADO_GAMEOVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        estado = ESTADO_MENU
                    elif event.key == pygame.K_ESCAPE:
                        rodando = False

        # ---------------------------
        # Lógica por estado
        # ---------------------------
        if estado == ESTADO_JOGANDO:
            tempo += dt
            if tempo >= TEMPO_MAX_SEG:
                estado = ESTADO_GAMEOVER
                if pontuacao > recorde:
                    recorde = pontuacao
                    salvar_recorde(recorde)

            # dificuldade progressiva
            if tempo >= proximo_marco and tempo < TEMPO_MAX_SEG:
                proximo_marco += 10
                vel_obs += 0.8
                for o in obstaculos:
                    o["velx"] = (vel_obs if o["velx"] > 0 else -vel_obs)
                if len(obstaculos) < QTD_OBS_MAX:
                    obstaculos += criar_obstaculos(1, vel_obs)

            # movimento jogador
            teclas = pygame.key.get_pressed()
            dx = dy = 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                dx -= vel_jogador
            if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                dx += vel_jogador
            if teclas[pygame.K_UP] or teclas[pygame.K_w]:
                dy -= vel_jogador
            if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
                dy += vel_jogador

            jogador.x += dx
            jogador.y += dy

            # limites
            if jogador.left < 0: jogador.left = 0
            if jogador.right > LARGURA: jogador.right = LARGURA
            if jogador.top < 0: jogador.top = 0
            if jogador.bottom > ALTURA: jogador.bottom = ALTURA

            # obsts ping-pong
            for o in obstaculos:
                o["rect"].x += o["velx"]
                if o["rect"].left <= 0 or o["rect"].right >= LARGURA:
                    o["velx"] *= -1

            # colisão com obstáculo -> -2 pontos e flash
            for o in obstaculos:
                if jogador.colliderect(o["rect"]):
                    if pontuacao > 0:
                        pontuacao = max(0, pontuacao - 2)
                    flash_t = 0.15  # 150ms de flash
                    if sfx_hit:
                        try: sfx_hit.play()
                        except Exception: pass

            # pegar moedas -> +1 e reposiciona
            for m in moedas:
                if jogador.colliderect(m):
                    pontuacao += 1
                    m.x = random.randint(RAIO_MOEDA + 10, LARGURA - RAIO_MOEDA - 10) - RAIO_MOEDA
                    m.y = random.randint(RAIO_MOEDA + 10, ALTURA - RAIO_MOEDA - 10) - RAIO_MOEDA
                    if sfx_coin:
                        try: sfx_coin.play()
                        except Exception: pass

            # animações
            coin_angle = (coin_angle + 180 * dt) % 360  # gira ~180º/seg
            coin_pulse_t += dt
            if flash_t > 0:
                flash_t -= dt

        # ---------------------------
        # Desenho
        # ---------------------------
        if bg_img:
            tela.blit(bg_img, (0, 0))
        else:
            tela.fill(BG_COR)

        if estado in (ESTADO_JOGANDO, ESTADO_PAUSA, ESTADO_GAMEOVER):
            # desenhar moedas (sprite com rotação + leve “pulso”)
            for m in moedas:
                if coin_base_img:
                    # pulso suave (escala entre 0.9 e 1.1)
                    scale = 1.0 + 0.1 * math.sin(coin_pulse_t * 4.0)
                    coin_scaled = pygame.transform.rotozoom(coin_base_img, coin_angle, scale)
                    rect_img = coin_scaled.get_rect(center=(m.centerx, m.centery))
                    tela.blit(coin_scaled, rect_img.topleft)
                else:
                    pygame.draw.circle(tela, MOEDA_COR, (m.x + RAIO_MOEDA, m.y + RAIO_MOEDA), RAIO_MOEDA)

            # obstáculos
            for o in obstaculos:
                if obs_img:
                    tela.blit(obs_img, (o["rect"].x, o["rect"].y))
                else:
                    pygame.draw.rect(tela, OBS_COR, o["rect"])

            # jogador
            if player_img:
                tela.blit(player_img, (jogador.x, jogador.y))
            else:
                pygame.draw.rect(tela, JOGADOR_COR, jogador)

            # flash de dano (breve overlay avermelhado)
            if flash_t > 0:
                overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
                alpha = int(180 * (flash_t / 0.15))  # desbota até 0
                overlay.fill((255, 50, 50, alpha))
                tela.blit(overlay, (0, 0))

            # HUD
            tempo_rest = max(0, int(TEMPO_MAX_SEG - tempo)) if estado != ESTADO_GAMEOVER else 0
            sombra_texto(tela, f"Pontos: {pontuacao}", 28, 12, 10)
            sombra_texto(tela, f"Tempo: {tempo_rest}s", 28, 12, 42)
            sombra_texto(tela, f"Recorde: {recorde}", 28, LARGURA-12-160, 10)  # pequena margem

            if estado == ESTADO_JOGANDO:
                desenhar_texto(tela, "P para pausar", 20, (200, 200, 200), LARGURA-160, 44)

        if estado == ESTADO_MENU:
            sombra_texto(tela, "COLETA & DESVIO", 72, LARGURA//2, ALTURA//2 - 80, centro=True)
            desenhar_texto(tela, "Colete moedas, desvie dos obstáculos e faça pontos em 60s!", 26, HUD, LARGURA//2, ALTURA//2 - 10, centro=True)
            desenhar_texto(tela, "ENTER/ESPAÇO para jogar | ESC para sair", 24, HUD, LARGURA//2, ALTURA//2 + 40, centro=True)
            desenhar_texto(tela, f"Recorde atual: {recorde}", 24, (180, 220, 255), LARGURA//2, ALTURA//2 + 90, centro=True)

        elif estado == ESTADO_PAUSA:
            sombra_texto(tela, "PAUSADO", 60, LARGURA//2, ALTURA//2 - 20, centro=True)
            desenhar_texto(tela, "Pressione P para continuar", 26, HUD, LARGURA//2, ALTURA//2 + 30, centro=True)

        elif estado == ESTADO_GAMEOVER:
            sombra_texto(tela, "FIM DE JOGO!", 64, LARGURA//2, ALTURA//2 - 60, centro=True)
            desenhar_texto(tela, f"Pontuação: {pontuacao}", 30, HUD, LARGURA//2, ALTURA//2 - 10, centro=True)
            if pontuacao >= recorde:
                desenhar_texto(tela, "Novo recorde!", 26, (255, 200, 60), LARGURA//2, ALTURA//2 + 26, centro=True)
            desenhar_texto(tela, "R para reiniciar | ESC para sair", 24, HUD, LARGURA//2, ALTURA//2 + 70, centro=True)

        pygame.display.flip()

    # fim do loop
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
