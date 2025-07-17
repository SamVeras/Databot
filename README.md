# Databot

Bot de Discord para coletar dados de _seu próprio servidor_ para propósitos de análise, sem intenções nefastas.

## Setup

### 1. Ambiente virtual

```bash
python -m venv venv # Windows
.\venv\Scripts\activate

python3 -m venv venv # Linux / macOS
source ./venv/bin/activate
```

### 2. Dependências

```bash
pip install -r requirements.txt
```

### 3. Variáveis de ambiente

Crie um arquivo `.env` na raíz do projeto com o seguinte conteúdo:

```
DISCORD_TOKEN={token do bot}
GUILD_ID={id da guilda}
MONGO_URI={sua string de conexão do MongoDB}
BATCH_SIZE=750
```

- **BATCH_SIZE**: Controla quantas mensagens são salvas de uma vez no banco de dados. Valores maiores podem acelerar a coleta, mas usam mais RAM. O padrão é 500, recomendado entre 500 e 2000.

### 4. Executar

```bash
python bot.py
```

## Comandos Disponíveis

- `/scrape` — Coleta todas as mensagens do canal atual e salva no banco de dados. (Requer permissão de administrador)
- `/show <id da mensagem>` — Mostra uma mensagem específica do banco de dados pelo ID.
- `/random` — Mostra uma mensagem aleatória do banco de dados.
- `/randomfix` — Mostra uma mensagem fixada aleatória do banco de dados.
- `/ping` — Testa a latência do bot.
- `/teste` — Testa se o bot está respondendo.
- `/repetir <mensagem>` — Repete a mensagem enviada.
- `/admintest` — Testa permissões de administrador.
- `/nonadmintest` — Testa permissões de não-administrador.
- `/restart` — Reinicia o bot (apenas para administradores).

## Permissões Necessárias

- O bot precisa de permissões de leitura de mensagens, leitura de histórico, envio de mensagens e, para alguns comandos, permissão de administrador.
- Para coletar dados de todos os canais, o bot deve ter acesso a cada canal desejado.

## Performance

- O bot salva mensagens em lotes (bulk) no MongoDB, o que é muito mais rápido do que salvar uma por uma.
- O maior gargalo é a API do Discord, que é naturalmente lenta para buscar mensagens antigas.
- Se quiser mais performance, aumente o `BATCH_SIZE` (se sua máquina aguentar) ou rode o bot em um servidor mais rápido.
- Para canais muito grandes, pode consumir bastante RAM.

## Observações

- O bot só coleta dados do servidor onde está rodando e precisa de permissões de leitura de mensagens.
- Não use para fins maliciosos.
