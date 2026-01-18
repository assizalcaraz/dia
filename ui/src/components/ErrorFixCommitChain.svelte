<script>
  import { onMount } from "svelte";

  export let apiBase = "/api";

  let chain = { error: null, fix: null, commit: null };
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

  const loadChain = async () => {
    loading = true;
    error = null;
    try {
      const data = await fetchJson("/chain/latest/");
      chain = data;
    } catch (err) {
      console.error("Error cargando cadena:", err);
      error = err.message;
    } finally {
      loading = false;
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Comando copiado al portapapeles');
    }).catch(err => {
      console.error('Error al copiar:', err);
    });
  };

  const getFixCommand = () => {
    if (!chain.error) return "";
    const captureId = chain.error.artifact_ref?.match(/cap_[\w]+/)?.[0] || "cap_<id>";
    return `dia fix --from ${captureId} --title "descripción del fix" --area it`;
  };

  const getCommitCommand = () => {
    if (!chain.fix) return "";
    const fixId = chain.fix.fix_id || "fix_<id>";
    return `dia fix-commit --fix ${fixId} --last`;
  };

  onMount(() => {
    loadChain();
    // Refrescar cada 5 segundos
    const interval = setInterval(loadChain, 5000);
    return () => clearInterval(interval);
  });
</script>

<div class="chain-container">
  <h3>Cadena Error → Fix → Commit</h3>
  
  {#if loading}
    <p>Cargando...</p>
  {:else if error}
    <p class="error">Error: {error}</p>
  {:else if !chain.error && !chain.fix && !chain.commit}
    <p class="empty">No hay cadena activa en la sesión actual.</p>
  {:else}
    <div class="chain-steps">
      <!-- Error -->
      <div class="chain-step" class:active={chain.error} class:completed={chain.fix || chain.commit}>
        <div class="step-header">
          <span class="step-number">1</span>
          <span class="step-label">Error</span>
          {#if chain.error}
            <span class="step-status">✓</span>
          {/if}
        </div>
        {#if chain.error}
          <div class="step-content">
            <p class="step-title">{chain.error.title}</p>
            <p class="step-meta">
              {new Date(chain.error.ts).toLocaleString()}
            </p>
            {#if chain.error.artifact_ref}
              <a href="#" class="step-link" on:click|preventDefault>
                Ver artifact
              </a>
            {/if}
          </div>
        {:else}
          <div class="step-content empty">
            <p>No hay error capturado</p>
          </div>
        {/if}
      </div>

      <!-- Fix -->
      <div class="chain-arrow">→</div>
      <div class="chain-step" class:active={chain.fix} class:completed={chain.commit}>
        <div class="step-header">
          <span class="step-number">2</span>
          <span class="step-label">Fix</span>
          {#if chain.fix}
            <span class="step-status">✓</span>
          {/if}
        </div>
        {#if chain.fix}
          <div class="step-content">
            <p class="step-title">{chain.fix.title}</p>
            <p class="step-meta">
              Fix ID: {chain.fix.fix_id}
            </p>
            {#if chain.fix.fix_sha}
              <p class="step-meta">SHA: {chain.fix.fix_sha.substring(0, 8)}...</p>
            {:else}
              <p class="step-meta warning">En working tree (sin commit)</p>
            {/if}
          </div>
        {:else if chain.error}
          <div class="step-content empty">
            <p>Fix pendiente</p>
            <button 
              class="action-button"
              on:click={() => copyToClipboard(getFixCommand())}
              title="Copiar comando sugerido"
            >
              Crear fix
            </button>
            <p class="command-hint">{getFixCommand()}</p>
          </div>
        {:else}
          <div class="step-content empty">
            <p>No aplicable</p>
          </div>
        {/if}
      </div>

      <!-- Commit -->
      <div class="chain-arrow">→</div>
      <div class="chain-step" class:active={chain.commit} class:completed={chain.commit}>
        <div class="step-header">
          <span class="step-number">3</span>
          <span class="step-label">Commit</span>
          {#if chain.commit}
            <span class="step-status">✓</span>
          {/if}
        </div>
        {#if chain.commit}
          <div class="step-content">
            <p class="step-title">Commit linkeado</p>
            <p class="step-meta">
              SHA: {chain.commit.commit_sha.substring(0, 8)}...
            </p>
          </div>
        {:else if chain.fix}
          <div class="step-content empty">
            <p>Commit pendiente</p>
            <button 
              class="action-button"
              on:click={() => copyToClipboard(getCommitCommand())}
              title="Copiar comando sugerido"
            >
              Link commit
            </button>
            <p class="command-hint">{getCommitCommand()}</p>
          </div>
        {:else}
          <div class="step-content empty">
            <p>No aplicable</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .chain-container {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    background: white;
    margin-bottom: 1rem;
  }

  .chain-container h3 {
    margin: 0 0 1rem 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .chain-steps {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .chain-step {
    flex: 1;
    min-width: 150px;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.75rem;
    background: #f9f9f9;
  }

  .chain-step.active {
    border-color: #4a9eff;
    background: #e8f4ff;
  }

  .chain-step.completed {
    border-color: #4caf50;
    background: #e8f5e9;
  }

  .step-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-weight: 600;
  }

  .step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #ddd;
    color: #666;
    font-size: 0.875rem;
  }

  .chain-step.active .step-number {
    background: #4a9eff;
    color: white;
  }

  .chain-step.completed .step-number {
    background: #4caf50;
    color: white;
  }

  .step-label {
    flex: 1;
  }

  .step-status {
    color: #4caf50;
    font-weight: bold;
  }

  .step-content {
    font-size: 0.875rem;
  }

  .step-content.empty {
    color: #999;
    font-style: italic;
  }

  .step-title {
    margin: 0 0 0.25rem 0;
    font-weight: 500;
  }

  .step-meta {
    margin: 0.25rem 0;
    font-size: 0.75rem;
    color: #666;
  }

  .step-meta.warning {
    color: #ff9800;
  }

  .step-link {
    color: #4a9eff;
    text-decoration: none;
    font-size: 0.75rem;
  }

  .step-link:hover {
    text-decoration: underline;
  }

  .chain-arrow {
    align-self: center;
    font-size: 1.5rem;
    color: #999;
    padding: 0 0.5rem;
  }

  .action-button {
    margin-top: 0.5rem;
    padding: 0.375rem 0.75rem;
    background: #4a9eff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
  }

  .action-button:hover {
    background: #357abd;
  }

  .command-hint {
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: #f5f5f5;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.75rem;
    color: #666;
    word-break: break-all;
  }

  .error {
    color: #d32f2f;
    font-size: 0.875rem;
  }

  .empty {
    color: #999;
    font-style: italic;
    font-size: 0.875rem;
  }
</style>
