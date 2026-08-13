# Painel de Backups — Controle Interno

Painel web que consulta a API do MSP Clouds (Cloud Backup PRO) periodicamente
e mostra o status de todas as tarefas de backup de todos os clientes num
único lugar, com destaque automático para erros, avisos e backups atrasados.

Não depende de e-mail nem de entrar cliente por cliente no portal — os dados
vêm direto da API `reports/summary`.

---

## 1. Pré-requisitos

- Python 3.10 ou superior instalado no seu PC
- A chave de API do MSP Clouds ativada (Portal Web → engrenagem no canto
  superior direito → Configurações → API → Editar → Ativar)

## 2. Instalação

Abra um terminal (PowerShell, no Windows) dentro da pasta do projeto e rode:

```bash
pip install -r requirements.txt
```

## 3. Configuração

Copie o arquivo `.env.example` para `.env`:

```bash
copy .env.example .env
```

Abra o `.env` e cole sua chave de API no lugar de `cole_sua_chave_aqui`:

```
MSPCLOUDS_API_KEY=sua_chave_real_aqui
```

> ⚠️ Se a autenticação da API do MSP Clouds usar um formato diferente de
> `Authorization: Bearer <chave>` (por exemplo, a chave indo direto na URL
> como parâmetro), me avise o formato exato mostrado na tela deles em
> "Try it" — é só uma linha para ajustar em `fetch_data.py`, na função
> `_request_headers()`.

## 4. Testar a coleta de dados (opcional, mas recomendado)

Antes de subir o painel, rode só a coleta pra confirmar que a API responde
certo:

```bash
python fetch_data.py
```

Deve aparecer algo como:
```
[OK] 214 tarefas atualizadas com sucesso
```

Se der erro, a mensagem já indica o motivo (chave inválida, sem internet, etc).

## 5. Rodar o painel

```bash
python app.py
```

Você verá algo como:
```
Coletando dados a cada 30 minutos.
Painel disponível em http://0.0.0.0:5000  (acesse pelo IP desta máquina na rede)
```

No seu próprio PC, acesse: **http://localhost:5000**

## 6. Acessar de outros computadores na rede

1. Descubra o IP local do seu PC:
   - Windows: abra o `cmd` e digite `ipconfig`, procure "Endereço IPv4"
     (geralmente algo como `192.168.0.XX`)
2. Em qualquer outro computador **na mesma rede** (Wi-Fi/cabo do escritório),
   acesse pelo navegador: `http://192.168.0.XX:5000` (troque pelo IP real)
3. Se não abrir, o Firewall do Windows provavelmente está bloqueando.
   Libere a porta 5000:
   - Painel de Controle → Firewall do Windows Defender → Configurações
     avançadas → Regras de Entrada → Nova Regra → Porta → TCP → 5000 → Permitir

> O painel só fica disponível enquanto o `python app.py` estiver rodando no
> seu PC. Se quiser que fique sempre no ar (mesmo com o PC ligado e você sem
> o terminal aberto), me avise — dá para configurar para rodar como serviço
> em segundo plano.

## 7. Como funciona por baixo dos panos

- `fetch_data.py` chama a API do MSP Clouds e grava o resultado em
  `data/backups.db` (um banco SQLite local, criado automaticamente)
- `app.py` sobe o site e roda `fetch_data.py` sozinho a cada
  `FETCH_INTERVAL_MINUTES` (padrão: 30 minutos), sem precisar de Task
  Scheduler nem nada externo
- A tela busca os dados salvos em `data/backups.db` — não fala com a API
  diretamente, então abre rápido mesmo se a API estiver lenta
- O botão **"Atualizar agora"** força uma busca imediata, sem esperar o
  próximo ciclo automático

## 8. O que o painel mostra

- Cartões de resumo: total de tarefas, quantas em erro, aviso, atrasadas,
  sem monitoramento e com sucesso — clique em qualquer um para filtrar
- Tabela com todos os clientes e tarefas, com busca por nome e ordenação por
  coluna (clique no cabeçalho)
- **"Atrasado"**: calculado automaticamente quando uma tarefa passa de
  `STALE_HOURS` (padrão: 26h) sem um backup com sucesso — ajustável no `.env`
- Link direto para o relatório de cada execução no próprio portal do MSP
  Clouds, quando disponível

## 9. Ajustes comuns

| O que mudar                          | Onde                              |
|---------------------------------------|------------------------------------|
| Intervalo de coleta automática       | `.env` → `FETCH_INTERVAL_MINUTES` |
| Quantas horas até marcar "Atrasado"  | `.env` → `STALE_HOURS`            |
| Porta do painel                       | última linha de `app.py`          |
