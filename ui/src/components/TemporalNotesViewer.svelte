<script>
  import { onMount } from "svelte";
  import MarkdownRenderer from "./MarkdownRenderer.svelte";

  export let apiBase = "/api";
  export let dayId = null;

  let files = [];
  let selectedFile = null;
  let selectedContent = "";
  let loading = false;
  let error = null;

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

  const loadFiles = async () => {
    if (!dayId) return;
    
    loading = true;
    error = null;
    
    try {
      const data = await fetchJson(`/notes/tmp/${dayId}/`);
      files = data.files || [];
      error = null;
    } catch (err) {
      if (err.message.includes("404")) {
        files = [];
        error = null;
      } else {
        console.error("Error cargando notas temporales:", err);
        error = `Error al cargar notas: ${err.message}`;
      }
    } finally {
      loading = false;
    }
  };

  const loadFileContent = async (fileName) => {
    loading = true;
    error = null;
    
    try {
      const data = await fetchJson(`/notes/tmp/${dayId}/${fileName}`);
      selectedContent = data.content || "";
      selectedFile = fileName;
      error = null;
    } catch (err) {
      console.error("Error cargando contenido:", err);
      error = `Error al cargar archivo: ${err.message}`;
      selectedContent = "";
    } finally {
      loading = false;
    }
  };

  onMount(() => {
    loadFiles();
  });

  $: if (dayId) {
    loadFiles();
  }
</script>

<div class="temporal-notes-viewer">
  <div class="viewer-header">
    <h3>Notas Temporales</h3>
    <div class="warning-badge">⚠️ TEMPORAL</div>
  </div>

  <div class="warning-box">
    <p class="warning-text">
      <strong>⚠️ Contenido temporal / no canónico / descartable</strong>
    </p>
    <p class="warning-description">
      Estas notas son superficie de trabajo, no documentación. Pueden descartarse sin afectar el sistema.
    </p>
  </div>

  {#if error}
    <div class="error-state">
      <p class="error-text">{error}</p>
    </div>
  {/if}

  {#if loading && files.length === 0}
    <div class="loading-state">
      <p class="muted">Cargando notas temporales...</p>
    </div>
  {:else if files.length === 0}
    <div class="empty-state">
      <p class="muted">No hay notas temporales para este día.</p>
    </div>
  {:else}
    <div class="notes-container">
      <div class="notes-list">
        <h4>Archivos disponibles</h4>
        {#each files as file}
          <button
            class="note-item"
            class:active={selectedFile === file.name}
            on:click={() => loadFileContent(file.name)}
          >
            <span class="note-name">{file.name}</span>
            <span class="note-size">{Math.round(file.size / 1024)} KB</span>
          </button>
        {/each}
      </div>

      <div class="notes-content">
        {#if selectedFile}
          <div class="content-header">
            <h4>{selectedFile}</h4>
            <span class="temporal-badge">TEMPORAL</span>
          </div>
          <div class="content-body">
            <MarkdownRenderer content={selectedContent} />
          </div>
        {:else}
          <div class="empty-content">
            <p class="muted">Selecciona un archivo para ver su contenido</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .temporal-notes-viewer {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .viewer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
  }

  .viewer-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text);
  }

  .warning-badge {
    display: inline-block;
    padding: 4px 8px;
    background: #ff9800;
    color: white;
    border-radius: var(--radius-sm);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .warning-box {
    padding: var(--spacing-md);
    background: #fff3e0;
    border: 2px solid #ff9800;
    border-radius: var(--radius-md);
  }

  .warning-text {
    margin: 0 0 var(--spacing-xs) 0;
    font-size: 14px;
    font-weight: 600;
    color: #e65100;
  }

  .warning-description {
    margin: 0;
    font-size: 13px;
    color: var(--color-text-muted);
    line-height: 1.5;
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

  .notes-container {
    display: grid;
    grid-template-columns: 250px 1fr;
    gap: var(--spacing-lg);
    min-height: 400px;
  }

  @media (max-width: 768px) {
    .notes-container {
      grid-template-columns: 1fr;
    }
  }

  .notes-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    padding: var(--spacing-md);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
  }

  .notes-list h4 {
    margin: 0 0 var(--spacing-md) 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
  }

  .note-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-bg);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition);
    text-align: left;
    font-size: 13px;
  }

  .note-item:hover {
    border-color: var(--color-border-strong);
    background: var(--color-surface);
  }

  .note-item.active {
    border-color: var(--color-border-strong);
    background: var(--color-surface);
    font-weight: 500;
  }

  .note-name {
    color: var(--color-text);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .note-size {
    color: var(--color-text-muted);
    font-size: 11px;
    margin-left: var(--spacing-sm);
  }

  .notes-content {
    display: flex;
    flex-direction: column;
    padding: var(--spacing-md);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    opacity: 0.9;
  }

  .content-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border);
  }

  .content-header h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
  }

  .temporal-badge {
    display: inline-block;
    padding: 2px 6px;
    background: #ff9800;
    color: white;
    border-radius: var(--radius-sm);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .content-body {
    font-size: 13px;
    color: var(--color-text-muted);
    line-height: 1.6;
  }

  .empty-content {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    text-align: center;
  }
</style>
