<script>
  import { onMount, onDestroy } from "svelte";
  import BitacoraViewer from "./components/BitacoraViewer.svelte";
  import SummariesViewer from "./components/SummariesViewer.svelte";
  import DocsViewer from "./components/DocsViewer.svelte";
  import BoardView from "./components/BoardView.svelte";
  import SessionObjectives from "./components/SessionObjectives.svelte";
  import BitacoraEditor from "./components/BitacoraEditor.svelte";
  import TemporalNotesViewer from "./components/TemporalNotesViewer.svelte";
  import ErrorFixCommitChain from "./components/ErrorFixCommitChain.svelte";

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
  // Calcular fecha actual en zona horaria local (no UTC)
  const getLocalDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  let today = getLocalDate(); // YYYY-MM-DD en zona horaria local
  let activeTab = "overview"; // overview, bitacora, summaries, docs, sessions
  let zonaVivaTab = "sesion"; // sesion, bitacora, objetivos, temporales
  let boardOpen = false; // Control de visibilidad del board
  let zonaVivaElement = null; // Referencia al contenedor de zona viva para preservar scroll
  let temporalNotesCount = 0; // Contador de notas temporales
  let archivedErrors = new Set(); // IDs de errores archivados
  let expandedErrors = new Set(); // IDs de errores expandidos en acordeón
  let dayElapsedMinutes = null; // Tiempo transcurrido desde inicio de jornada
  let dayElapsedInterval = null; // Interval para actualizar tiempo transcurrido

  const fetchJson = async (path) => {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const fetchPost = async (path, body = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  };

  // Cargar errores archivados desde localStorage
  const loadArchivedErrors = () => {
    try {
      const stored = localStorage.getItem(`dia_archived_errors_${today}`);
      if (stored) {
        archivedErrors = new Set(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Error cargando errores archivados:", e);
    }
  };

  // Guardar errores archivados en localStorage
  const saveArchivedErrors = () => {
    try {
      localStorage.setItem(`dia_archived_errors_${today}`, JSON.stringify(Array.from(archivedErrors)));
    } catch (e) {
      console.error("Error guardando errores archivados:", e);
    }
  };

  // Archivar un error
  const archiveError = (errorId) => {
    archivedErrors.add(errorId);
    saveArchivedErrors();
  };

  // Calcular tiempo transcurrido desde inicio de jornada
  const calculateDayElapsed = () => {
    if (!dayToday || !dayToday.sessions || dayToday.sessions.length === 0) {
      dayElapsedMinutes = null;
      return;
    }
    
    // Encontrar la primera sesión del día
    const firstSession = dayToday.sessions[dayToday.sessions.length - 1]; // Más antigua
    if (!firstSession || !firstSession.start_ts) {
      dayElapsedMinutes = null;
      return;
    }
    
    const startTime = new Date(firstSession.start_ts);
    const now = new Date();
    const diffMs = now - startTime;
    dayElapsedMinutes = Math.floor(diffMs / 60000);
  };

  // Control de sesión: pausar
  const pauseSession = async () => {
    if (!confirm("¿Pausar la sesión actual?")) {
      return;
    }
    try {
      await fetchPost("/session/pause/");
      await loadIncremental();
    } catch (error) {
      alert(`Error al pausar sesión: ${error.message}`);
    }
  };

  // Control de sesión: retomar
  const resumeSession = async () => {
    if (!confirm("¿Retomar la sesión pausada?")) {
      return;
    }
    try {
      await fetchPost("/session/resume/");
      await loadIncremental();
    } catch (error) {
      alert(`Error al retomar sesión: ${error.message}`);
    }
  };

  // Control de sesión: finalizar
  const endSession = async () => {
    if (!confirm("¿Finalizar la sesión actual? Esta acción no se puede deshacer.")) {
      return;
    }
    try {
      await fetchPost("/session/end/");
      await loadIncremental();
    } catch (error) {
      alert(`Error al finalizar sesión: ${error.message}`);
    }
  };

  // Verificar si la sesión está pausada
  const isSessionPaused = () => {
    if (!currentSession) return false;
    const pausedTs = currentSession.paused_ts;
    const resumedTs = currentSession.resumed_ts;
    if (!pausedTs) return false;
    if (!resumedTs) return true;
    return pausedTs > resumedTs;
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
      const [sessionsRes, activeRes, summariesRes, latestRes, timelineRes, metricsRes, errorsRes, dayTodayRes] =
        await Promise.all([
          fetchJson("/sessions/"),
          fetchJson("/session/active/"),
          fetchJson("/summaries/"),
          fetchJson(`/summaries/latest/?day_id=${today}&mode=rolling`),
          fetchJson(`/summaries/?day_id=${today}&mode=rolling&limit=20`),
          fetchJson("/metrics/"),
          fetchJson("/captures/errors/open/"),
          fetchJson("/day/today/"),
        ]);
      sessions = sessionsRes.sessions || [];
      currentSession = activeRes.session;
      summaries = summariesRes.summaries || [];
      latestRollingSummary = latestRes.summary;
      rollingTimeline = timelineRes.summaries || [];
      metrics = metricsRes || {};
      openErrors = errorsRes.errors || [];
      dayToday = dayTodayRes || null;
      calculateDayElapsed();
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
      const [sessionsRes, activeRes, summariesRes, latestRes, timelineRes, metricsRes, errorsRes, dayTodayRes, temporalNotesRes] =
        await Promise.all([
          fetchJson("/sessions/"),
          fetchJson("/session/active/"),
          fetchJson("/summaries/"),
          fetchJson(`/summaries/latest/?day_id=${today}&mode=rolling`),
          fetchJson(`/summaries/?day_id=${today}&mode=rolling&limit=20`),
          fetchJson("/metrics/"),
          fetchJson("/captures/errors/open/"),
          fetchJson("/day/today/"),
          fetchJson(`/notes/tmp/${today}/`).catch(() => ({ files: [] })),
        ]);
      
      // Actualizar datos sin causar parpadeo
      sessions = sessionsRes.sessions || [];
      currentSession = activeRes.session;
      summaries = summariesRes.summaries || [];
      latestRollingSummary = latestRes.summary;
      rollingTimeline = timelineRes.summaries || [];
      metrics = metricsRes || {};
      openErrors = errorsRes.errors || [];
      dayToday = dayTodayRes || null;
      temporalNotesCount = (temporalNotesRes?.files || []).length;
      
      // Calcular tiempo transcurrido del día
      calculateDayElapsed();
      
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
    // Cargar errores archivados
    loadArchivedErrors();
    
    // Carga inicial completa
    load();
    
    // Iniciar actualización de tiempo transcurrido cada minuto
    dayElapsedInterval = setInterval(() => {
      calculateDayElapsed();
    }, 60000);
    
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
    
    // Cleanup al desmontar
    return () => {
      if (intervalId) clearInterval(intervalId);
      if (dayElapsedInterval) clearInterval(dayElapsedInterval);
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

  function copyErrorContent(error) {
    const lines = [
      `Error: ${error.title || "Sin título"}`,
      `Sesión: ${error.session?.session_id || "N/A"}`,
      `Fecha: ${error.ts ? new Date(error.ts).toLocaleString() : "N/A"}`,
    ];
    
    if (error.artifact_ref) {
      lines.push(`Artifact: ${error.artifact_ref}`);
    }
    
    if (error.error_hash) {
      lines.push(`Hash: ${error.error_hash}`);
    }
    
    const text = lines.join('\n');
    
    navigator.clipboard.writeText(text).then(() => {
      // Feedback visual temporal (opcional)
      console.log('Contenido copiado al portapapeles');
    }).catch(err => {
      console.error('Error al copiar:', err);
    });
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
      <button
        class="tab-button"
        class:active={activeTab === "sessions"}
        on:click={() => (activeTab = "sessions")}
      >
        Sesiones
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
    {:else if activeTab === "sessions"}
      <div class="tab-content">
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
          {@const visibleErrors = openErrors.filter(e => !archivedErrors.has(e.event_id))}
          {@const resolvedErrors = visibleErrors.filter(e => e.has_fix)}
          {@const unresolvedErrors = visibleErrors.filter(e => !e.has_fix)}
          {#if visibleErrors.length > 0}
          <div class="errors-container">
            <div class="errors-header">
              <div class="errors-header-title">
                ⚠️ {unresolvedErrors.length} {unresolvedErrors.length === 1 ? 'error' : 'errores'} sin resolver
                {#if resolvedErrors.length > 0}
                  <span class="muted">• {resolvedErrors.length} resuelto{resolvedErrors.length === 1 ? '' : 's'}</span>
                {/if}
              </div>
            </div>
            <div class="errors-accordion">
              {#each unresolvedErrors.slice(0, 10) as error}
                {@const errorId = error.event_id}
                {@const isExpanded = expandedErrors.has(errorId)}
                {@const errorTitle = error.title || "Sin título"}
                {@const errorSession = error.session?.session_id || "N/A"}
                {@const errorDate = error.ts ? new Date(error.ts).toLocaleString() : "N/A"}
                
                <div class="error-accordion-item">
                  <button
                    class="error-accordion-header"
                    class:expanded={isExpanded}
                    type="button"
                    on:click={() => {
                      if (isExpanded) {
                        expandedErrors.delete(errorId);
                      } else {
                        expandedErrors.add(errorId);
                      }
                      expandedErrors = expandedErrors; // Trigger reactivity
                    }}
                  >
                    <span class="error-status-icon">{error.has_fix ? '✅' : '⚠️'}</span>
                    <span class="error-title-text">{errorTitle}</span>
                    <span class="error-meta-badge">{errorSession}</span>
                    <span class="error-expand-icon">{isExpanded ? '▼' : '▶'}</span>
                  </button>
                  {#if isExpanded}
                    <div class="error-accordion-content">
                      <div class="error-content-details">
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
                        {#if error.error_hash}
                          <div class="error-meta-item">
                            <span class="error-meta-label">Hash:</span>
                            <span class="error-meta-value mono" style="font-size: 10px;">{error.error_hash.substring(0, 16)}...</span>
                          </div>
                        {/if}
                      </div>
                      <div class="error-actions">
                        <button
                          class="btn-error-archive"
                          type="button"
                          on:click={() => archiveError(errorId)}
                          title="Archivar este error"
                        >
                          📦 Archivar
                        </button>
                        <button
                          class="btn-error-copy"
                          type="button"
                          on:click={() => copyErrorContent(error)}
                          title="Copiar información del error"
                        >
                          📋 Copiar
                        </button>
                      </div>
                    </div>
                  {/if}
                </div>
              {/each}
              {#if unresolvedErrors.length > 10}
                <div class="errors-more">
                  <span class="muted">... y {unresolvedErrors.length - 10} más</span>
                </div>
              {/if}
            </div>
          </div>
          {:else}
            <div class="empty-state">
              <p class="muted">No hay errores visibles (todos archivados).</p>
            </div>
          {/if}
        {:else}
          <div class="empty-state">
            <p class="muted">No hay errores abiertos.</p>
          </div>
        {/if}
      </div>
    {/if}
  </section>

  <section class="panel">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--spacing-lg);">
      <h2 style="margin: 0;">Zona viva</h2>
      {#if currentSession}
        <button 
          class="btn-open-board"
          on:click={openBoard}
          title="Abrir Feature Board"
        >
          Abrir Board
        </button>
      {/if}
    </div>
    <div class="tabs">
      <button
        class="tab-button"
        class:active={zonaVivaTab === "sesion"}
        on:click={() => (zonaVivaTab = "sesion")}
      >
        Sesión
      </button>
      <button
        class="tab-button"
        class:active={zonaVivaTab === "bitacora"}
        on:click={() => (zonaVivaTab = "bitacora")}
      >
        Bitácora
      </button>
      <button
        class="tab-button"
        class:active={zonaVivaTab === "objetivos"}
        on:click={() => (zonaVivaTab = "objetivos")}
      >
        Objetivos
      </button>
      {#if temporalNotesCount > 0}
        <button
          class="tab-button"
          class:active={zonaVivaTab === "temporales"}
          on:click={() => (zonaVivaTab = "temporales")}
        >
          Notas Temporales ({temporalNotesCount})
        </button>
      {/if}
    </div>
    <div class="tab-content zona-viva-content" bind:this={zonaVivaElement}>
      {#if loading}
        <div class="loading-state">
          <p class="muted">Cargando...</p>
        </div>
      {:else if zonaVivaTab === "sesion"}
        {#if currentSession}
          <!-- Visualizador de tiempo transcurrido -->
          {#if dayElapsedMinutes !== null}
            <div class="card time-tracker-card">
              <div class="card-header">
                <div class="mono">⏱️ Tiempo transcurrido</div>
              </div>
              <div class="card-body">
                <div class="time-display">
                  {formatElapsed(dayElapsedMinutes)}
                </div>
                <div class="muted" style="font-size: 12px; margin-top: 0.5rem;">
                  Desde inicio de jornada
                </div>
              </div>
            </div>
          {/if}
          
          <!-- Controles de sesión -->
          <div class="card session-controls-card">
            <div class="card-header">
              <div class="mono">Control de sesión</div>
            </div>
            <div class="card-body">
              <div class="session-controls">
                {#if isSessionPaused()}
                  <button 
                    class="btn-session btn-resume"
                    on:click={resumeSession}
                    title="Retomar sesión pausada"
                  >
                    ▶️ Retomar sesión
                  </button>
                {:else if currentSession}
                  <button 
                    class="btn-session btn-pause"
                    on:click={pauseSession}
                    title="Pausar sesión actual"
                  >
                    ⏸️ Pausar sesión
                  </button>
                {/if}
                {#if currentSession}
                  <button 
                    class="btn-session btn-end"
                    on:click={endSession}
                    title="Finalizar sesión actual"
                  >
                    ⏹️ Finalizar sesión
                  </button>
                {/if}
              </div>
            </div>
          </div>
          
          <ErrorFixCommitChain apiBase={API_BASE} />
          <SessionObjectives session={currentSession} />
          <div class="card session-card">
            <div class="card-header">
              <div class="mono session-id">
                {currentSession.day_id} {currentSession.session_id}
              </div>
            </div>
            <div class="card-body">
              <div class="session-details">
                <div class="detail-item">
                  <span class="detail-label">Repo:</span>
                  <span class="muted mono">{currentSession.repo?.path || "N/A"}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Branch:</span>
                  <span class="muted mono">{currentSession.repo?.branch || "N/A"}</span>
                </div>
                {#if isSessionPaused()}
                  <div class="detail-item">
                    <span class="detail-label">Estado:</span>
                    <span class="muted">⏸️ Pausada</span>
                  </div>
                {/if}
              </div>
            </div>
          </div>
        {:else}
          <div class="empty-state">
            <p class="muted">No hay sesión activa. Iniciá con <code>dia start</code>.</p>
          </div>
        {/if}
      {:else if zonaVivaTab === "bitacora"}
        <BitacoraEditor apiBase={API_BASE} dayId={today} />
      {:else if zonaVivaTab === "objetivos"}
        <SessionObjectives session={currentSession} />
        {#if !currentSession}
          <div class="empty-state">
            <p class="muted">No hay sesión activa para mostrar objetivos.</p>
          </div>
        {/if}
      {:else if zonaVivaTab === "temporales"}
        <TemporalNotesViewer apiBase={API_BASE} dayId={today} />
      {/if}
    </div>
  </section>
  </div>
  
  {#if boardOpen}
    <BoardView boardId={boardId} onClose={closeBoard} />
  {/if}
</div>
