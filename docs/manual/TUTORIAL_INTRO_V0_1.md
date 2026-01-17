# Tutorial introductorio v0.1

Objetivo: probar el flujo real de `/dia` con CLI local + UI + API ya corriendo en Docker.

## Requisitos
- Contenedores `server` y `ui` corriendo sin errores.
- Un repo Git local para operar con el CLI.
- Acceso a `data/` dentro del monorepo.
- Entorno virtual activo: `source envdia/bin/activate`.

## 0) Instalar la CLI local (editable)
En `envdia` activo, instalar desde el monorepo:

```
cd /Users/joseassizalcarazbaxter/Developer/dia/cli
pip install -e .
```

Nota: el punto final es obligatorio. Sin el `.` aparece el mensaje de uso de pip.
Si `pip` es muy viejo y falla el editable, actualizar:

```
python3 -m pip install --upgrade pip
```

Si el error menciona `No module named pip`, instalar/actualizar `pip`, `setuptools` y `wheel` dentro del venv:

```
python3 -m pip install --upgrade pip setuptools wheel
```

Actualizacion de la CLI (cuando cambias empaquetado o entrypoints):

```
dia update
```

Nota: si solo cambias archivos `.py`, no hace falta reinstalar.

## 1) Verificar UI y API
1. Abrir la UI: `http://localhost:5173`
2. Verificar API: `http://localhost:8000/api/sessions/`

Si ambos responden, la UI debería mostrar zonas indeleble/viva aunque estén vacías.

## 2) Iniciar una sesión (`dia start`)
Desde el repo donde vas a trabajar:

```
cd /ruta/al/repo
dia start --data-root /ruta/al/monorepo/data --area it
```

Confirmaciones y solicitudes:
1) Se usará el nombre del directorio principal como nombre del proyecto. Confirmar.  
2) Solicita intención (1 frase).  
3) Solicita DoD (definición de hecho).  
4) Solicita modo (default `it`).  

Notas:
- Si escribís `no`, se cancela para que hagas `cd` al repo correcto.
- `--project` y `--repo` son opcionales; si no se pasan, se usa el directorio actual.

Qué debería pasar:
- Se crea `data/bitacora/YYYY-MM-DD/Sxx.md`.
- Se agrega un evento `SessionStarted` y `RepoBaselineCaptured` en `data/index/events.ndjson`.
- La UI muestra una sesión activa en zona viva.

## 3) Checkpoint de éxito (`dia pre-feat`)
Desde el repo donde estás trabajando:

```
dia pre-feat --data-root /ruta/al/monorepo/data --area it
```

Notas:
- Usa el directorio actual como repo si no pasás `--repo`.
- No ejecuta commits, solo sugiere el comando.

Qué debería pasar:
- Se imprime **solo** un comando sugerido:
  ```
  git commit -m "feat: ... [dia] [#sesion Sxx]"
  ```
- Se registra un evento `CommitSuggestionIssued` en NDJSON.
- **No** se ejecuta ningún commit automáticamente.

## 4) Cerrar la sesión (`dia end`)
Ejemplo:

```
dia end \
  --project surfix \
  --area it \
  --repo /ruta/al/repo \
  --data-root /ruta/al/monorepo/data
```

Qué debería pasar:
- Se generan:
  - `data/bitacora/YYYY-MM-DD/CIERRE_Sxx.md`
  - `data/bitacora/YYYY-MM-DD/LIMPIEZA_Sxx.md`
- Se registran eventos `RepoDiffComputed`, `CleanupTaskGenerated`, `SessionEnded`.
- La UI refleja que la sesión quedó cerrada.

## 5) Checklist rápida de validación
- `events.ndjson` crece en append-only.
- `Sxx.md`, `CIERRE_Sxx.md`, `LIMPIEZA_Sxx.md` existen.
- UI actualiza zona indeleble/viva sin errores.

## 6) Convención de commits: distinguir manual vs automatizado

**Sistema de identificación**:
- **Commits de Cursor/IA**: Usan `git-commit-cursor` con autoría `Cursor Assistant <cursor@dia.local>` y prefijo 🦾
- **Commits manuales**: Usan `git -M` con tu autoría normal, sin emoji

**Commits automatizados (Cursor)**:
Los commits sugeridos por `dia pre-feat` usan `git-commit-cursor`:
```bash
dia pre-feat --data-root /path/to/data
# → sugiere: git-commit-cursor -m "🦾 feat: pre-feat checkpoint [#sesion Sxx]"
```

Esto genera commits con:
- Autor: `Cursor Assistant <cursor@dia.local>`
- Mensaje con 🦾 al INICIO para identificación rápida en git log
- Sin `[dia]` (se removió por confusión)

**Commits manuales (tuyos)**:
Para hacer un commit realmente tuyo (sin emoji, con tu autoría):
```bash
# Opción 1: agregar al PATH y usar como alias
export PATH="$PATH:/Users/joseassizalcarazbaxter/Developer/dia/cli"
git -M "feat: mi cambio manual"

# Opción 2: usar directamente
/path/to/dia/cli/git-M "feat: mi cambio manual"
```

**Resultado en git log**:
- `Cursor Assistant <cursor@dia.local>` + 🦾 = commit de Cursor/IA
- Tu nombre + sin 🦾 = commit manual tuyo

**Por qué**: Cursor puede hacer muchos commits. Con este sistema quedan claramente identificados en el git log por autoría y prefijo visual.

## 7) Recordatorios automáticos para Cursor

**Al iniciar sesión**: `dia start` genera automáticamente `.cursorrules` en el repo activo.

Este archivo contiene las reglas de workflow que Cursor lee automáticamente:
- Convención de commits (🦾 al inicio, usar `git-commit-cursor`)
- Autoría identificable
- Workflow /dia

**Actualización periódica**: Cada vez que ejecutás `dia start`, se regenera `.cursorrules` con las reglas actuales.

**Manual**: También podés generar el recordatorio manualmente:
```bash
python3 -m dia_cli.cursor_reminder > .cursorrules
```

## Notas
- El CLI no ejecuta commits ni pushes.
- `/dia` no toca ramas protegidas: solo sugiere.
- Si trabajás con múltiples repos, apuntar siempre `--repo` y `--data-root` correctos.
