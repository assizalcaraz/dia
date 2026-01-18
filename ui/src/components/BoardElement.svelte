<script>
  export let element;
  export let viewport;

  // Calcular posición transformada según viewport
  $: transformedX = element && viewport ? (element.position.x + viewport.x) * viewport.zoom : 0;
  $: transformedY = element && viewport ? (element.position.y + viewport.y) * viewport.zoom : 0;
  $: transformedWidth = element && viewport ? element.size.width * viewport.zoom : 150;
  $: transformedHeight = element && viewport ? element.size.height * viewport.zoom : 80;

  // Obtener icono según tipo
  function getTypeIcon(type) {
    const icons = {
      note: '📝',
      task: '✓',
      session: '📅',
      error: '⚠️',
      custom: '📦'
    };
    return icons[type] || '📦';
  }

  // Verificar si el elemento tiene imagen
  $: hasImage = element?.content?.data?.imageData;
  $: imageData = element?.content?.data?.imageData;
</script>

{#if element && viewport}
<div
  class="board-element board-element--{element.type}"
  style="
    left: {transformedX}px;
    top: {transformedY}px;
    width: {transformedWidth}px;
    height: {transformedHeight}px;
    z-index: {element.zIndex || 0};
  "
>
  <div class="board-element__header">
    <span class="board-element__icon">{getTypeIcon(element.type)}</span>
    <span class="board-element__title">
      {element.content?.title || element.type || 'Element'}
    </span>
  </div>
  
  {#if hasImage}
    <div class="board-element__image">
      <img src={imageData} alt={element.content?.title || 'Imagen'} />
    </div>
  {/if}
  
  {#if element.content?.body}
    <div class="board-element__body">
      {element.content.body}
    </div>
  {/if}
  
  {#if element.metadata?.tags && element.metadata.tags.length > 0}
    <div class="board-element__tags">
      {#each element.metadata.tags as tag}
        <span class="board-element__tag">{tag}</span>
      {/each}
    </div>
  {/if}
</div>
{/if}

<style>
  .board-element {
    position: absolute;
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-md);
    background: var(--color-surface);
    padding: var(--spacing-sm);
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    min-width: 150px;
    min-height: 80px;
    transition: var(--transition);
  }

  .board-element:hover {
    border-color: var(--color-border-strong);
    box-shadow: var(--shadow-md);
  }

  .board-element__header {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-xs);
    padding-bottom: var(--spacing-xs);
    border-bottom: 1px solid var(--color-border);
  }

  .board-element__icon {
    font-size: 16px;
    line-height: 1;
  }

  .board-element__title {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .board-element__image {
    width: 100%;
    margin: var(--spacing-xs) 0;
    border-radius: var(--radius-sm);
    overflow: hidden;
    background: var(--color-bg);
  }

  .board-element__image img {
    width: 100%;
    height: auto;
    display: block;
    object-fit: contain;
    max-height: 200px;
  }

  .board-element__body {
    font-size: 13px;
    color: var(--color-text-muted);
    line-height: 1.4;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
  }

  .board-element__tags {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
    margin-top: var(--spacing-xs);
    padding-top: var(--spacing-xs);
    border-top: 1px solid var(--color-border);
  }

  .board-element__tag {
    font-size: 11px;
    color: var(--color-text-subtle);
    background: var(--color-bg);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border);
  }

  /* Variantes por tipo */
  .board-element--note {
    border-left: 3px solid var(--color-border-strong);
  }

  .board-element--task {
    border-left: 3px solid #4caf50;
  }

  .board-element--session {
    border-left: 3px solid #2196f3;
  }

  .board-element--error {
    border-left: 3px solid #f44336;
  }

  .board-element--custom {
    border-left: 3px solid var(--color-text-subtle);
  }
</style>
