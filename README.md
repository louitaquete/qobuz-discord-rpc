# qobuz-discord-rpc

Discord Rich Presence para o app desktop do **Qobuz** no Windows. Mostra a música que você está ouvindo no seu perfil do Discord, com a capa do álbum, e fica quietinho na bandeja do Windows (a setinha ao lado do relógio).

Usa o Rich Presence oficial do Discord (IPC local): não mexe no client do Discord e não usa token de conta.

## Instalação (recomendado)

1. Baixe o `QobuzRPC-Setup-x.y.z.exe` na página de [Releases](../../releases).
2. Execute o instalador. Marque **Iniciar com o Windows** se quiser.
3. Na primeira vez, o app pede o **Application ID** do Discord (veja abaixo).

> O instalador não é assinado digitalmente, então o Windows SmartScreen pode avisar. Clique em *Mais informações → Executar assim mesmo*.

### Criar o Application ID (uma vez)

1. Acesse <https://discord.com/developers/applications> e crie um app chamado **Qobuz** (esse nome aparece como "Ouvindo Qobuz").
2. Em *Rich Presence → Art Assets*, envie uma imagem chamada `qobuz` (usada quando a capa não é encontrada).
3. Copie o **Application ID** (página *General Information*) e cole quando o app pedir.

## Menu da bandeja

Clique com o botão direito no ícone (talvez dentro da setinha ^ da barra de tarefas):

| Item | O que faz |
|---|---|
| *status* | Mostra o que está acontecendo (ouvindo, aguardando, Discord fechado…). Clique esquerdo no ícone também mostra. |
| Mostrar no Discord | Liga/desliga o Rich Presence. |
| Iniciar com o Windows | Liga/desliga o início automático. |
| Configurar Application ID… | Troca o ID. |
| Abrir pasta de logs | Abre `%APPDATA%\QobuzRPC` (logs e configuração). |
| Sair | Encerra o app. |

## Rodar pelo código-fonte

```
pip install -r requirements.txt
python run.py
```

Diagnóstico:

```
python run.py --list                                    # título lido da janela do Qobuz
python run.py --cover "Cut the Bridge" "Linkin Park"    # testa a busca de capa
```

## Gerar o instalador

O instalador é gerado pelo GitHub Actions (`.github/workflows/build.yml`): ao criar uma tag `vX.Y.Z`, ele compila o `.exe` com PyInstaller, monta o instalador com Inno Setup e publica na Release.

```
git tag v1.0.0
git push origin v1.0.0
```

Também dá para rodar manualmente pela aba *Actions → Build installer → Run workflow* (o resultado fica como artefato).

## Como funciona

1. Lê o título da janela do `Qobuz.exe` (`Música – Artista`).
2. Busca a capa do álbum no Deezer (e, se falhar, no iTunes).
3. Envia a atividade "Ouvindo" ao Discord, com o nome da música no status.

## Limitações

- O Qobuz não informa o tempo da faixa, então o Discord mostra o tempo desde que a música começou a ser lida, sem barra de progresso.
- Ao pausar, a presença só some se o título da janela mudar.
- A capa é buscada por nome de música e artista e pode errar em títulos muito comuns.

## Licença

MIT
