# Bot invasor ladrão de dados safado

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

Em um arquivo `.env` na raíz do projeto:

```
DISCORD_TOKEN={token do bot}
GUILD_ID={id da guilda}
```

### 4. Executar

```bash
python bot.py
```

<!-- 1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Add the token to your `.env` file -->
