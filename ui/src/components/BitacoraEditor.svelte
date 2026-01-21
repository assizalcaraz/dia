<script>
  import { onMount } from "svelte";
  import MarkdownRenderer from "./MarkdownRenderer.svelte";

  export let apiBase = "/api";
  export let dayId = null;

  let humanSections = ""; // Secciones 1 y 2 (editables)
  let autoSection = ""; // Sección 3 (read-only)
  let isEditing = false;
  let isSaving = false;
  let lastSaved = null;
  let error = null;
  let saveTimeout = null;

  const fetchJson = async (path) => {
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    const cleanApiBase = apiBase.endsWith("/") ? apiBase.slice(0, -1) : apiBase;
    const url = `${cleanApiBase}${cleanPath}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const parseBitacora = (content) => {
    // Separar por el separador que marca el inicio de sección automática
    const separator = "---\n\n## 3. Registro automático (NO EDITAR)";
    const separatorIndex = content.indexOf(separator);
    
    if (separatorIndex === -1) {
      // No hay sección automática aún, todo es editable
      return {
        human: content,
        auto: ""
      };
    }
    
    return {
      human: content.substring(0, separatorIndex).trim(),
      auto: content.substring(separatorIndex).trim()
    };
  };

  const loadBitacora = async () => {
    if (!dayId) return;
    
    try {
      const data = await fetchJson(`/jornada/${dayId}/`);
      const parsed = parseBitacora(data.content || "");
      humanSections = parsed.human;
      autoSection = parsed.auto;
      error = null;
    } catch (err) {
      if (err.message.includes("404")) {
        // No hay bitácora, inicializar vacía
        humanSections = "";
        autoSection = "";
        error = null;
      } else {
        console.error("Error cargando bitácora:", err);
        error = `Error al cargar bitácora: ${err.message}`;
      }
    }
  };

  const saveBitacora = async () => {
    if (!dayId) return;
    
    isSaving = true;
    error = null;
    
    try {
      const response = await fetch(`${apiBase}/jornada/${dayId}/human/`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: humanSections
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
      
      lastSaved = new Date();
      error = null;
    } catch (err) {
      console.error("Error guardando bitácora:", err);
      error = `Error al guardar: ${err.message}`;
    } finally {
      isSaving = false;
    }
  };

  const handleInput = (e) => {
    humanSections = e.target.value;
    isEditing = true;
    
    // Debounce: guardar después de 2 segundos sin escribir
    if (saveTimeout) {
      clearTimeout(saveTimeout);
    }
    
    saveTimeout = setTimeout(() => {
      saveBitacora();
      isEditing = false;
    }, 2000);
  };

  onMount(() => {
    loadBitacora();
    
    return () => {
      if (saveTimeout) {
        clearTimeout(saveTimeout);
      }
    };
  });

  $: if (dayId) {
    loadBitacora();
  }
</script>

<div class="bitacora-editor">
  <div class="editor-header">
    <h3>Bitácora del día: {dayId}</h3>
    <div class="editor-status">
      {#if isSaving}
        <span class="status-saving">Guardando...</span>
      {:else if lastSaved}
        <span class="status-saved">Guardado {lastSaved.toLocaleTimeString()}</span>
      {:else if isEditing}
        <span class="status-editing">Editando...</span>
      {/if}
    </div>
  </div>

  {#if error}
    <div class="error-state">
      <p class="error-text">{error}</p>
    </div>
  {/if}

  <div class="editor-section">
    <div class="section-header">
      <h4>Secciones editables (1 y 2)</h4>
      <span class="section-badge">Editable</span>
    </div>
    <textarea
      class="editor-textarea"
      bind:value={humanSections}
      on:input={handleInput}
      placeholder="## 1. Intención del día (manual)&#10;- Objetivo principal:&#10;- Definición de Hecho (DoD):&#10;- Restricciones / contexto:&#10;&#10;## 2. Notas humanas (manual)&#10;- ideas&#10;- dudas&#10;- decisiones&#10;- observaciones subjetivas relevantes"
    ></textarea>
  </div>

  {#if autoSection}
    <div class="separator-section">
      <div class="separator-line"></div>
      <div class="separator-text">Sección automática (no editable)</div>
      <div class="separator-line"></div>
    </div>
    
    <div class="readonly-section">
      <div class="section-header">
        <h4>Registro automático (NO EDITAR)</h4>
        <span class="section-badge readonly">Solo lectura</span>
      </div>
      <div class="readonly-content">
        <MarkdownRenderer content={autoSection} />
      </div>
    </div>
  {/if}
</div>

<style>
  .bitacora-editor {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .editor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .editor-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text);
  }

  .editor-status {
    font-size: 12px;
    color: var(--color-text-muted);
  }

  .status-saving {
    color: var(--color-text-muted);
  }

  .status-saved {
    color: #4caf50;
  }

  .status-editing {
    color: var(--color-text-muted);
  }

  .error-state {
    padding: var(--spacing-md);
    background: #ffebee;
    border: 1px solid #ef5350;
    border-radius: var(--radius-md);
  }

  .error-text {
    color: #d32f2f;
    font-size: 14px;
    margin: 0;
  }

  .editor-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .section-header h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
  }

  .section-badge {
    display: inline-block;
    padding: 2px 8px;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 11px;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .section-badge.readonly {
    background: #f5f5f5;
    border-color: var(--color-border-strong);
    color: var(--color-text-muted);
  }

  .editor-textarea {
    width: 100%;
    min-height: 300px;
    padding: var(--spacing-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-family: ui-monospace, SFMono-Regular, "Cascadia Code", "Roboto Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    line-height: 1.6;
    color: var(--color-text);
    background: var(--color-bg);
    resize: vertical;
    transition: var(--transition);
  }

  .editor-textarea:focus {
    outline: none;
    border-color: var(--color-border-strong);
    box-shadow: 0 0 0 2px rgba(26, 26, 26, 0.1);
  }

  .separator-section {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin: var(--spacing-lg) 0;
  }

  .separator-line {
    flex: 1;
    height: 1px;
    background: var(--color-border-strong);
  }

  .separator-text {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
  }

  .readonly-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: #fafafa;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    opacity: 0.8;
  }

  .readonly-content {
    font-size: 13px;
    color: var(--color-text-muted);
  }
</style>
