# Tips: Usar CLI dia durante Desarrollo

**Versión**: v0.1  
**Audiencia**: Desarrolladores trabajando en el proyecto /dia

Guía práctica de cómo usar el CLI `dia` mientras desarrollas funcionalidades, con ejemplos específicos para el desarrollo del Feature Board.

---

## Workflow Recomendado

### 1. Iniciar Sesión de Desarrollo

```bash
# Desde el directorio del proyecto /dia
cd /Users/joseassizalcarazbaxter/Developer/dia

# Iniciar sesión con intención clara
dia start \
  --data-root ./data \
  --area it \
  --intent "Implementar Feature Board Fase 1" \
  --dod "BoardView fullscreen funcional con toggle desde Zona viva, persistencia en localStorage, componentes BoardElement renderizando correctamente según tipo, stores de Svelte operativos, y estilos fullscreen aplicados sin errores en consola"
```

**Tips**:
- Usa `--intent` para describir qué vas a hacer (1 frase)
- Usa `--dod` para definir criterios de completitud (puede ser multilínea)
- El DoD debe ser verificable y específico

### 2. Durante el Desarrollo

#### Capturar Errores

Cuando encuentres un error o problema:

```bash
# Capturar error de compilación
npm run dev 2>&1 | dia cap \
  --kind error \
  --title "Error de TypeScript en BoardView.svelte" \
  --data-root ./data \
  --area it

# Capturar error de runtime (desde consola del navegador)
echo "TypeError: Cannot read property 'position' of undefined" | dia cap \
  --kind error \
  --title "Error en BoardElement al renderizar elemento undefined" \
  --data-root ./data \
  --area it
```

**Tips**:
- Captura errores inmediatamente cuando ocurren
- Usa títulos descriptivos que expliquen el contexto
- El `artifact_ref` se genera automáticamente

#### Checkpoint Pre-Feat

Antes de hacer un commit importante (feature completa, fix crítico):

```bash
dia pre-feat --data-root ./data --area it
```

Esto:
- Sugiere mensaje de commit con formato correcto
- Incluye referencia a sesión actual `[#sesion S02]`
- Si hay errores abiertos, los menciona en el mensaje

**Ejemplo de output**:
```
Mensaje sugerido:
🦾 feat: implementar Feature Board Fase 1 (infraestructura base) [#sesion S02]

Archivos modificados:
- ui/src/App.svelte
- ui/src/app.css
- ui/src/components/BoardView.svelte (nuevo)
- ui/src/components/BoardElement.svelte (nuevo)
- ui/src/stores/boardStore.js (nuevo)
- ui/src/types/board.ts (nuevo)
```

### 3. Cerrar Sesión

Al terminar el trabajo del día o completar una feature:

```bash
dia end --data-root ./data --area it
```

Esto genera:
- `CIERRE_S02.md`: Resumen de lo hecho, decisiones, errores
- `LIMPIEZA_S02.md`: Checklist de limpieza (commits pendientes, etc.)

---

## Casos de Uso Específicos

### Desarrollo de Feature Board

#### Inicio de Sesión

```bash
dia start \
  --data-root ./data \
  --area it \
  --intent "Implementar Feature Board Fase 1: infraestructura base" \
  --dod "BoardView fullscreen funcional con toggle desde Zona viva, persistencia en localStorage, componentes BoardElement renderizando correctamente según tipo, stores de Svelte operativos, y estilos fullscreen aplicados sin errores en consola"
```

#### Durante Implementación

1. **Crear componente nuevo**:
   ```bash
   # No requiere captura, solo documentar en el commit
   ```

2. **Encontrar error de compilación**:
   ```bash
   # Error: Unexpected token en BoardView.svelte
   echo "Error: TypeScript no configurado en Svelte" | dia cap \
     --kind error \
     --title "BoardView.svelte requiere preprocesador TypeScript" \
     --data-root ./data \
     --area it
   ```

3. **Fix aplicado**:
   ```bash
   # Después de convertir a JavaScript
   dia fix \
     --title "Convertir componentes TypeScript a JavaScript" \
     --data-root ./data \
     --area it
   ```

4. **Checkpoint antes de commit**:
   ```bash
   dia pre-feat --data-root ./data --area it
   ```

#### Cierre de Sesión

```bash
dia end --data-root ./data --area it
```

Revisa los archivos generados:
- `data/bitacora/2026-01-17/CIERRE_S02.md`
- `data/bitacora/2026-01-17/LIMPIEZA_S02.md`

---

## Tips Avanzados

### 1. DoD Detallado vs Simple

**Simple** (para tareas pequeñas):
```
DoD: Feature implementada y funcionando
```

**Detallado** (para features complejas):
```
DoD: Feature Board Fase 1 completa cuando:
- BoardView.svelte creado con canvas básico
- BoardElement.svelte renderizando elementos según tipo
- boardStore.ts con persistencia localStorage
- Botón "Abrir Board" en Zona viva
- Sin errores en consola
```

### 2. Capturar Errores de Forma Efectiva

**Buen título**:
```bash
dia cap --title "BoardElement falla con elemento undefined" ...
```

**Mal título**:
```bash
dia cap --title "Error" ...  # Muy genérico
```

### 3. Usar pre-feat Antes de Commits Importantes

No uses `pre-feat` para cada commit pequeño. Úsalo para:
- Features completas
- Fixes críticos
- Cambios que afectan múltiples archivos
- Puntos de rollback importantes

### 4. Revisar Bitácora Durante Desarrollo

```bash
# Ver bitácora del día actual
cat data/bitacora/$(date +%Y-%m-%d).md

# Ver bitácora de sesión específica
cat data/bitacora/2026-01-17/S02.md
```

### 5. Múltiples Sesiones en un Día

Puedes tener múltiples sesiones en un día:

```bash
# Sesión 1: Mañana
dia start --intent "Implementar BoardView" ...

# Trabajar...

dia end

# Sesión 2: Tarde
dia start --intent "Agregar drag & drop" ...

# Trabajar...

dia end
```

Cada sesión genera su propio `CIERRE_SXX.md` y `LIMPIEZA_SXX.md`.

---

## Integración con Git

### Workflow Recomendado

1. **Iniciar sesión**: `dia start`
2. **Desarrollar**: Hacer cambios, probar
3. **Capturar errores**: `dia cap` cuando ocurran
4. **Checkpoint**: `dia pre-feat` antes de commit importante
5. **Commit**: Usar mensaje sugerido por `dia pre-feat`
6. **Cerrar sesión**: `dia end` al terminar

### Ejemplo Completo

```bash
# 1. Iniciar
dia start --intent "Fix: convertir TypeScript a JavaScript" --dod "Sin errores de compilación" --data-root ./data --area it

# 2. Hacer cambios
# ... editar archivos ...

# 3. Encontrar error
npm run dev 2>&1 | dia cap --kind error --title "Error de sintaxis" --data-root ./data --area it

# 4. Fix
# ... corregir error ...

# 5. Linkear fix
dia fix --title "Corregir sintaxis JavaScript" --data-root ./data --area it

# 6. Checkpoint
dia pre-feat --data-root ./data --area it

# 7. Commit (usar mensaje sugerido)
git add .
git commit -m "🦾 fix: convertir componentes TypeScript a JavaScript [#sesion S02]"

# 8. Cerrar
dia end --data-root ./data --area it
```

---

## Referencias

- [dia start](dia-start.md) - Documentación completa de `dia start`
- [dia pre-feat](dia-pre-feat.md) - Documentación completa de `dia pre-feat`
- [dia end](dia-end.md) - Documentación completa de `dia end`
- [dia cap](dia-cap.md) - Documentación completa de `dia cap`
- [dia fix](dia-fix.md) - Documentación completa de `dia fix`

---

**Última actualización**: 2026-01-17
