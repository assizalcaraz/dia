<script>
  import { onMount } from "svelte";
  import MarkdownRenderer from "./MarkdownRenderer.svelte";

  export let apiBase = "/api";
  export let initialDayId = null;

  let availableDays = [];
  let selectedDayId = initialDayId || new Date().toISOString().split("T")[0];
  let summaries = [];
  let selectedSummary = null;
  let content = "";
  let loading = false;
  let loadingContent = false;
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

  const getAssessmentEmoji = (assessment) => {
    const emojis = {
      ON_TRACK: "✅",
      OFF_TRACK: "⚠️",
      BLOCKED: "🚫",
    };
    return emojis[assessment] || "❓";
  };

  const loadAvailableDays = async () => {
    try {
      const summariesRes = await fetchJson("/summaries/");
      const days = new Set();
      summariesRes.summaries?.forEach((summary) => {
        const dayId = summary.session?.day_id;
        if (dayId) {
          days.add(dayId);
        }
      });
      availableDays = Array.from(days).sort().reverse();
    } catch (err) {
      console.error("Error cargando días disponibles:", err);
    }
  };

  const loadSummaries = async () => {
    if (!selectedDayId) return;

    loading = true;
    error = null;
    try {
      const data = await fetchJson(`/summaries/${selectedDayId}/list/`);
      summaries = data.summaries || [];
      if (summaries.length > 0 && !selectedSummary) {
        selectedSummary = summaries[0];
      }
    } catch (err) {
      error = `Error al cargar resúmenes: ${err.message}`;
      summaries = [];
    } finally {
      loading = false;
    }
  };

  const loadSummaryContent = async () => {
    if (!selectedSummary || !selectedDayId) return;

    loadingContent = true;
    try {
      const data = await fetchJson(
        `/summaries/${selectedDayId}/${selectedSummary.summary_id}/content/`
      );
      content = data.content || "";
    } catch (err) {
      content = `Error al cargar contenido: ${err.message}`;
    } finally {
      loadingContent = false;
    }
  };

  $: if (selectedDayId) {
    loadSummaries();
    selectedSummary = null;
    content = "";
  }

  $: if (selectedSummary) {
    loadSummaryContent();
  }

  onMount(() => {
    loadAvailableDays();
  });
</script>

<div class="summaries-viewer">
  <div class="viewer-header">
    <label for="day-selector" class="label">Resúmenes del día:</label>
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
      <p class="muted">Cargando resúmenes...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p class="error-text">{error}</p>
    </div>
  {:else if summaries.length === 0}
    <div class="empty-state">
      <p class="muted">No hay resúmenes disponibles para este día.</p>
    </div>
  {:else}
    <div class="summaries-layout">
      <div class="summaries-list">
        <h3 class="list-title">Resúmenes disponibles</h3>
        <div class="list-items">
          {#each summaries as summary}
            {@const isSelected = selectedSummary?.summary_id === summary.summary_id}
            <button
              class="summary-item"
              class:selected={isSelected}
              on:click={() => (selectedSummary = summary)}
            >
              <div class="summary-header">
                <span class="summary-mode">{summary.mode}</span>
                <span class="summary-assessment">
                  {getAssessmentEmoji(summary.assessment)} {summary.assessment}
                </span>
              </div>
              <div class="summary-meta">
                <span class="muted mono">{summary.summary_id}</span>
              </div>
            </button>
          {/each}
        </div>
      </div>

      <div class="summary-content">
        {#if loadingContent}
          <div class="loading-state">
            <p class="muted">Cargando contenido...</p>
          </div>
        {:else if content}
          <div class="content-wrapper">
            <MarkdownRenderer content={content} />
          </div>
        {:else}
          <div class="empty-state">
            <p class="muted">Selecciona un resumen para ver su contenido.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .summaries-viewer {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .viewer-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
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

  .summaries-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: var(--spacing-lg);
    min-height: 400px;
  }

  @media (max-width: 768px) {
    .summaries-layout {
      grid-template-columns: 1fr;
    }
  }

  .summaries-list {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    background: var(--color-surface);
    overflow-y: auto;
    max-height: 70vh;
  }

  .list-title {
    font-size: 14px;
    font-weight: 600;
    margin: 0 0 var(--spacing-md) 0;
    color: var(--color-text);
  }

  .list-items {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .summary-item {
    padding: var(--spacing-md);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg);
    text-align: left;
    cursor: pointer;
    transition: var(--transition);
  }

  .summary-item:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-sm);
  }

  .summary-item.selected {
    border-color: var(--color-border-strong);
    background: var(--color-surface);
  }

  .summary-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-xs);
  }

  .summary-mode {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--color-text-muted);
    letter-spacing: 0.05em;
  }

  .summary-assessment {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-text);
  }

  .summary-meta {
    font-size: 11px;
  }

  .summary-content {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    background: var(--color-bg);
    overflow-y: auto;
    max-height: 70vh;
  }

  .content-wrapper {
    width: 100%;
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
