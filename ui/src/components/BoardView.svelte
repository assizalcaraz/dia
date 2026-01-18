<script>
  import { onMount, onDestroy } from 'svelte';
  import { boardState, viewport, initializeBoardStore, cleanupBoardStore, addElement, generateElementId } from '../stores/boardStore.js';
  import BoardElement from './BoardElement.svelte';

  export let boardId;
  export let onClose;

  $: currentViewport = $viewport;
  $: currentBoardState = $boardState;

  let isDragging = false;
  let canvasElement = null;

  onMount(() => {
    // Inicializar store y cargar estado
    if (boardId) {
      initializeBoardStore(boardId);
    }
  });

  onDestroy(() => {
    // Limpiar suscripción al desmontar
    cleanupBoardStore();
  });

  function handleClose() {
    onClose();
  }

  // Manejar drag and drop de imágenes
  function handleDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes('Files')) {
      isDragging = true;
    }
  }

  function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes('Files')) {
      e.dataTransfer.dropEffect = 'copy';
    }
  }

  function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    // Solo cambiar estado si salimos del canvas
    if (!canvasElement?.contains(e.relatedTarget)) {
      isDragging = false;
    }
  }

  async function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    isDragging = false;

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));

    if (imageFiles.length === 0) {
      console.warn('No se encontraron archivos de imagen');
      return;
    }

    // Obtener posición del drop relativa al canvas
    const rect = canvasElement.getBoundingClientRect();
    let x = (e.clientX - rect.left - currentViewport.x) / currentViewport.zoom;
    let y = (e.clientY - rect.top - currentViewport.y) / currentViewport.zoom;

    // Procesar cada imagen
    for (const file of imageFiles) {
      try {
        const imageDataUrl = await fileToDataURL(file);
        
        const newElement = {
          id: generateElementId(),
          type: 'custom',
          position: { x, y },
          size: { width: 300, height: 200 },
          content: {
            title: file.name,
            body: '',
            data: {
              imageType: 'dataurl',
              imageData: imageDataUrl,
              originalFileName: file.name,
              fileSize: file.size,
              mimeType: file.type
            }
          },
          metadata: {
            createdAt: new Date().toISOString(),
            modifiedAt: new Date().toISOString(),
            tags: ['image', 'uploaded'],
            color: undefined
          },
          zIndex: Date.now()
        };

        addElement(newElement);
        
        // Ajustar posición para la siguiente imagen
        x += 50;
        y += 50;
      } catch (error) {
        console.error('Error procesando imagen:', error);
        // Si hay error, documentarlo
        alert(`Error al procesar ${file.name}: ${error.message}\n\nPara documentar este error, ejecuta:\necho "${error.message}" | dia cap --kind error --title "Error procesando imagen ${file.name}" --data-root ./data --area it`);
      }
    }
  }

  // Convertir archivo a Data URL
  function fileToDataURL(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = (e) => reject(new Error('Error leyendo archivo'));
      reader.readAsDataURL(file);
    });
  }
</script>

<div class="board-fullscreen">
  <div class="board-header">
    <h2 class="board-title">Feature Board</h2>
    <button class="board-close-btn" on:click={handleClose}>
      Cerrar
    </button>
  </div>
  
  <div 
    class="board-canvas"
    class:dragging={isDragging}
    bind:this={canvasElement}
    on:dragenter={handleDragEnter}
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  >
    {#if currentBoardState}
      {#each currentBoardState.elements as element (element.id)}
        <BoardElement 
          element={element} 
          viewport={currentViewport}
        />
      {/each}
    {:else}
      <div class="board-empty">
        <p class="muted">Board vacío. Los elementos aparecerán aquí.</p>
        <p class="muted" style="margin-top: var(--spacing-md);">Arrastra imágenes aquí para agregarlas al board.</p>
      </div>
    {/if}
    
    {#if isDragging}
      <div class="board-drop-zone">
        <p>Suelta las imágenes aquí</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .board-fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--color-bg);
    z-index: 1000;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .board-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--color-border);
    background: var(--color-surface);
    flex-shrink: 0;
  }

  .board-title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--color-text);
  }

  .board-close-btn {
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text);
    cursor: pointer;
    transition: var(--transition);
  }

  .board-close-btn:hover {
    border-color: var(--color-border-strong);
    background: var(--color-bg);
    box-shadow: var(--shadow-sm);
  }

  .board-canvas {
    flex: 1;
    position: relative;
    overflow: hidden;
    background: var(--color-bg);
    background-image: 
      linear-gradient(var(--color-border) 1px, transparent 1px),
      linear-gradient(90deg, var(--color-border) 1px, transparent 1px);
    background-size: 20px 20px;
    background-position: 0 0, 0 0;
  }

  .board-empty {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    text-align: center;
    padding: var(--spacing-xl);
  }

  .board-canvas.dragging {
    background-color: rgba(0, 0, 0, 0.02);
  }

  .board-drop-zone {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.05);
    border: 3px dashed var(--color-border-strong);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    pointer-events: none;
  }

  .board-drop-zone p {
    font-size: 24px;
    font-weight: 600;
    color: var(--color-text);
    margin: 0;
  }
</style>
