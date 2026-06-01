## ADDED Requirements

### Requirement: Discovery semantica dei report SITUAS da query naturale
Il comando `which <query>` SHALL cercare nel catalogo SITUAS i report il cui titolo,
ambito territoriale o unità territoriale contengono i token della query (case-insensitive).
Il risultato SHALL essere una lista ordinata per rilevanza (numero di token matched)
con al massimo `--limit` voci (default 3).

#### Scenario: Query con match
- **WHEN** si esegue `opensituas which "comuni per anno"`
- **THEN** exit code è 0
- **THEN** output contiene almeno un report con pfun, titolo e comando suggerito

#### Scenario: Query senza match
- **WHEN** si esegue `opensituas which "xyz_inesistente"`
- **THEN** exit code è 2
- **THEN** su stderr appare un messaggio che nessun report corrisponde

#### Scenario: Flag --limit
- **WHEN** si esegue `opensituas which --limit 1 "comuni"`
- **THEN** il risultato contiene al massimo 1 voce

### Requirement: Output include comando suggerito per ogni report trovato
Per ogni report restituito, `which` SHALL includere il campo `comando_suggerito`
con il comando completo (es. `opensituas get 61 --date DD/MM/YYYY` per report DATA,
`opensituas get 50 --from DD/MM/YYYY --to DD/MM/YYYY` per report PERIODO).

#### Scenario: Report a data singola
- **WHEN** il report trovato è di tipo DATA (parametro `pdata`)
- **THEN** `comando_suggerito` contiene `get <pfun> --date <fine_validità>`

#### Scenario: Report a intervallo
- **WHEN** il report trovato è di tipo PERIODO (parametri `pdatada`/`pdataa`)
- **THEN** `comando_suggerito` contiene `get <pfun> --from ... --to ...`

### Requirement: Senza argomenti lista l'indice completo delle capability
Se `which` è invocato senza argomento SHALL restituire tutti i report del catalogo
(equivalente a `catalog` ma con il campo `comando_suggerito`), con exit code 0.

#### Scenario: Nessuna query
- **WHEN** si esegue `opensituas which`
- **THEN** exit code è 0
- **THEN** output contiene tutti i report del catalogo con `comando_suggerito`
