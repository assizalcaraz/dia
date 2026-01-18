<script>
  import { onMount } from "svelte";
  import MarkdownRenderer from "./MarkdownRenderer.svelte";

  export let apiBase = "/api";
  export let initialDayId = null;

  let availableDays = [];
  let selectedDayId = initialDayId || new Date().toISOString().split("T")[0];
  let content = "";
  let loading = false;
  let error = null;

  const fetchJson = async (path) => {
    // Asegurar que la ruta empiece con / y apiBase no termine con /
    const cleanPath = path.startsWith("/") ? path : `/${path}`;
    const cleanApiBase = apiBase.endsWith("/") ? apiBase.slice(0, -1) : apiBase;
    const url = `${cleanApiBase}${cleanPath}`;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const loadAvailableDays = async () => {
    try {
      const sessionsRes = await fetchJson("/sessions/");
      const days = new Set();
      sessionsRes.sessions?.forEach((session) => {
        if (session.day_id) {
          days.add(session.day_id);
        }
      });
      availableDays = Array.from(days).sort().reverse();
    } catch (err) {
      console.error("Error cargando días disponibles:", err);
      // No mostrar error aquí, solo loguear
    }
  };

  const loadBitacora = async () => {
    if (!selectedDayId) return;

    loading = true;
    error = null;
    try {
      const data = await fetchJson(`/jornada/${selectedDayId}/`);
      content = data.content || "";
    } catch (err) {
      console.error("Error cargando bitácora:", err);
      error = `Error al cargar bitácora: ${err.message}`;
      content = "";
    } finally {
      loading = false;
    }
  };

  $: if (selectedDayId) {
    loadBitacora();
  }

  onMount(() => {
    loadAvailableDays();
  });
</script>

<div class="bitacora-viewer">
  <div class="viewer-header">
    <label for="day-selector" class="label">Bitácora del día:</label>
    <select id="day-selector" bind:value={selectedDayId} class="day-selector">
      {#each availableDays as day}
        <option value={day}>{day}</option>
      {/each}
      {#if selectedDayId && !availableDays.includes(selectedDayId)}
        <option value={selectedDayId}>{selectedDayId}</option>
      {/if}
    </select>
  </div>

  {#if loading}
    <div class="loading-state">
      <p class="muted">Cargando bitácora...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p class="error-text">{error}</p>
    </div>
  {:else if content}
    <div class="content-wrapper">
      <MarkdownRenderer content={content} />
    </div>
  {:else}
    <div class="empty-state">
      <p class="muted">No hay bitácora disponible para este día.</p>
    </div>
  {/if}
</div>

<style>
  .bitacora-viewer {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    height: 100%;
    overflow: hidden;
    min-width: 0;
    max-width: 100%;
  }

  .viewer-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
    flex-shrink: 0;
  }

  .label {
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text);
  }

  .day-selector {
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg);
    color: var(--color-text);
    font-size: 14px;
    font-family: ui-monospace, SFMono-Regular, "Cascadia Code", "Roboto Mono", Menlo, Consolas, monospace;
    cursor: pointer;
    transition: var(--transition);
  }

  .day-selector:hover {
    border-color: var(--color-border-strong);
  }

  .day-selector:focus {
    outline: none;
    border-color: var(--color-border-strong);
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
  }

  .content-wrapper {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    background: var(--color-bg);
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
    min-width: 0;
    max-width: 100%;
  }

  .loading-state,
  .empty-state,
  .error-state {
    padding: var(--spacing-lg);
    text-align: center;
  }

  .error-text {
    color: #d32f2f;
  }
</style>
