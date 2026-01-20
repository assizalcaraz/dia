# Gestión de Datos en /dia

**Versión**: v0.1.1  
**Última actualización**: 2026-01-19

---

## ¿Por qué `/data` está excluido del repositorio?

El directorio `/data` contiene **datos de uso** (runtime data) generados por la aplicación durante su funcionamiento normal. Estos datos son **fundamentalmente diferentes** de los **documentos de desarrollo** que sí pertenecen al repositorio.

### Separación de Responsabilidades

| Tipo | Ubicación | Contenido | ¿En el repo? |
|------|-----------|-----------|--------------|
| **Documentos de desarrollo** | `docs/`, `README.md`, etc. | Especificaciones, guías, diseño, arquitectura | ✅ Sí |
| **Datos de uso** | `/data/` | Eventos, bitácoras, capturas, resúmenes, artifacts | ❌ No |

### Razones de la Exclusión

1. **Confidencialidad**: Los datos de uso pueden contener información sensible del usuario (nombres de proyectos, rutas, errores específicos, etc.)

2. **Separación de concerns**: Evita confundir datos de runtime con documentos de desarrollo

3. **Commits limpios**: Previene commits accidentales de datos generados automáticamente

4. **Escalabilidad**: Los datos crecen con el uso, mientras que la documentación es relativamente estable

5. **Multi-proyecto**: Permite usar `/dia` con múltiples proyectos sin mezclar datos

---

## Opción B2: Estrategia Híbrida de Gestión de Datos

Desde v0.1.1, `/dia` implementa una **estrategia híbrida (Opción B2)** que combina flexibilidad y conveniencia.

### Prioridad de Resolución

El sistema determina dónde almacenar los datos siguiendo este orden de prioridad:

#### 1. Soberanía Explícita (`--data-root`)

**Máxima prioridad**: Si se especifica `--data-root`, se usa esa ruta sin excepciones.

```bash
dia start --data-root /ruta/personalizada/data --area it
```

**Uso recomendado**: Cuando necesitas control total sobre la ubicación de los datos.

#### 2. Datos Locales por Proyecto (`.dia/`)

Si no se especifica `--data-root`, el sistema busca un directorio `.dia/` en la raíz del repositorio donde se ejecuta el comando.

```bash
# Si estás en /ruta/al/proyecto y existe .dia/
cd /ruta/al/proyecto
dia start --area it  # Usa automáticamente .dia/
```

**Ventajas**:
- Datos específicos por proyecto
- Fácil de respaldar junto con el proyecto
- Aislado de otros proyectos

**Desventajas**:
- Requiere crear `.dia/` manualmente si no existe
- Los datos están en el mismo sistema de archivos que el código

#### 3. Data Global según OS (Fallback)

Si no existe `.dia/` en el repo, el sistema usa un directorio global según el sistema operativo:

| OS | Ubicación |
|----|-----------|
| **macOS** | `~/Library/Application Support/dia/` |
| **Linux** | `~/.local/share/dia/` (o `$XDG_DATA_HOME/dia/` si está definido) |
| **Windows** | `%APPDATA%/dia/` (o `~/AppData/Roaming/dia/`) |

**Ventajas**:
- Funciona automáticamente sin configuración
- Centraliza datos de todos los proyectos
- Sigue convenciones del sistema operativo

**Desventajas**:
- Mezcla datos de múltiples proyectos en un solo lugar
- Puede ser menos intuitivo para respaldos por proyecto

---

## Estructura del Directorio `/data`

El directorio `/data` (donde quiera que esté ubicado) tiene la siguiente estructura:

```
data/
├── index/                    # Índices append-only
│   ├── events.ndjson        # Todos los eventos registrados
│   ├── sessions.ndjson      # Registro de sesiones
│   └── summaries.ndjson     # Índice de resúmenes generados
│
├── bitacora/                # Bitácoras de jornada
│   ├── YYYY-MM-DD.md       # Bitácora principal del día
│   └── YYYY-MM-DD/         # Bitácoras de sesiones individuales
│       ├── S01.md
│       ├── CIERRE_S01.md
│       └── LIMPIEZA_S01.md
│
├── artifacts/               # Artefactos generados
│   ├── captures/           # Capturas de errores/logs
│   │   └── YYYY-MM-DD/
│   │       └── Sxx/
│   │           ├── cap_<id>.txt
│   │           └── cap_<id>.meta.json
│   ├── summaries/          # Resúmenes regenerables
│   │   └── YYYY-MM-DD/
│   │       ├── rolling_<timestamp>.md
│   │       └── rolling_<timestamp>.json
│   ├── snapshots/          # Snapshots de repositorios
│   ├── proposals/          # Propuestas (futuro)
│   └── Sxx_repo_diff_*.patch  # Diffs de sesiones
│
├── analysis/               # Análisis generados
│   └── YYYY-MM-DD_vs_objetivo.md
│
├── docs_temp/              # Documentación temporal (fuera del repo)
│
├── rules/                  # Reglas personalizadas por proyecto
│   └── repo_structure.json
│
└── rules.json              # Configuración de reglas globales
```

### Descripción de Directorios

- **`index/`**: Archivos NDJSON append-only que funcionan como índices inmutables
- **`bitacora/`**: Bitácoras editables (secciones manuales) y automáticas (append-only)
- **`artifacts/`**: Archivos generados automáticamente (capturas, diffs, resúmenes)
- **`analysis/`**: Análisis comparativos generados por `dia close-day`
- **`docs_temp/`**: Documentación temporal que no debe estar en el repo
- **`rules/`**: Reglas personalizadas que pueden sobrescribir defaults versionados

---

## Configuración en Docker

El servidor Django necesita acceso al mismo directorio de datos que el CLI para mantener consistencia.

### Configuración Actual (`docker-compose.yml`)

```yaml
services:
  server:
    environment:
      - DIA_DATA_ROOT=/data-global
    volumes:
      # Montar el directorio global de dia (macOS)
      - ${HOME}/Library/Application Support/dia:/data-global
      # Montar también ./data local por si se necesita (legacy)
      - ./data:/data-local
```

### Comportamiento

1. **Variable de entorno `DIA_DATA_ROOT`**: El servidor usa esta variable para determinar dónde buscar los datos
2. **Volumen montado**: Se monta el directorio global del sistema operativo para que el servidor acceda a los mismos datos que el CLI
3. **Legacy `./data`**: Se mantiene por compatibilidad, pero no se usa por defecto

### Alineación CLI-Servidor

Tanto el CLI como el servidor Django usan la misma lógica para determinar `data_root`:

1. **CLI**: `data_root(override, repo_path)` en `cli/dia_cli/config.py`
2. **Servidor**: `_get_data_root()` en `server/dia_server/settings.py`

Ambos respetan:
- Soberanía explícita (CLI: `--data-root`, Servidor: `DIA_DATA_ROOT`)
- Fallback a data global según OS

---

## Migración desde v0.1.0 (Opción A)

Si tenías `/data` dentro del repositorio en v0.1.0, la migración a Opción B2 es automática:

1. **`.gitignore` actualizado**: `data/` y `.dia/` están excluidos
2. **Datos existentes**: Si tenías `data/` en el repo, sigue funcionando localmente pero ya no se trackea
3. **Nuevos datos**: Se crean según Opción B2 (`.dia/` local o data global)

### Recomendación de Migración

1. **Mover datos existentes** (opcional):
   ```bash
   # Si quieres usar .dia/ local
   mv data .dia
   
   # O si prefieres data global
   mv data/* ~/Library/Application\ Support/dia/
   ```

2. **Verificar funcionamiento**:
   ```bash
   dia start --area it
   # El sistema creará la estructura necesaria automáticamente
   ```

---

## Buenas Prácticas

### Para Desarrollo Local

- **Usa `.dia/` local**: Si trabajas en un proyecto específico, crea `.dia/` en la raíz del repo
- **Respaldos**: Incluye `.dia/` en tus respaldos del proyecto si es relevante

### Para Uso Multi-proyecto

- **Usa data global**: Deja que el sistema use el fallback global para centralizar datos
- **O usa `--data-root`**: Si necesitas separar datos por contexto o entorno

### Para Producción/Docker

- **Variable de entorno**: Siempre define `DIA_DATA_ROOT` explícitamente
- **Volúmenes persistentes**: Monta el directorio de datos como volumen persistente
- **Backups**: Incluye el directorio de datos en tus estrategias de backup

---

## Referencias

- **Implementación CLI**: [`cli/dia_cli/config.py`](../../cli/dia_cli/config.py)
- **Implementación Servidor**: [`server/dia_server/settings.py`](../../server/dia_server/settings.py)
- **Docker Compose**: [`docker-compose.yml`](../../docker-compose.yml)
- **Historial**: Commit `afcce74` - "chore: stop tracking runtime data (Opcion B)"

---

**Última actualización**: 2026-01-19
