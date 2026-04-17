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
        <img src="https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-green" alt="python" width="300">
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

---

## 🛠️ Stack Tecnológica

-   **Linguagem**: Python 3.10+
-   **Bot Engine**: Telethon (Async Telegram API)
-   **Banco de Dados**: PostgreSQL + **PostGIS**
-   **Cache & States**: **Redis**
-   **Finanças**: [pypix](https://github.com/cleitonleonel/pypix)
-   **Localização**: Geopy & Nominatim

---

## Clonando o projeto:

```shell
git clone https://github.com/cleitonleonel/DriveMatchBot.git
cd DriveMatchBot
```

---

## 🚀 Guia de Deploy (Produção)

### 1. Configuração de Ambiente
Recomendamos o uso de variáveis de ambiente para maior segurança. Crie um arquivo `.env` ou exporte:
```bash
export API_ID=seu_id
export API_HASH=seu_hash
export BOT_TOKEN=seu_token
export ADMIN_IDS=id1,id2
export DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
```

### 2. Execução Rápida via Docker
O projeto está pronto para ser orquestrado via Docker Compose:
```bash
chmod +x deploy.sh
./deploy.sh
```

### 3. Monitoramento de Logs
Os logs de produção são gravados em `drivematch.log` e também podem ser visualizados via Docker:
```bash
docker-compose logs -f bot
```

---

##  Configurando base de dados (Postgres):
```shell
poetry run python manage.py makemigrations
poetry run python manage.py migrate
```

---

## 🧪 Testes e Qualidade de Código

Para facilitar o desenvolvimento, usamos o `Makefile` para organizar comandos frequentes. 

### Validação de Funcionalidade
Para validar a integridade antes do lançamento, execute nossos testes isolados (mocks assíncronos):
```bash
make test
```

### Limpeza e Padronização
Seu ambiente inclui linter embutido (`autoflake`) configurado pelo `pyproject.toml`. Essa ferramenta varre o projeto para remover imports não utilizados e variáveis orfãs (dead code), otimizando a leitura:
```bash
make format
```

### Iniciar o Bot
Para subir o bot em modo desenvolvedor local:
```bash
make run
```

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<img src="https://github.com/cleitonleonel/pypix/blob/master/qrcode.png?raw=true" alt="Your image title" width="250"/>

---

## 🤝 Suporte e Contribuição
Desenvolvido com ❤️ por [Cleiton Leonel](https://github.com/cleitonleonel). 
Dúvidas ou suporte: `cleiton.leonel@gmail.com`
