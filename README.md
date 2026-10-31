# qobuz-discord-rpc

Discord Rich Presence para o app desktop do **Qobuz** no Windows. Mostra a música que você está ouvindo no seu perfil do Discord, com capa do álbum.

Usa o Rich Presence oficial do Discord (IPC local), então não mexe no client do Discord e não usa token de conta.

## Como funciona

1. Lê o título da janela do `Qobuz.exe` (`Música – Artista`).
2. Busca a capa do álbum no Deezer (e, se falhar, no iTunes).
3. Envia a atividade "Ouvindo" ao Discord, com o nome da música no status.

## Requisitos

- Windows 10/11
- Python 3.9+
- App desktop do Qobuz e app desktop do Discord abertos

## Instalação

```
pip install -r requirements.txt
```

1. Crie um app em <https://discord.com/developers/applications> chamado **Qobuz** (o nome aparece como "Ouvindo Qobuz") e copie o **Application ID**.
2. Em *Rich Presence → Art Assets*, envie uma imagem chamada `qobuz` (usada quando a capa não é encontrada).
3. Defina o ID, no topo do `qobuz_rpc.py` (`CLIENT_ID`) ou pela variável de ambiente:

```
set QOBUZ_RPC_CLIENT_ID=123456789012345678
```

## Uso

```
python qobuz_rpc.py                 # roda o Rich Presence
python qobuz_rpc.py --list          # mostra o título lido da janela e como foi interpretado
python qobuz_rpc.py --cover "Cut the Bridge" "Linkin Park"   # testa a busca de capa
```

## Limitações

- O Qobuz não informa o tempo da faixa, então o Discord mostra o tempo desde que a música começou a ser lida, sem barra de progresso.
- Ao pausar, a presença só some se o título da janela mudar.
- A capa é buscada por nome de música e artista e pode errar em títulos muito comuns.

## Licença

MIT
