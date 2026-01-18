<script>
  import { onMount } from "svelte";
  import BitacoraViewer from "./components/BitacoraViewer.svelte";
  import SummariesViewer from "./components/SummariesViewer.svelte";
  import DocsViewer from "./components/DocsViewer.svelte";

  const API_BASE = import.meta.env.VITE_API_BASE || "/api";

  let sessions = [];
  let currentSession = null;
  let summaries = [];
  let latestRollingSummary = null;
  let rollingTimeline = [];
  let metrics = {};
  let openErrors = [];
  let dayToday = null; // Información del día actual
  let loading = true;
  let today = new Date().toISOString().split("T")[0]; // YYYY-MM-DD
  let activeTab = "overview"; // overview, bitacora, summaries, docs

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

  const formatElapsed = (minutes) => {
    if (minutes === null || minutes === undefined) return "—";
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  };

  let intervalId;

  onMount(() => {
    load();
    intervalId = setInterval(load, 5000);
    return () => clearInterval(intervalId);
  });
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
    <h2>Zona viva</h2>
    <div class="tab-content">
      {#if loading}
      <div class="loading-state">
        <p class="muted">Cargando...</p>
      </div>
    {:else if !currentSession}
      <div class="empty-state">
        <p class="muted">No hay sesión activa.</p>
      </div>
    {:else}
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
        <div class="list">
          {#each openErrors.slice(0, 5) as error}
            <div class="card error-card">
              <div class="card-header">
                <div class="mono">{error.title || "Sin título"}</div>
              </div>
              <div class="card-body">
                <div class="muted">
                  {error.session?.session_id || "N/A"} — {error.ts ? new Date(error.ts).toLocaleString() : "N/A"}
                </div>
                {#if error.artifact_ref}
                  <div class="muted mono">Artifact: {error.artifact_ref}</div>
                {/if}
              </div>
            </div>
          {/each}
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
</div>
