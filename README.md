# /dia — v0.1

Herramienta de hábito y cierre. Registra sesiones de trabajo en formato NDJSON y genera bitácoras inmutables.
El foco de v0.1 es instalar el ciclo: iniciar → trabajar → cerrar.

## Qué es /dia
- CLI local para iniciar, checkpoint y cierre de sesión.
- UI web (Svelte) para zona indeleble y zona viva.
- API Django read-only que expone sesiones/eventos.
- Rutinas técnicas declarativas: sugieren y registran, no ejecutan.

## Qué no es
- No ejecuta commits ni pushes.
- No toca ramas protegidas.
- No es agente autónomo (v0.1).

## Estructura
- `cli/`: CLI Python (`dia start`, `dia pre-feat`, `dia end`, `dia update`).
- `server/`: Django API read-only.
- `ui/`: UI Svelte.
- `data/`: eventos NDJSON, bitácoras, artefactos.
- `docs/`: specs y manual.

## Requisitos
- Python 3.9+ con venv local `envdia`.
- Docker para `server` + `ui`.
- Repo Git local donde se trabaja la sesión.

## Instalación CLI (local)
```
source envdia/bin/activate
cd /Users/joseassizalcarazbaxter/Developer/dia/cli
pip install -e .
```

Si aparece `No module named pip`:
```
python3 -m pip install --upgrade pip setuptools wheel
```

## Actualizar CLI
Solo si cambiaste empaquetado/entrypoints:
```
dia update
```
Si solo cambiaste `.py`, no hace falta reinstalar.

## Levantar UI + API (Docker)
```
make up
```
UI: `http://localhost:5173`  
API: `http://localhost:8000/api`

## Uso rápido (interactivo)
Desde el repo donde vas a trabajar:
```
cd /ruta/al/repo
dia start --data-root /ruta/al/monorepo/data --area it
```

Confirmaciones y solicitudes:
1) Usa el nombre del directorio como `project` (confirmar).  
2) Pide intención (1 frase).  
3) Pide DoD.  
4) Pide modo (default `it`).  

Luego:
```
dia pre-feat --data-root /ruta/al/monorepo/data --area it
dia end --data-root /ruta/al/monorepo/data --area it
```

## Datos generados
- `data/index/events.ndjson` (append-only)
- `data/bitacora/YYYY-MM-DD/Sxx.md`
- `data/bitacora/YYYY-MM-DD/CIERRE_Sxx.md`
- `data/bitacora/YYYY-MM-DD/LIMPIEZA_Sxx.md`
- `data/artifacts/*` (diffs, logs)

## Convención de commits

**Sistema de identificación**:
- **Commits de Cursor/IA**: `git-commit-cursor` → autoría `Cursor Assistant <cursor@dia.local>` + 🦾 al INICIO
- **Commits manuales**: `git -M` → tu autoría normal, sin emoji

**Formato**: `🦾 tipo: mensaje [#sesion Sxx]` (sin `[dia]`)

**Recordatorios automáticos**: `dia start` genera `.cursorrules` en el repo activo para que Cursor recuerde el workflow.

## Manual
Ver `docs/manual/TUTORIAL_INTRO_V0_1.md`.
