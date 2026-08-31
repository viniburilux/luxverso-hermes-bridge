# Playbook: Data Source Discovery

**Evidência:** Aplicado 1 vez com sucesso:
1. **CGU 2026** (2026-08-31): 4 fontes descobertas em 1 turno — PNCP (API oficial), NASA FIRMS (CSV público), CNES (OpenDataSUS), IBGE (GeoJSON). Cruzadas com PNCP resultaram em 4 iniciativas PROVEN.

**Quando usar:** "Preciso de dados sobre [X]", "qual a melhor fonte para [Y]", "tem dado público sobre [Z]?".

---

## Sequência

### FASE 1 — DEFINIR O QUE BUSCA
Especificar:
- **Entidade** (município, empresa, pessoa, evento, propriedade)
- **Período** (data_range)
- **Granularidade** (município, UF, bairro, individual)
- **Propriedades** (lat, lon, valor, categoria, status)

### FASE 2 — VERIFICAR FONTES CONHECIDAS
**Fontes BR já catalogadas (Lux-Radar + Lux-Lab):**
- **PNCP** — `https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao` — contratações públicas federais
- **NASA FIRMS** — `https://firms.modaps.eosdis.nasa.gov/data/active_fire/...csv` — focos de queimada ativos (24h)
- **OpenDataSUS (CNES)** — `https://apidadosabertos.saude.gov.br/cnes/estabelecimentos` — estabelecimentos de saúde
- **IBGE Localidades** — `https://servicodados.ibge.gov.br/api/v1/localidades` — municípios, UFs
- **INPE Queimadas** — quebrado SSL, mas acessível via FIRMS
- **IBGE GeoJSON** — `https://servicodados.ibge.gov.br/.../geojson` — polígonos
- **NASA EONET** — `https://eonet.gsfc.nasa.gov/api/v3/events` — eventos naturais globais
- **Open-Meteo** — `https://api.open-meteo.com/v1/forecast` — clima

**Fontes globais (TraceFoundry adapters):**
- **DANDI** — neurociência
- **OpenAlex** — papers acadêmicos
- **PatentsView** — patentes US (precisa key)
- **Zenodo** — datasets genéricos

### FASE 3 — TESTAR ACESSO
```bash
# Testar URL
curl -fsSI "<url>" | head -5

# Testar com params
curl -fsS "<url>?param=value" | head -c 200
```

**Critérios:**
- HTTP 200 ✅
- JSON estruturado (não HTML)
- Sem auth necessária
- Sem rate limit agressivo

### FASE 4 — VALIDAR DADOS
1. **Contar registros:** `jq length < data.json` ou `len(parsed)`
2. **Ver schema:** primeiro record, identificar campos
3. **Conferir cobertura:** matches com geografia/período esperado?
4. **Conferir lat/lon:** quando aplicável

### FASE 5 — CRUZAR COM BASES PRÓPRIAS
- Com IBGE: padronizar codigo_ibge
- Com PNCP: cruzar codigo_ibge + data
- Com FIRMS: cruzar lat/lon + data (Haversine para distância)
- Com CNES: cruzar codigo_ibge (mesma chave territorial)

### FASE 6 — REGISTRAR FONTE
Adicionar em `~/.hermes/capabilities/registry.yaml`:
```yaml
- id: <fonte>-collect
  name: <descrição>
  type: data-acquisition
  domain: <domínio>
  problem_types: [<lista>]
  inputs: [<campos>]
  outputs: <formato>
  scripts: <caminho>
  evidencia: <evidência>
```

---

## Anti-padrões

- **NÃO use Google sem key de API** — limits são agressivos
- **NÃO baixe datasets inteiros sem testar schema** — pode ser 10GB
- **NÃO acredite em "dados abertos" sem testar auth** — "aberto" no Brasil muitas vezes requer cadastro
- **NÃO reinvente a coleta** — use TraceFoundry adapters se existirem
- **NÃO cruze sem chave territorial comum** — codigo_ibge é o mais universal no BR

---

## Métricas de Sucesso

Uma fonte está "OK" quando:
- ✅ Acessível via HTTPS sem auth
- ✅ Retorna JSON estruturado
- ✅ Tem schema documentado
- ✅ Tem pelo menos 1 chave territorial (codigo_ibge, lat/lon, CNPJ)
- ✅ Tem timestamp ISO 8601

**Status:** proven
**Confidence:** 0.85
**Last used:** 2026-08-31 (CGU 4 fontes)
**Reused count:** 1
