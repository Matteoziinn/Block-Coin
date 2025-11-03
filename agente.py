# agente.py
import json
import math
import os

ARQ_MELHOR = "melhor_agente.json"

def _norm(vx, vy):
    m = math.hypot(vx, vy)
    if m == 0.0:
        return 0.0, 0.0
    return vx / m, vy / m

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

class AgenteParametrico:
    """
    Agente controlado por parâmetros (genes):
    - alcance_repulsao: raio de influência de obstáculos
    - peso_repulsao: quanto a repulsão pesa vs. atração à moeda
    """
    def __init__(self, alcance_repulsao=120.0, peso_repulsao=1.2):
        self.alc = float(alcance_repulsao)
        self.peso = float(peso_repulsao)

    def _moeda_alvo(self, player_rect, moedas):
        if not moedas:
            return None
        px, py = player_rect.center
        return min(moedas, key=lambda m: math.hypot(px - m.centerx, py - m.centery))

    def _vet_atrair_moeda(self, player_rect, moedas):
        alvo = self._moeda_alvo(player_rect, moedas)
        if alvo is None:
            return 0.0, 0.0
        px, py = player_rect.center
        vx, vy = (alvo.centerx - px), (alvo.centery - py)
        return _norm(vx, vy)

    def _vet_repulsao(self, player_rect, obstaculos_rects):
        px, py = player_rect.center
        rx, ry = 0.0, 0.0
        for o in obstaculos_rects:
            qx = _clamp(px, o.left, o.right)
            qy = _clamp(py, o.top, o.bottom)
            d = math.hypot(px - qx, py - qy)
            if 0.0 < d < self.alc:
                f = (self.alc - d) / self.alc
                nx, ny = _norm(px - qx, py - qy)
                rx += nx * f
                ry += ny * f
        mag = math.hypot(rx, ry)
        if mag > 1.0:
            rx, ry = rx / mag, ry / mag
        return rx, ry

    def decidir(self, player_rect, moedas, obstaculos_rects):
        ax, ay = self._vet_atrair_moeda(player_rect, moedas)
        rx, ry = self._vet_repulsao(player_rect, obstaculos_rects)
        vx, vy = ax + rx * self.peso, ay + ry * self.peso
        vx, vy = _norm(vx, vy)
        # fallback para nunca ficar parado
        if vx == 0.0 and vy == 0.0:
            alvo = self._moeda_alvo(player_rect, moedas)
            if alvo:
                px, py = player_rect.center
                dx, dy = alvo.centerx - px, alvo.centery - py
                if abs(dx) >= abs(dy):
                    vx = 1.0 if dx > 0 else -1.0
                else:
                    vy = 1.0 if dy > 0 else -1.0
        return vx, vy

def carregar_melhor_agente():
    """
    Carrega parâmetros do arquivo JSON salvo pelo algoritmo genético.
    Se não existir, devolve um agente com parâmetros padrão.
    """
    if os.path.exists(ARQ_MELHOR):
        try:
            with open(ARQ_MELHOR, "r", encoding="utf-8") as f:
                data = json.load(f)
                alc = float(data.get("alcance_repulsao", 120.0))
                peso = float(data.get("peso_repulsao", 1.2))
                return AgenteParametrico(alcance_repulsao=alc, peso_repulsao=peso)
        except Exception:
            pass
    return AgenteParametrico()
