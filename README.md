# DriveMatchBot

---

<p align="center">
    <a href="https://github.com/cleitonleonel/DriveMatchBot" target="_blank">
        <img src="https://raw.githubusercontent.com/cleitonleonel/DriveMatchBot/master/src/media/taxi.png" alt="DriveMatchBot" width="300"/>
    </a>
</p>
    <p align="center">
      <i><a href="https://t.me/DriveMatch_bot">DriveMatchBot</a> é um bot para Telegram que conecta passageiros a motoristas próximos e vice-versa. O bot facilita a interação entre usuários, permitindo que passageiros encontrem rapidamente motoristas disponíveis em sua área e motoristas recebam solicitações de corrida de passageiros próximos. Ideal para criar um serviço de caronas ou táxis de forma simples e eficiente...
</i>
    </p>
<p align="center">
    <a target="_blank">
        <img src="https://img.shields.io/badge/python-3.12%2B-green" alt="python" width="300">
    </a>
</p>

---

## ✨ Diferenciais do Produto (MAT)

O DriveMatchBot foi elevado de um protótipo para um produto de nível comercial com os seguintes pilares:

-   **🎯 Geolocalização de Alta Precisão**: Utiliza **PostGIS** para buscar motoristas em um raio geográfico exato.
-   **⚡ Escalabilidade Assíncrona**: Arquitetura 100% assíncrona baseada em **Redis**.
-   **💎 UX Premium**: Mensagens estilizadas, botões intuitivos e alertas de proximidade.
-   **💰 Ciclo Financeiro Completo**: Checkout integrado via **PIX (pypix)** com split automático (80/20).
-   **🌟 Sistema de Reputação**: Avaliações mútuas que garantem a qualidade.
-   **🖥️ Web Admin Panel**: Painel administrativo profissional via **FastAPI** para gestão de usuários e taxas.

---

## 🛠️ Stack Tecnológica

-   **Linguagem**: Python 3.12+ (**Gerenciado por [uv](https://docs.astral.sh/uv/)**)
-   **Bot Engine**: Telethon (Async Telegram API)
-   **Web Framework**: FastAPI (Admin Panel)
-   **Banco de Dados**: PostgreSQL + **PostGIS**
-   **Cache & States**: **Redis**
-   **Finanças**: [pypix](https://github.com/cleitonleonel/pypix)
-   **Localização**: Geopy & Nominatim

---

## Instalação e Configuração

### 1. Clonando o projeto:

```shell
git clone https://github.com/cleitonleonel/DriveMatchBot.git
cd DriveMatchBot
```

### 2. Configurando o Ambiente (via `uv`):

Este projeto utiliza o **`uv`** para gerenciamento de dependências ultrarrápido.

```shell
# Criar venv e instalar dependências
uv sync
```

---

## 🚀 Guia de Deploy

### 1. Configuração de Ambiente
O DriveMatchBot utiliza o arquivo `config.toml` para gerenciar as credenciais e parâmetros do sistema. Crie um arquivo `config.toml` na raiz (baseado no `config_dev.toml` se necessário):

```toml
[API]
ID = 123456
HASH = "seu_hash"
BOT_TOKEN = "seu_token"

[ADMIN]
IDS = [1285949564]

[DATABASE]
# URL do Banco de Dados (PostgreSQL + PostGIS)
DATABASE_URL = "postgresql+psycopg2://user:pass@host:5432/db"
REDIS_URL = "redis://localhost:6379/0"
```

### 2. Configurando base de dados (Postgres):
```shell
uv run python manage.py makemigrations
uv run python manage.py migrate
```

---

## 🖥️ Painel Administrativo Web

O DriveMatch inclui um painel administrativo moderno para gerenciar a plataforma sem comandos de chat.

- **Iniciar Painel**: `make admin` (Acessível em `http://localhost:8000`)
- **Recursos**:
    - Dashboard de faturamento.
    - Ativação/Desativação de usuários.
    - Edição de taxas globais.

---

## 🧪 Testes e Qualidade de Código

### Validação de Funcionalidade
Para validar a integridade antes do lançamento, execute nossos testes isolados:
```bash
make test
```

### Limpeza e Padronização
```bash
make format
```

### Iniciar o Bot
Para subir o bot em modo desenvolvedor local:
```bash
make run
```

## Licença

Este projeto está licenciado sob a Licença MIT.

---

<img src="https://github.com/cleitonleonel/pypix/blob/master/qrcode.png?raw=true" alt="Your image title" width="250"/>

---

## 🤝 Suporte e Contribuição
Desenvolvido com ❤️ por [Cleiton Leonel](https://github.com/cleitonleonel). 
Dúvidas ou suporte: `cleiton.leonel@gmail.com`
