# PhishDataset — Gerenciador de Dataset para Detecção de Golpes
## TCC: Detecção de Smishing e Phishing com PLN

---

## Instalação

### 1. Instalar dependências
```bash
pip install flask
```

### 2. Executar o sistema
```bash
cd dataset_manager
python app.py
```

### 3. Acessar no navegador
```
http://localhost:5000
```

---

## Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| Dashboard | Estatísticas gerais, gráficos por tipo e fonte |
| Dataset | Listagem completa com filtros e busca |
| Nova Mensagem | Formulário de cadastro com todos os campos |
| Exportar | Exportação para CSV e JSON formatados para ML |

## Estrutura de Campos

```
id           → ID automático sequencial
texto        → Texto completo da mensagem
classificacao → fraude | legitima | suspeita (label para ML)
tipo_golpe   → smishing | phishing | scam | outro
fonte        → SMS | WhatsApp | Email | Simulada
data_cadastro → Data automática de cadastro
observacoes  → Notas adicionais sobre a mensagem
revisada     → Booleano: mensagem foi validada/revisada
```

## Formato de Exportação CSV (ML-ready)

```csv
id,texto,label,tipo_golpe,fonte,data_cadastro,revisada
1,"Seu banco detectou...",fraude,phishing,Email,2024-01-12,1
```

## Tecnologias

- **Backend**: Python + Flask
- **Banco de dados**: SQLite (arquivo `database.db`)
- **Frontend**: HTML + CSS customizado + JavaScript vanilla
- **Fontes**: IBM Plex Mono / IBM Plex Sans
