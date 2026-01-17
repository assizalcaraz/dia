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
Ejemplo:

```
dia pre-feat \
  --project surfix \
  --area it \
  --repo /ruta/al/repo \
  --data-root /ruta/al/monorepo/data
```

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

## Notas
- El CLI no ejecuta commits ni pushes.
- `/dia` no toca ramas protegidas: solo sugiere.
- Si trabajás con múltiples repos, apuntar siempre `--repo` y `--data-root` correctos.
