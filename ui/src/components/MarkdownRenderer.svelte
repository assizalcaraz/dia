<script>
  import { marked } from "marked";
  import { onMount, onDestroy } from "svelte";
  import { createEventDispatcher } from "svelte";

  export let content = "";
  export let basePath = ""; // Ruta base del documento actual para resolver enlaces relativos

  const dispatch = createEventDispatcher();

  let htmlContent = "";
  let containerElement = null;

  // Función para resolver rutas relativas a rutas absolutas
  const resolvePath = (href, currentPath) => {
    // Si es un enlace absoluto o externo, no hacer nada
    if (href.startsWith("http://") || href.startsWith("https://") || href.startsWith("//") || href.startsWith("mailto:")) {
      return null; // Dejar que el navegador maneje enlaces externos
    }

    // Si es solo un fragmento (empieza con #), no es un enlace a documento
    if (href.startsWith("#")) {
      return null;
    }

    // Remover fragmento (#) y query string (?) si existen
    const pathWithoutFragment = href.split("#")[0].split("?")[0];

    // Verificar si es un archivo .md (puede estar en cualquier parte de la ruta)
    if (!pathWithoutFragment.includes(".md")) {
      return null;
    }

    // Si es una ruta absoluta (empieza con /)
    if (pathWithoutFragment.startsWith("/")) {
      // Remover el / inicial y retornar
      return pathWithoutFragment.substring(1);
    }

    // Si no hay basePath, no podemos resolver rutas relativas
    if (!currentPath) {
      return null;
    }

    // Resolver ruta relativa
    const currentDir = currentPath.split("/").slice(0, -1).join("/");
    const parts = pathWithoutFragment.split("/").filter(p => p !== "");
    let resolved = currentDir ? currentDir.split("/").filter(p => p !== "") : [];

    for (const part of parts) {
      if (part === ".") {
        continue;
      } else if (part === "..") {
        if (resolved.length > 0) {
          resolved.pop();
        }
      } else {
        resolved.push(part);
      }
    }

    return resolved.join("/");
  };

  $: if (content) {
    try {
      htmlContent = marked.parse(content, {
        breaks: true,
        gfm: true,
      });
    } catch (error) {
      htmlContent = `<p class="error">Error al renderizar markdown: ${error.message}</p>`;
    }
  }

  // Interceptar clics en enlaces después de renderizar
  const handleLinkClick = (event) => {
    const link = event.target.closest("a");
    if (!link) return;

    const href = link.getAttribute("href");
    if (!href) return;

    // Resolver ruta si es un enlace a .md
    const resolvedPath = resolvePath(href, basePath);
    if (resolvedPath !== null) {
      event.preventDefault();
      dispatch("docLink", { path: resolvedPath });
      return;
    }

    // Para otros enlaces, dejar que el navegador maneje (pero prevenir navegación si es relativo)
    if (!href.startsWith("http://") && !href.startsWith("https://") && !href.startsWith("//") && !href.startsWith("#")) {
      event.preventDefault();
    }
  };

  onMount(() => {
    if (containerElement) {
      containerElement.addEventListener("click", handleLinkClick);
    }
  });

  onDestroy(() => {
    if (containerElement) {
      containerElement.removeEventListener("click", handleLinkClick);
    }
  });
</script>

<div class="markdown-content" bind:this={containerElement}>
  {@html htmlContent}
</div>

<style>
  .markdown-content {
    line-height: 1.6;
    color: var(--color-text);
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
  }

  .markdown-content :global(h1) {
    font-size: 24px;
    font-weight: 600;
    margin: var(--spacing-xl) 0 var(--spacing-md) 0;
    padding-bottom: var(--spacing-sm);
    border-bottom: 1px solid var(--color-border);
    color: var(--color-text);
  }

  .markdown-content :global(h2) {
    font-size: 20px;
    font-weight: 600;
    margin: var(--spacing-lg) 0 var(--spacing-md) 0;
    color: var(--color-text);
  }

  .markdown-content :global(h3) {
    font-size: 16px;
    font-weight: 600;
    margin: var(--spacing-md) 0 var(--spacing-sm) 0;
    color: var(--color-text);
  }

  .markdown-content :global(h4),
  .markdown-content :global(h5),
  .markdown-content :global(h6) {
    font-size: 14px;
    font-weight: 600;
    margin: var(--spacing-md) 0 var(--spacing-xs) 0;
    color: var(--color-text);
  }

  .markdown-content :global(p) {
    margin: var(--spacing-md) 0;
    color: var(--color-text);
  }

  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: var(--spacing-md) 0;
    padding-left: var(--spacing-xl);
    color: var(--color-text);
  }

  .markdown-content :global(li) {
    margin: var(--spacing-xs) 0;
  }

  .markdown-content :global(code) {
    font-family: ui-monospace, SFMono-Regular, "Cascadia Code", "Roboto Mono", Menlo, Consolas, monospace;
    font-size: 13px;
    background: var(--color-surface);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    color: var(--color-text);
    border: 1px solid var(--color-border);
  }

  .markdown-content :global(pre) {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    overflow-x: auto;
    margin: var(--spacing-md) 0;
    max-width: 100%;
    box-sizing: border-box;
  }

  .markdown-content :global(pre code) {
    background: none;
    padding: 0;
    border: none;
    font-size: 13px;
  }

  .markdown-content :global(blockquote) {
    border-left: 3px solid var(--color-border-strong);
    padding-left: var(--spacing-md);
    margin: var(--spacing-md) 0;
    color: var(--color-text-muted);
    font-style: italic;
  }

  .markdown-content :global(a) {
    color: var(--color-text);
    text-decoration: underline;
  }

  .markdown-content :global(a:hover) {
    color: var(--color-text);
  }

  .markdown-content :global(table) {
    width: 100%;
    max-width: 100%;
    border-collapse: collapse;
    margin: var(--spacing-md) 0;
    table-layout: auto;
    overflow-x: auto;
    display: block;
  }
  
  .markdown-content :global(table) :global(tbody) {
    display: table;
    width: 100%;
  }

  .markdown-content :global(th),
  .markdown-content :global(td) {
    border: 1px solid var(--color-border);
    padding: var(--spacing-sm);
    text-align: left;
  }

  .markdown-content :global(th) {
    background: var(--color-surface);
    font-weight: 600;
  }

  .markdown-content :global(hr) {
    border: none;
    border-top: 1px solid var(--color-border);
    margin: var(--spacing-lg) 0;
  }

  .markdown-content :global(.error) {
    color: #d32f2f;
    padding: var(--spacing-md);
    background: var(--color-surface);
    border: 1px solid #d32f2f;
    border-radius: var(--radius-md);
  }
</style>
