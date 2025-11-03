# EvoCoin — Coleta & Desvio (Pygame + AG)

Jogo 2D simples feito em **Pygame** onde você coleta moedas, desvia de obstáculos e soma pontos em **60s**.  
O projeto inclui um **Agente Inteligente** treinado por **Algoritmo Genético (AG)** para jogar sozinho.

---

## 🎮 Gameplay

- **Objetivo:** coletar o máximo de moedas em 60 segundos.
- **Pontuação:**  
  - +1 por moeda coletada  
  - −2 ao colidir com um obstáculo
- **Dificuldade progressiva:** a velocidade/quantidade de obstáculos aumenta a cada 10s.
- **Animações:** moedas giram com “pulso” e o jogador recebe um flash vermelho breve ao colidir.

---

## 🗂️ Estrutura do Projeto

```
.
├─ main.py                # jogo (manual ou com agente)
├─ genetico.py            # treino do agente (algoritmo genético)
├─ agente.py              # lógica do agente em tempo de jogo
├─ melhor_agente.json     # genes do melhor agente (gerado no treino)
├─ evolucao.csv           # log de treino por geração (gerado no treino)
├─ placar.csv             # placar das partidas (nome, pontos, data/hora)
├─ assets/                # (opcional) sprites e sons
│   ├─ bg.png
│   ├─ player.png
│   ├─ coin.png
│   └─ obstacle.png
└─ score.txt              # recorde local (criado automaticamente)
```

---

## ⚙️ Requisitos

- Python **3.9+** (recomendado 3.10+)
- **Pygame**: `pip install pygame`

Opcional (para gráficos pós-treino):
- **matplotlib** (interativo): `pip install matplotlib`
- Backend gráfico (se necessário): `pip install pyqt5` ou usar **tkinter** (já vem no Python oficial)

---

## 🚀 Como rodar

### 1) Jogar manualmente
```bash
python main.py
```
| ⬅️➡️⬆️⬇️ ou WASD | Movimentar o jogador |
| P | Pausar / Retomar o jogo |
| R | Reiniciar (após o fim do jogo) |
| ESC | Sair do jogo |
| ENTER / Espaço | Iniciar partida (na tela inicial) |

### 2) Treinar o agente (Algoritmo Genético)
```bash
# treino básico (gera evolucao.csv + melhor_agente.json + abre gráfico)
python genetico.py
```

#### Parâmetros úteis do treino
```bash
# mais gerações e população
python genetico.py --geracoes 40 --pop 80

# escolher seed (reprodutibilidade)
python genetico.py --seed 123

# suavizar o gráfico com média móvel (k = janela)
python genetico.py --smooth 5

# ver animação da evolução geração a geração
python genetico.py --animate

# combinar tudo
python genetico.py --geracoes 50 --pop 100 --seed 987 --smooth 7 --animate
```

> Dica: cada execução **reinicia** o `evolucao.csv` (apenas o treino atual).  
> Campos do `evolucao.csv`: `geracao, melhor_fitness, media_fitness`.

### 3) Jogar com o agente treinado
```bash
# usa os genes do melhor agente em melhor_agente.json
python main.py --play-best --nome "Rafaela"
```

Parâmetros:
- `--play-best` → inicia já com o agente jogando
- `--nome "Seu Nome"` → registra partidas no `placar.csv`

> Campos do `placar.csv`: `nome, pontos, data_hora`.

---

## 🧠 Como o agente funciona

- O **genetico.py** evolui 3 genes:
  - `alcance_repulsao`: alcance de “percepção” dos obstáculos
  - `peso_repulsao`: peso da repulsão (desvio)
  - `vel_jogador`: velocidade do agente
- A avaliação (fitness) soma **+1 por moeda** e **−2 por colisão** ao longo de ~60s simulados.
- O melhor indivíduo é salvo em **`melhor_agente.json`** e usado pelo `main.py` no modo `--play-best`.

---

## 🖼️ Assets

O jogo funciona **sem sprites** (usa cores fallback).  
Para visual mais bonito, coloque imagens em `assets/` com os nomes:

- `bg.png` (800×600 recomendado)
- `player.png` (48×48)
- `coin.png` (32×32 ou maior — será redimensionada/animada)
- `obstacle.png` (80×20)

---

## 🧪 Comandos — resumo rápido

```bash
# Instalar dependências
pip install pygame matplotlib

# Jogar manual
python main.py

# Jogar com agente
python main.py --play-best --nome "Jogador"

# Treinar agente (gera gráfico interativo)
python genetico.py

# Treinar com configurações
python genetico.py --geracoes 40 --pop 80 --seed 123 --smooth 5
python genetico.py --animate
```

---

## 🛠️ Configurações visuais (moedas)

No `main.py`, você pode ajustar:
```python
COIN_BASE_SIZE = 32          # sprite base
COIN_ROT_SPEED = 180.0       # graus/seg
COIN_PULSE_SPEED = 4.0       # velocidade do “pulso”
COIN_PULSE_MIN_SCALE = 1.25  # escala base (moeda maior)
COIN_PULSE_AMP = 0.12        # amplitude do pulso
```

---

## ❓Dúvidas & Solução de Problemas

- **A janela do gráfico não abre após o treino**  
  Instale um backend interativo:
  ```bash
  pip install matplotlib pyqt5
  ```
  (ou use o Python oficial com tkinter.)

- **O gráfico sempre aparece “igual”**  
  Use outra **seed** (`--seed`) ou aumente gerações/população.  
  O `genetico.py` já reinicia o `evolucao.csv` a cada treino.

- **O agente não se move**  
  Certifique-se de que existe **`melhor_agente.json`** (rode `genetico.py` primeiro) e execute com `--play-best`.

---

## 🧩 Tecnologias Utilizadas

- **Python 3.10+**
- **Pygame 2.x**
- **IDE recomendada:** VS Code, PyCharm ou IDLE

---

## 📝 Licença e Créditos

Projeto acadêmico/educacional. Use e modifique livremente.  
Créditos: implementação do jogo, agente e documentação desenvolvidos em colaboração com o(a) estudante.

---
## 👨‍💻 Autor

**Desenvolvido por:** *Matteo Souza Caetano / Adison de Oliveira*  
📧 *E-mail:* matteoscaetano@gmail.com / adisonogm376@gmail.com
🎓 *Disciplina:* Inteligencia Artificial Aplicada / PUC Goiás  
📅 *Ano:* 2025
