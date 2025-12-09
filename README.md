# Sistema de Processamento de Dados Meteorológicos em Tempo Real

Sistema de ingestão, processamento e análise de dados meteorológicos utilizando AWS, com capacidades de processamento em tempo real e em lote, incluindo sistema de alertas.

## 📋 Visão Geral

Este projeto implementa uma arquitetura de dados completa na AWS para coletar dados meteorológicos da API Tomorrow.io, processá-los em tempo real para alertas e armazená-los para análise posterior através de pipelines ETL.

## 🏗️ Arquitetura

A arquitetura é dividida em três fluxos principais:

### 1. **Ingestão de Dados**
- **API Gateway / CloudWatch Events** → Aciona a função Lambda `producer`
- **Lambda Producer** (`lambda_function.py`): 
  - Coleta dados meteorológicos da API Tomorrow.io
  - Envia os dados para o Kinesis Data Streams (broker)

### 2. **Processamento em Tempo Real**
- **Kinesis Data Streams** (broker): Recebe os dados do producer
- **Lambda Consumer Realtime** (`consumer_realtime.py`):
  - Consome dados do Kinesis em tempo real
  - Monitora condições meteorológicas críticas:
    - Probabilidade de chuva
    - Velocidade do vento
    - Rajada de vento
    - Intensidade da chuva
  - Envia alertas via **SNS** quando os limites configurados são excedidos
  - SNS envia notificações via SMS e e-mail

### 3. **Processamento em Lote (ETL)**
- **Lambda Consumer Batch** (`consumer_batch.py`):
  - Consome dados do Kinesis
  - Armazena dados brutos no bucket S3 `raw` com particionamento por data (year/month/day)
  
- **AWS Glue Crawler** (`raw_crawler`):
  - Varre o bucket S3 `raw`
  - Cria/atualiza tabelas no Glue Data Catalog (`raw_db`)

- **AWS Glue Job** (`weather_job` - `jobglue.py`):
  - Processa dados do `raw_db`
  - Transforma dados JSON em formato Parquet
  - Aplana estruturas aninhadas
  - Particiona dados por ano, mês e dia
  - Armazena dados processados no bucket S3 `gold`

- **AWS Glue Crawler** (`gold_crawler`):
  - Varre o bucket S3 `gold`
  - Cria/atualiza tabelas no Glue Data Catalog (`gold_db`)

- **AWS Athena**: Consulta e análise dos dados processados no `gold_db`

## 📁 Estrutura do Projeto

```
project-realtimeDados/
├── lambda_function.py      # Producer Lambda - coleta dados da API
├── consumer_realtime.py     # Consumer Lambda - processamento em tempo real e alertas
├── consumer_batch.py        # Consumer Lambda - armazenamento em lote no S3
├── jobglue.py              # AWS Glue Job - ETL e transformação de dados
├── requirements.txt        # Dependências Python
└── README.md              # Este arquivo
```

## 🔧 Componentes

### Lambda Functions

#### `lambda_function.py` (Producer)
- **Função**: Coleta dados meteorológicos da API Tomorrow.io
- **Trigger**: API Gateway ou CloudWatch Events
- **Saída**: Kinesis Data Streams
- **Variáveis de Ambiente**:
  - `TOMORROW_API_KEY`: Chave da API Tomorrow.io

#### `consumer_realtime.py` (Consumer Realtime)
- **Função**: Processa dados em tempo real e envia alertas
- **Trigger**: Kinesis Data Streams
- **Saída**: SNS (alertas)
- **Variáveis de Ambiente**:
  - `PRECIPITATION_PROBABILITY`: Limite de probabilidade de chuva (padrão: 10)
  - `WIND_SPEED`: Limite de velocidade do vento em m/s (padrão: 10)
  - `WIND_GUST`: Limite de rajada de vento em m/s (padrão: 10)
  - `RAIN_INTENSITY`: Limite de intensidade da chuva em mm/h (padrão: 10)

#### `consumer_batch.py` (Consumer Batch)
- **Função**: Armazena dados brutos no S3
- **Trigger**: Kinesis Data Streams
- **Saída**: S3 bucket `raw`
- **Variáveis de Ambiente**:
  - `BUCKET_NAME`: Nome do bucket S3 para dados brutos

### AWS Glue Job

#### `jobglue.py` (Weather Job)
- **Função**: ETL dos dados meteorológicos
- **Entrada**: Glue Data Catalog (`raw_db`)
- **Processamento**:
  - Aplana estruturas JSON aninhadas
  - Extrai métricas meteorológicas (temperatura, umidade, vento, etc.)
  - Particiona dados por ano, mês e dia
- **Saída**: S3 bucket `gold` em formato Parquet

## 🚀 Configuração

### Pré-requisitos

- Conta AWS configurada
- AWS CLI configurado
- Python 3.8+
- Credenciais AWS com permissões apropriadas

### Dependências

Instale as dependências:

```bash
pip install -r requirements.txt
```

### Variáveis de Ambiente

Configure as seguintes variáveis de ambiente nas suas funções Lambda:

**Producer Lambda:**
- `TOMORROW_API_KEY`: Sua chave da API Tomorrow.io

**Consumer Batch Lambda:**
- `BUCKET_NAME`: Nome do bucket S3 (ex: `weatherrt-bacth`)

**Consumer Realtime Lambda:**
- `PRECIPITATION_PROBABILITY`: Limite de probabilidade de chuva (%)
- `WIND_SPEED`: Limite de velocidade do vento (m/s)
- `WIND_GUST`: Limite de rajada de vento (m/s)
- `RAIN_INTENSITY`: Limite de intensidade da chuva (mm/h)

### Recursos AWS Necessários

1. **Kinesis Data Streams**: Stream chamado `broker`
2. **S3 Buckets**:
   - `raw`: Para dados brutos
   - `gold`: Para dados processados
3. **SNS Topic**: `snsalerta` (ARN: `arn:aws:sns:us-east-1:331104657282:snsalerta`)
4. **Glue Data Catalog**:
   - `raw_db`: Banco de dados para dados brutos
   - `gold_db`: Banco de dados para dados processados
5. **IAM Roles**:
   - `producer_iam`: Permissões para Producer Lambda
   - `consumerrealtime_iam`: Permissões para Consumer Realtime Lambda
   - `consumerbatch_iam`: Permissões para Consumer Batch Lambda
   - `etl_role`: Permissões para Glue Job

## 📊 Fluxo de Dados

```
API Tomorrow.io
    ↓
Producer Lambda
    ↓
Kinesis Data Streams (broker)
    ├──→ Consumer Realtime Lambda → SNS → Alertas (SMS/E-mail)
    └──→ Consumer Batch Lambda → S3 (raw)
            ↓
        Glue Crawler (raw_crawler)
            ↓
        Glue Data Catalog (raw_db)
            ↓
        Glue Job (weather_job)
            ↓
        S3 (gold)
            ↓
        Glue Crawler (gold_crawler)
            ↓
        Glue Data Catalog (gold_db)
            ↓
        AWS Athena (Consultas)
```

## 🔐 Permissões IAM

### Producer Lambda Role
- Permissão para escrever no Kinesis Data Streams

### Consumer Realtime Lambda Role
- Permissão para ler do Kinesis Data Streams
- Permissão para publicar no SNS

### Consumer Batch Lambda Role
- Permissão para ler do Kinesis Data Streams
- Permissão para escrever no bucket S3 `raw`

### Glue Job Role
- Permissão para ler do Glue Data Catalog
- Permissão para ler do bucket S3 `raw`
- Permissão para escrever no bucket S3 `gold`

## 📝 Notas

- Os dados são particionados por data (year/month/day) para otimizar consultas
- O formato Parquet é usado na camada `gold` para melhor compressão e performance
- Os alertas são enviados quando qualquer um dos limites configurados é excedido
- A localização padrão configurada é: Latitude -15.31227249, Longitude -49.11664409

## 🔄 Melhorias Futuras

- [ ] Adicionar tratamento de erros mais robusto
- [ ] Implementar retry logic para chamadas de API
- [ ] Adicionar monitoramento com CloudWatch Metrics
- [ ] Implementar testes unitários
- [ ] Adicionar suporte a múltiplas localizações
- [ ] Implementar cache para reduzir chamadas à API

## 📄 Licença

Este projeto é de uso interno.
