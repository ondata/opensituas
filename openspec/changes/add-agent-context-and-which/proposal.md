## Why

opensituas è pensata per gli agenti AI, ma manca di due strumenti fondamentali per
l'auto-orientamento: un endpoint di introspection strutturata e una discovery semantica
dei report. Gli agenti devono oggi parsare `--help` o conoscere a priori i codici pfun.

## What Changes

- **Nuovo comando `agent-context`**: emette un JSON versionato con schema_version, info
  CLI, elenco comandi con flag/annotazioni/exit code — consumabile da agenti senza
  parsare `--help`.
- **Nuovo comando `which`**: riceve una query in linguaggio naturale (es. "comuni per
  data", "province cessate") e restituisce i report SITUAS più pertinenti (pfun + titolo
  + comando suggerito) con exit code 0/2.

## Capabilities

### New Capabilities

- `agent-context`: introspection strutturata della CLI in JSON versionato per agenti AI
- `which`: discovery semantica dei report SITUAS da linguaggio naturale

### Modified Capabilities

## Impact

- `src/opensituas/cli.py`: aggiunti due `@app.command`
- Nessuna dipendenza esterna nuova (solo stdlib + catalogo già caricato)
- Nessuna breaking change agli altri comandi
