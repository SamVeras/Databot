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
MSG_QUEUE_SIZE={tamanho da fila de mensagens que o bot processa}
WORKERS_COUNT={número de threads que irão processar mensagens}
BULK_SIZE={número de mensagens para cada inserção}
REMINDER_CHANNEL_NAME={nome do canal para lembretes (caso o canal em que o lembrete foi criado não exista mais, ou seja inacessível)}
```

```bash
python bot.py
```

- É necessário permissões: Leitura de mensagens, histórico, envio de mensagens

- O bot só coleta dados do servidor onde está rodando e precisa de permissões de leitura de mensagens.
- Não use para fins maliciosos.
