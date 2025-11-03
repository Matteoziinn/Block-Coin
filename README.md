# 🎮 Coleta & Desvio

Um jogo 2D simples desenvolvido em **Python** com **Pygame**, onde o jogador deve **coletar moedas e desviar de obstáculos** dentro de um limite de tempo.  
Ideal como projeto introdutório para quem está aprendendo **programação de jogos** ou **Pygame**.

---

## 🧠 Conceito do Jogo

Você controla um pequeno quadrado azul em uma arena.  
Seu objetivo é coletar o máximo de moedas possíveis em **60 segundos**, **evitando os obstáculos vermelhos** que se movem pela tela.

- Cada moeda coletada vale **+1 ponto**  
- Cada colisão com obstáculo remove **2 pontos**  
- Ao final, sua pontuação é comparada ao **recorde salvo localmente**

---

## 🕹️ Controles

| Tecla | Função |
|:------|:--------|
| ⬅️➡️⬆️⬇️ ou WASD | Movimentar o jogador |
| P | Pausar / Retomar o jogo |
| R | Reiniciar (após o fim do jogo) |
| ESC | Sair do jogo |
| ENTER / Espaço | Iniciar partida (na tela inicial) |

---

## 🏗️ Estrutura do Projeto

```
jogo_coleta/
│
├── main.py          # Código principal do jogo
├── score.txt        # Arquivo gerado automaticamente com o recorde
└── README.md        # Este arquivo
```

---

## ⚙️ Instalação e Execução

### 1️⃣ Instalar dependências

Certifique-se de ter o **Python 3.10+** instalado.  
Depois, crie um ambiente virtual e instale o Pygame:

```bash
python -m venv venv
# Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar Pygame
pip install pygame
```

---

### 2️⃣ Rodar o jogo

No terminal, dentro da pasta do projeto:

```bash
python main.py
```

---

## 🎯 Objetivos do Jogo

- Coletar o maior número possível de moedas em 60 segundos.
- Evitar colidir com os obstáculos móveis.
- Bater o recorde armazenado no arquivo `score.txt`.

---

## 🧩 Mecânicas Implementadas

✅ Movimento suave com teclas direcionais  
✅ Colisões com moedas e obstáculos  
✅ Sistema de pontuação e recorde salvo  
✅ Dificuldade progressiva a cada 10 segundos  
✅ Interface simples e intuitiva  
✅ Tela inicial, pausa e fim de jogo  
✅ FPS fixo (60 quadros por segundo) para estabilidade

---

## 🎨 Design e Cores

| Elemento | Cor | Descrição |
|-----------|------|------------|
| Fundo | Azul escuro (`#12161C`) | Ambiente principal |
| Jogador | Azul claro (`#40A0FF`) | Controlado pelo usuário |
| Moedas | Amarelo ouro (`#FFD700`) | Pontos a coletar |
| Obstáculos | Vermelho (`#FF5050`) | Perdem pontos ao colidir |
| HUD | Branco / cinza claro | Interface e textos |

---

## 🚀 Melhorias Futuras

- Adicionar efeitos sonoros ao coletar moedas ou bater em obstáculos  
- Incluir sprites/imagens no lugar dos retângulos  
- Criar um sistema de níveis ou modo infinito  
- Implementar um modo IA que aprenda a jogar sozinho (com base no documento de neuroevolução que inspirou o projeto)

---

## 🧩 Tecnologias Utilizadas

- **Python 3.10+**
- **Pygame 2.x**
- **IDE recomendada:** VS Code, PyCharm ou IDLE

---

## 👨‍💻 Autor

**Desenvolvido por:** *Matteo Souza Caetano*  
📧 *E-mail:* (adicione aqui, se quiser)  
🎓 *Disciplina:* Fundamentos de Programação / PUC Goiás  
📅 *Ano:* 2025
