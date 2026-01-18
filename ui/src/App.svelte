<script>
  import { onMount } from "svelte";
  import BitacoraViewer from "./components/BitacoraViewer.svelte";
  import SummariesViewer from "./components/SummariesViewer.svelte";
  import DocsViewer from "./components/DocsViewer.svelte";
  import BoardView from "./components/BoardView.svelte";

  const API_BASE = import.meta.env.VITE_API_BASE || "/api";

  let sessions = [];
  let currentSession = null;
  let summaries = [];
  let latestRollingSummary = null;
  let rollingTimeline = [];
  let metrics = {};
  let openErrors = [];
  let dayToday = null; // Información del día actual
  let loading = true; // Solo para carga inicial
  let today = new Date().toISOString().split("T")[0]; // YYYY-MM-DD
  let activeTab = "overview"; // overview, bitacora, summaries, docs
  let boardOpen = false; // Control de visibilidad del board
  let zonaVivaElement = null; // Referencia al contenedor de zona viva para preservar scroll

  const fetchJson = async (path) => {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const getAssessmentEmoji = (assessment) => {
    const emojis = {
      "ON_TRACK": "✅",
      "OFF_TRACK": "⚠️",
      "BLOCKED": "🚫",
    };
    return emojis[assessment] || "❓";
  };

  // Carga inicial completa (con indicador de carga)
  const load = async () => {
    loading = true;
    try {
      const [sessionsRes, currentRes, summariesRes, latestRes, timelineRes, metricsRes, errorsRes, dayTodayRes] =
        await Promise.all([
          fetchJson("/sessions/"),
          fetchJson("/sessions/current/"),
          fetchJson("/summaries/"),
          fetchJson(`/summaries/latest/?day_id=${today}&mode=rolling`),
          fetchJson(`/summaries/?day_id=${today}&mode=rolling&limit=20`),
          fetchJson("/metrics/"),
          fetchJson("/captures/errors/open/"),
          fetchJson("/day/today/"),
        ]);
      sessions = sessionsRes.sessions || [];
      currentSession = currentRes.session;
      summaries = summariesRes.summaries || [];
      latestRollingSummary = latestRes.summary;
      rollingTimeline = timelineRes.summaries || [];
      metrics = metricsRes || {};
      openErrors = errorsRes.errors || [];
      dayToday = dayTodayRes || null;
    } catch (error) {
      console.error(error);
    } finally {
      loading = false;
    }
  };

  // Actualización incremental sin parpadeo (preserva estado de UI)
  const loadIncremental = async () => {
    // Preservar posición de scroll antes de actualizar
    const scrollTop = zonaVivaElement?.scrollTop || 0;
    
    try {
      const [sessionsRes, currentRes, summariesRes, latestRes, timelineRes, metricsRes, errorsRes, dayTodayRes] =
        await Promise.all([
          fetchJson("/sessions/"),
          fetchJson("/sessions/current/"),
          fetchJson("/summaries/"),
          fetchJson(`/summaries/latest/?day_id=${today}&mode=rolling`),
          fetchJson(`/summaries/?day_id=${today}&mode=rolling&limit=20`),
          fetchJson("/metrics/"),
          fetchJson("/captures/errors/open/"),
          fetchJson("/day/today/"),
        ]);
      
      // Actualizar datos sin causar parpadeo
      sessions = sessionsRes.sessions || [];
      currentSession = currentRes.session;
      summaries = summariesRes.summaries || [];
      latestRollingSummary = latestRes.summary;
      rollingTimeline = timelineRes.summaries || [];
      metrics = metricsRes || {};
      openErrors = errorsRes.errors || [];
      dayToday = dayTodayRes || null;
      
      // Restaurar posición de scroll después de la actualización
      requestAnimationFrame(() => {
        if (zonaVivaElement) {
          zonaVivaElement.scrollTop = scrollTop;
        }
      });
    } catch (error) {
      console.error("Error en actualización incremental:", error);
      // No mostrar error al usuario para no interrumpir
    }
    // No establecer loading = true/false para evitar parpadeo
  };

  const formatElapsed = (minutes) => {
    if (minutes === null || minutes === undefined) return "—";
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  let intervalId = null;

  onMount(() => {
    // Carga inicial completa
    load();
    
    // Función para iniciar polling incremental
    const startPolling = () => {
      if (intervalId) clearInterval(intervalId);
      intervalId = setInterval(loadIncremental, 5000);
    };
    
    // Función para detener polling
    const stopPolling = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
    
    // Manejar visibilidad de la página (Page Visibility API)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Pausar cuando la ventana no está visible
        stopPolling();
      } else {
        // Cargar datos frescos al volver y reanudar polling
        load();
        startPolling();
      }
    };
    
    // Iniciar polling incremental
    startPolling();
    
    // Escuchar cambios de visibilidad
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Cleanup al desmontar
    return () => {
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  });

  // Obtener ID del board (session_id o day_id)
  $: boardId = currentSession?.session_id || today;

  function openBoard() {
    boardOpen = true;
  }

  function closeBoard() {
    boardOpen = false;
  }

  function handleErrorTooltipPosition(event, tooltipElement) {
    if (!tooltipElement) return;
    
    const button = event.currentTarget;
    if (!button) return;
    
    const rect = button.getBoundingClientRect();
    const tooltipWidth = 300;
    const spacing = 8;
    
    // Calcular posición inicial (debajo del botón)
    let tooltipTop = rect.bottom + spacing;
    let tooltipLeft = rect.left;
    
    // Asegurar que no se salga de la pantalla por la izquierda
    if (tooltipLeft < 0) {
      tooltipLeft = 0;
    }
    
    // Asegurar que no se salga de la pantalla por la derecha
    const screenMaxLeft = window.innerWidth - tooltipWidth;
    if (tooltipLeft > screenMaxLeft) {
      tooltipLeft = screenMaxLeft;
    }
    
    // Usar requestAnimationFrame para asegurar que los estilos se apliquen correctamente
    requestAnimationFrame(() => {
      // Obtener altura real después de renderizar
      const tooltipHeight = tooltipElement.offsetHeight || 200;
      
      // Asegurar que no se salga de la pantalla por abajo
      const screenMaxTop = window.innerHeight - tooltipHeight - spacing;
      if (tooltipTop > screenMaxTop) {
        // Si no cabe abajo, ponerlo arriba del botón
        tooltipTop = rect.top - tooltipHeight - spacing;
        // Si tampoco cabe arriba, ajustar al máximo disponible
        if (tooltipTop < 0) {
          tooltipTop = spacing;
          // Limitar altura si es necesario
          tooltipElement.style.maxHeight = `${window.innerHeight - tooltipTop - spacing * 2}px`;
          tooltipElement.style.overflowY = 'auto';
        } else {
          tooltipElement.style.maxHeight = '400px';
          tooltipElement.style.overflowY = 'auto';
        }
      } else {
        tooltipElement.style.maxHeight = '400px';
        tooltipElement.style.overflowY = 'auto';
      }
      
      tooltipElement.style.top = `${tooltipTop}px`;
      tooltipElement.style.left = `${tooltipLeft}px`;
      tooltipElement.style.opacity = '1';
      tooltipElement.style.visibility = 'visible';
      tooltipElement.style.pointerEvents = 'auto';
      tooltipElement.style.display = 'block';
    });
  }
</script>

<div class="main-container">
  <div class="page" class:docs-fullscreen={activeTab === "docs" || activeTab === "bitacora" || activeTab === "summaries"}>
  <section class="panel">
    <h2>Zona indeleble</h2>
    <div class="tabs">
      <button
        class="tab-button"
        class:active={activeTab === "overview"}
        on:click={() => (activeTab = "overview")}
      >
        Resumen
      </button>
      <button
        class="tab-button"
        class:active={activeTab === "bitacora"}
        on:click={() => (activeTab = "bitacora")}
      >
        Bitácora
      </button>
      <button
        class="tab-button"
        class:active={activeTab === "summaries"}
        on:click={() => (activeTab = "summaries")}
      >
        Resúmenes
      </button>
      <button
        class="tab-button"
        class:active={activeTab === "docs"}
        on:click={() => (activeTab = "docs")}
      >
        Documentación
      </button>
    </div>

    {#if activeTab === "overview"}
      <div class="tab-content">
        {#if loading}
          <div class="loading-state">
            <p class="muted">Cargando...</p>
          </div>
        {:else}
          <div class="metrics-grid">
          <div class="metric-card">
            <div class="metric-value">{dayToday?.sessions_count ?? 0}</div>
            <div class="metric-label">
              Sesiones hoy
              {#if currentSession?.actor?.user_id}
                <span class="user-name">({currentSession.actor.user_id})</span>
              {/if}
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{metrics.total_sessions ?? 0}</div>
            <div class="metric-label">Sesiones totales</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{summaries.length}</div>
            <div class="metric-label">Resúmenes</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{openErrors.length}</div>
            <div class="metric-label">Errores abiertos</div>
          </div>
        </div>
        <h3>Timeline de veredictos (rolling)</h3>
        <div class="list">
          {#if rollingTimeline.length > 0}
            {#each rollingTimeline as summary, index}
              {@const assessment = summary.payload?.assessment || "UNKNOWN"}
              {@const prevAssessment = index > 0 ? rollingTimeline[index - 1].payload?.assessment : null}
              {@const changed = prevAssessment && prevAssessment !== assessment}
              <div class="card">
                <div class="card-header">
                  <div class="mono">
                    {getAssessmentEmoji(assessment)} {assessment}
                    {#if changed}
                      <span class="muted">(cambió de {prevAssessment})</span>
                    {/if}
                  </div>
                </div>
                <div class="card-body">
                  <div class="muted">
                    {summary.ts ? new Date(summary.ts).toLocaleString() : "N/A"}
                  </div>
                  {#if summary.payload?.next_step}
                    <div class="muted">Próximo: {summary.payload.next_step}</div>
                  {/if}
                </div>
              </div>
            {/each}
          {:else}
            <div class="empty-state">
              <p class="muted">Sin resúmenes rolling. Ejecuta 'dia summarize --mode rolling' para generar.</p>
            </div>
          {/if}
          </div>
        {/if}
      </div>
    {:else if activeTab === "bitacora"}
      <div class="tab-content">
        <BitacoraViewer apiBase={API_BASE} initialDayId={today} />
      </div>
    {:else if activeTab === "summaries"}
      <div class="tab-content">
        <SummariesViewer apiBase={API_BASE} initialDayId={today} />
      </div>
    {:else if activeTab === "docs"}
      <div class="tab-content">
        <DocsViewer apiBase={API_BASE} />
      </div>
    {/if}
  </section>

  <section class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-lg);">
      <h2 style="margin: 0;">Zona viva</h2>
      <button 
        class="btn-open-board"
        on:click={openBoard}
        title="Abrir Feature Board"
      >
        Abrir Board
      </button>
    </div>
    <div class="tab-content zona-viva-content" bind:this={zonaVivaElement}>
      {#if loading}
      <div class="loading-state">
        <p class="muted">Cargando...</p>
      </div>
    {:else}
      {#if currentSession}
        <div class="card session-card">
          <div class="card-header">
            <div class="mono session-id">
              {currentSession.day_id} {currentSession.session_id}
            </div>
          </div>
          <div class="card-body">
            <div class="session-intent">{currentSession.intent}</div>
            <div class="session-details">
              <div class="detail-item">
                <span class="detail-label">DoD:</span>
                <span class="muted">{currentSession.dod}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Repo:</span>
                <span class="muted mono">{currentSession.repo?.path || "N/A"}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">Branch:</span>
                <span class="muted mono">{currentSession.repo?.branch || "N/A"}</span>
              </div>
            </div>
          </div>
        </div>
      {:else}
        <div class="empty-state">
          <p class="muted">No hay sesión activa.</p>
        </div>
      {/if}
      <h3>Sesiones de hoy</h3>
      {#if dayToday && dayToday.sessions && dayToday.sessions.length > 0}
        <div class="list">
          {#each dayToday.sessions as session}
            <div class="card session-card-small">
              <div class="card-header">
                <div class="mono">
                  {session.session_id}
                  {#if session.active}
                    <span class="badge-active">Activa</span>
                  {/if}
                </div>
              </div>
              <div class="card-body">
                {#if session.intent}
                  <div class="session-intent-small">{session.intent}</div>
                {/if}
                <div class="session-details-small">
                  <div class="detail-item">
                    <span class="detail-label">Inicio:</span>
                    <span class="muted">
                      {session.start_ts ? new Date(session.start_ts).toLocaleTimeString() : "N/A"}
                    </span>
                  </div>
                  {#if session.end_ts}
                    <div class="detail-item">
                      <span class="detail-label">Fin:</span>
                      <span class="muted">
                        {new Date(session.end_ts).toLocaleTimeString()}
                      </span>
                    </div>
                  {/if}
                  <div class="detail-item">
                    <span class="detail-label">Duración:</span>
                    <span class="muted">{formatElapsed(session.elapsed_minutes)}</span>
                  </div>
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <div class="empty-state">
          <p class="muted">No hay sesiones iniciadas hoy.</p>
        </div>
      {/if}
      <h3>Checklist diario</h3>
      <ul>
        <li>Sesión abierta con intención clara</li>
        <li>Repo limpio o cambios conscientes</li>
        <li>Checkpoint pre-feat ejecutado</li>
        <li>Plan de cierre listo</li>
      </ul>
      <h3>Último resumen rolling</h3>
      {#if latestRollingSummary}
        {@const assessment = latestRollingSummary.payload?.assessment || "UNKNOWN"}
        <div class="card">
          <div class="card-header">
            <div class="mono">
              {getAssessmentEmoji(assessment)} {assessment}
            </div>
          </div>
          <div class="card-body">
            <div class="muted">
              {latestRollingSummary.ts ? new Date(latestRollingSummary.ts).toLocaleString() : "N/A"}
            </div>
            <div><strong>Objetivo:</strong> {latestRollingSummary.payload?.objective || "No especificado"}</div>
            <div><strong>Próximo paso:</strong> {latestRollingSummary.payload?.next_step || "N/A"}</div>
            {#if latestRollingSummary.payload?.blocker}
              <div class="error-text"><strong>Blocker:</strong> {latestRollingSummary.payload.blocker}</div>
            {/if}
            {#if latestRollingSummary.payload?.risks && latestRollingSummary.payload.risks.length > 0}
              <div><strong>Riesgos:</strong></div>
              <ul>
                {#each latestRollingSummary.payload.risks as risk}
                  <li class="muted">{risk}</li>
                {/each}
              </ul>
            {/if}
          </div>
        </div>
        <div style="margin-top: 1rem;">
          <button 
            class="btn-regenerate"
            onclick="alert('Comando sugerido:\ndia summarize --scope day --mode rolling')"
            title="Muestra comando para regenerar resumen"
          >
            Regenerar ahora
          </button>
        </div>
      {:else}
        <div class="empty-state">
          <p class="muted">No hay resumen rolling. Ejecuta 'dia summarize --mode rolling' para generar.</p>
        </div>
      {/if}
      <h3>Errores abiertos</h3>
      {#if openErrors.length > 0}
        <div class="errors-container">
          <div class="errors-header">
            <div class="errors-header-title">⚠️ {openErrors.length} {openErrors.length === 1 ? 'error' : 'errores'} abierto{openErrors.length === 1 ? '' : 's'}</div>
            {#if openErrors.length > 10}
              <div class="errors-header-subtitle">Mostrando los 10 más recientes</div>
            {/if}
          </div>
          <div class="errors-stack">
            {#each openErrors.slice(0, 10) as error, index}
              {@const errorTitle = error.title || "Sin título"}
              {@const errorSession = error.session?.session_id || "N/A"}
              {@const errorDate = error.ts ? new Date(error.ts).toLocaleString() : "N/A"}
              
              <div 
                class="error-item"
                style="z-index: {openErrors.length - index};"
              >
                <button
                  class="error-tab"
                  on:mouseenter={(e) => {
                    const button = e.currentTarget;
                    const tooltip = button.querySelector('.error-content');
                    if (tooltip) {
                      handleErrorTooltipPosition(e, tooltip);
                    }
                  }}
                  on:mouseleave={(e) => {
                    const button = e.currentTarget;
                    const tooltip = button.querySelector('.error-content');
                    if (tooltip) {
                      setTimeout(() => {
                        tooltip.style.opacity = '0';
                        tooltip.style.visibility = 'hidden';
                        tooltip.style.pointerEvents = 'none';
                      }, 150);
                    }
                  }}
                  type="button"
                >
                  <span class="error-tab-title">{errorTitle}</span>
                  
                  <!-- Tooltip con detalles -->
                  <div class="error-content">
                    <h4 class="error-content-title">{errorTitle}</h4>
                    <div class="error-content-meta">
                      <div class="error-meta-item">
                        <span class="error-meta-label">Sesión:</span>
                        <span class="error-meta-value">{errorSession}</span>
                      </div>
                      <div class="error-meta-item">
                        <span class="error-meta-label">Fecha:</span>
                        <span class="error-meta-value">{errorDate}</span>
                      </div>
                      {#if error.artifact_ref}
                        <div class="error-meta-item">
                          <span class="error-meta-label">Artifact:</span>
                          <span class="error-meta-value mono">{error.artifact_ref}</span>
                        </div>
                      {/if}
                    </div>
                  </div>
                </button>
              </div>
            {/each}
          </div>
        </div>
      {:else}
        <div class="empty-state">
          <p class="muted">No hay errores abiertos.</p>
        </div>
      {/if}
      {/if}
    </div>
  </section>
  </div>
  
  {#if boardOpen}
    <BoardView boardId={boardId} onClose={closeBoard} />
  {/if}
</div>
