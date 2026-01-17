<script>
  import { onMount } from "svelte";
  import MarkdownRenderer from "./MarkdownRenderer.svelte";
  import DocTreeNode from "./DocTreeNode.svelte";

  export let apiBase = "/api";

  let docsTree = [];
  let selectedDoc = null;
  let content = "";
  let loading = false;
  let loadingContent = false;
  let error = null;
  let expandedNodes = {};
  let searchQuery = "";
  let filteredTree = [];

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

  const loadDocsTree = async () => {
    loading = true;
    error = null;
    try {
      const data = await fetchJson("/docs/list/");
      docsTree = data.tree || [];
      // Expandir nodo raíz por defecto
      if (docsTree.length > 0) {
        expandedNodes[""] = true;
      }
    } catch (err) {
      error = `Error al cargar documentación: ${err.message}`;
      docsTree = [];
    } finally {
      loading = false;
    }
  };

  const loadDocContent = async (path) => {
    if (!path) return;

    loadingContent = true;
    try {
      const data = await fetchJson(`/docs/${path}/`);
      content = data.content || "";
      selectedDoc = path;
      
      // Scroll al inicio del contenido después de cargar
      setTimeout(() => {
        const contentEl = document.querySelector(".docs-content");
        if (contentEl) {
          contentEl.scrollTop = 0;
        }
      }, 100);
    } catch (err) {
      console.error("Error cargando documento:", err);
      content = `Error al cargar documento: ${err.message}`;
      selectedDoc = null;
    } finally {
      loadingContent = false;
    }
  };

  const toggleNode = (path) => {
    expandedNodes[path] = !expandedNodes[path];
    expandedNodes = expandedNodes; // Trigger reactivity
  };

  const isExpanded = (path) => expandedNodes[path] === true;

  // Función para filtrar el árbol de documentación
  const filterTree = (tree, query) => {
    if (!query) return tree;
    
    const lowerQuery = query.toLowerCase();
    const filtered = [];
    
    for (const node of tree) {
      const matches = node.name.toLowerCase().includes(lowerQuery);
      
      if (node.type === "file" && matches) {
        filtered.push(node);
      } else if (node.type === "directory") {
        const filteredChildren = filterTree(node.children || [], query);
        if (matches || filteredChildren.length > 0) {
          filtered.push({
            ...node,
            children: filteredChildren,
          });
          // Expandir directorios que tienen resultados
          expandedNodes[node.path] = true;
        }
      }
    }
    
    return filtered;
  };

  // Expandir todos los nodos cuando hay búsqueda
  const expandAll = (tree) => {
    for (const node of tree) {
      if (node.type === "directory") {
        expandedNodes[node.path] = true;
        if (node.children) {
          expandAll(node.children);
        }
      }
    }
  };

  $: {
    if (searchQuery) {
      filteredTree = filterTree(docsTree, searchQuery);
      expandAll(filteredTree);
      expandedNodes = expandedNodes; // Trigger reactivity
    } else {
      filteredTree = docsTree;
    }
  }

  // Expandir automáticamente el directorio del documento seleccionado
  $: if (selectedDoc && docsTree.length > 0) {
    const parts = selectedDoc.split("/");
    let currentPath = "";
    for (let i = 0; i < parts.length - 1; i++) {
      currentPath = currentPath ? `${currentPath}/${parts[i]}` : parts[i];
      expandedNodes[currentPath] = true;
    }
    expandedNodes = expandedNodes; // Trigger reactivity
  }

  onMount(() => {
    loadDocsTree();
  });
</script>

<div class="docs-viewer">
  {#if loading}
    <div class="loading-state">
      <p class="muted">Cargando documentación...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p class="error-text">{error}</p>
    </div>
  {:else}
    <div class="docs-layout">
      <div class="docs-sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">Documentación</h3>
          {#if docsTree.length > 0}
            <div class="search-container">
              <input
                type="text"
                class="search-input"
                placeholder="Buscar..."
                bind:value={searchQuery}
              />
            </div>
          {/if}
        </div>
        {#if docsTree.length === 0}
          <div class="empty-state">
            <p class="muted">No hay documentación disponible.</p>
          </div>
        {:else if filteredTree.length === 0 && searchQuery}
          <div class="empty-state">
            <p class="muted">No se encontraron documentos que coincidan con "{searchQuery}".</p>
          </div>
        {:else}
          <div class="tree-container">
            {#each filteredTree as node}
            <DocTreeNode
              {node}
              path={node.path}
              level={0}
              {selectedDoc}
              {expandedNodes}
              {isExpanded}
              {toggleNode}
              on:select={(e) => loadDocContent(e.detail)}
            />
            {/each}
          </div>
        {/if}
      </div>

      <div class="docs-content">
        {#if loadingContent}
          <div class="loading-state">
            <p class="muted">Cargando documento...</p>
          </div>
        {:else if content}
          <div class="content-wrapper">
            {#if selectedDoc}
              <div class="breadcrumbs">
                {#each selectedDoc.split("/") as part, index}
                  {#if index > 0}
                    <span class="breadcrumb-separator">/</span>
                  {/if}
                  <span class="breadcrumb-part">{part}</span>
                {/each}
              </div>
            {/if}
            <MarkdownRenderer content={content} />
          </div>
        {:else}
          <div class="empty-state">
            <p class="muted">Selecciona un documento para ver su contenido.</p>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>


<style>
  .docs-viewer {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .docs-layout {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: var(--spacing-lg);
    flex: 1;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
  }

  /* Ajustar sidebar cuando hay más espacio */
  @media (min-width: 1200px) {
    .docs-layout {
      grid-template-columns: 350px 1fr;
    }
  }

  @media (max-width: 768px) {
    .docs-layout {
      grid-template-columns: 1fr;
    }

    .docs-sidebar {
      max-height: 200px;
      overflow-y: auto;
    }
  }

  .docs-sidebar {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    background: var(--color-surface);
    overflow-y: auto;
    height: 100%;
  }

  .sidebar-header {
    margin-bottom: var(--spacing-md);
  }

  .sidebar-title {
    font-size: 14px;
    font-weight: 600;
    margin: 0 0 var(--spacing-sm) 0;
    color: var(--color-text);
  }

  .search-container {
    margin-top: var(--spacing-sm);
  }

  .search-input {
    width: 100%;
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background: var(--color-bg);
    color: var(--color-text);
    font-size: 13px;
    font-family: inherit;
    transition: var(--transition);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-border-strong);
    box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.05);
  }

  .search-input::placeholder {
    color: var(--color-text-subtle);
  }

  .tree-container {
    display: flex;
    flex-direction: column;
  }

  .tree-node {
    margin: var(--spacing-xs) 0;
  }

  .tree-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) var(--spacing-sm);
    border: none;
    background: transparent;
    color: var(--color-text);
    font-size: 13px;
    text-align: left;
    cursor: pointer;
    width: 100%;
    border-radius: var(--radius-sm);
    transition: var(--transition);
  }

  .tree-item:hover {
    background: var(--color-bg);
  }

  .tree-icon {
    font-size: 14px;
    flex-shrink: 0;
  }

  .tree-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .docs-content {
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    background: var(--color-bg);
    overflow-y: auto;
    overflow-x: hidden;
    height: 100%;
    min-width: 0;
    max-width: 100%;
  }

  .breadcrumbs {
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--color-border);
    font-size: 12px;
    font-family: ui-monospace, SFMono-Regular, "Cascadia Code", "Roboto Mono", Menlo, Consolas, monospace;
    color: var(--color-text-muted);
  }

  .breadcrumb-separator {
    margin: 0 var(--spacing-xs);
    color: var(--color-text-subtle);
  }

  .breadcrumb-part {
    color: var(--color-text);
  }

  .content-wrapper {
    width: 100%;
    min-width: 0;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
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
