<script>
  import { onMount } from "svelte";

  const API_BASE = import.meta.env.VITE_API_BASE || "/api";

  let sessions = [];
  let currentSession = null;
  let events = [];
  let metrics = {};
  let loading = true;

  const fetchJson = async (path) => {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
  };

  const load = async () => {
    loading = true;
    try {
      const [sessionsRes, currentRes, eventsRes, metricsRes] =
        await Promise.all([
          fetchJson("/sessions/"),
          fetchJson("/sessions/current/"),
          fetchJson("/events/recent/?limit=10"),
          fetchJson("/metrics/"),
        ]);
      sessions = sessionsRes.sessions || [];
      currentSession = currentRes.session;
      events = eventsRes.events || [];
      metrics = metricsRes || {};
    } catch (error) {
      console.error(error);
    } finally {
      loading = false;
    }
  };

  let intervalId;

  onMount(() => {
    load();
    intervalId = setInterval(load, 5000);
    return () => clearInterval(intervalId);
  });
</script>

<div class="page">
  <section class="panel">
    <h2>Zona indeleble</h2>
    {#if loading}
      <p class="muted">Cargando...</p>
    {:else}
      <div class="card">
        <p>Total sesiones: {metrics.total_sessions ?? 0}</p>
        <p>Commit suggestions: {metrics.commit_suggestions ?? 0}</p>
        <p>Total eventos: {metrics.total_events ?? 0}</p>
      </div>
      <h3>Historial</h3>
      <div class="list">
        {#each sessions as session}
          <div class="card">
            <div class="mono">{session.day_id} {session.session_id}</div>
            <div>{session.intent}</div>
            <div class="muted">Modo: {session.mode}</div>
            <div class="muted">
              {session.start_ts} → {session.end_ts || "abierta"}
            </div>
          </div>
        {/each}
        {#if sessions.length === 0}
          <p class="muted">Sin sesiones registradas.</p>
        {/if}
      </div>
    {/if}
  </section>

  <section class="panel">
    <h2>Zona viva</h2>
    {#if loading}
      <p class="muted">Cargando...</p>
    {:else if !currentSession}
      <p class="muted">No hay sesion activa.</p>
    {:else}
      <div class="card">
        <div class="mono">
          {currentSession.day_id} {currentSession.session_id}
        </div>
        <div>{currentSession.intent}</div>
        <div class="muted">DoD: {currentSession.dod}</div>
        <div class="muted">
          Repo: {currentSession.repo?.path || "N/A"}
        </div>
        <div class="muted">
          Branch: {currentSession.repo?.branch || "N/A"}
        </div>
      </div>
      <h3>Checklist diario</h3>
      <ul>
        <li>Sesion abierta con intencion clara</li>
        <li>Repo limpio o cambios conscientes</li>
        <li>Checkpoint pre-feat ejecutado</li>
        <li>Plan de cierre listo</li>
      </ul>
      <h3>Eventos recientes</h3>
      <div class="list">
        {#each events as event}
          <div class="card">
            <div class="mono">{event.type}</div>
            <div class="muted">{event.ts}</div>
          </div>
        {/each}
        {#if events.length === 0}
          <p class="muted">Sin eventos recientes.</p>
        {/if}
      </div>
    {/if}
  </section>
</div>
