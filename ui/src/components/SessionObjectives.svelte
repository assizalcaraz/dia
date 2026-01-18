<script>
  export let session = null; // Sesión activa
</script>

{#if session}
  <div class="objectives-card">
    <div class="objectives-header">
      <h3 class="objectives-title">Objetivos de la sesión activa</h3>
      <span class="session-badge">{session.session_id}</span>
    </div>
    <div class="objectives-body">
      <div class="objective-item">
        <span class="objective-label">Objetivo:</span>
        <span class="objective-value">{session.intent || "No especificado"}</span>
      </div>
      <div class="objective-item">
        <span class="objective-label">DoD:</span>
        <span class="objective-value">{session.dod || "No especificado"}</span>
      </div>
    </div>
  </div>
{:else}
  <div class="empty-state">
    <p class="muted">No hay sesión activa.</p>
  </div>
{/if}

<style>
  .objectives-card {
    border: 2px solid var(--color-border-strong);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    background: var(--color-surface);
    margin-bottom: var(--spacing-lg);
    transition: var(--transition);
  }

  .objectives-card:hover {
    box-shadow: var(--shadow-sm);
  }

  .objectives-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border);
  }

  .objectives-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--color-text);
  }

  .session-badge {
    display: inline-block;
    padding: 4px 8px;
    background: var(--color-border-strong);
    color: var(--color-bg);
    border-radius: var(--radius-sm);
    font-size: 12px;
    font-weight: 600;
    font-family: ui-monospace, SFMono-Regular, "Cascadia Code", "Roboto Mono", Menlo, Consolas, monospace;
    letter-spacing: 0.05em;
  }

  .objectives-body {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .objective-item {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .objective-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .objective-value {
    font-size: 15px;
    font-weight: 500;
    color: var(--color-text);
    line-height: 1.5;
  }
</style>
