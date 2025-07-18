```bash
python -m venv venv # Windows
.\venv\Scripts\activate

python3 -m venv venv # Linux / macOS
source ./venv/bin/activate
```

```bash
pip install -r requirements.txt
```

`.env`:

```
DISCORD_TOKEN={token do bot}
GUILD_ID={id do server}
MONGO_URI={string de conexão do MongoDB}
BATCH_SIZE={tamanho dos batches (padrão é 500)}
```

```bash
python bot.py
```

- É necessário permissões: Leitura de mensagens, histórico, envio de mensagens

- O bot só coleta dados do servidor onde está rodando e precisa de permissões de leitura de mensagens.
- Não use para fins maliciosos.
