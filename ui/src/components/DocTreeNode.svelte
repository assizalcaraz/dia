<script>
  import { createEventDispatcher } from "svelte";

  export let node;
  export let path = "";
  export let level = 0;
  export let selectedPath = null;
  export let expandedNodes = {};
  export let isExpanded = () => false;
  export let toggleNode = () => {};

  const dispatch = createEventDispatcher();

  const handleClick = () => {
    if (node.type === "file") {
      dispatch("select", node.path);
    } else {
      toggleNode(path);
    }
  };
</script>

<div class="tree-node">
  <button
    class="tree-item"
    class:selected={node.type === "file" && selectedPath === path}
    style="padding-left: {level * 16 + 8}px"
    on:click={handleClick}
  >
    {#if node.type === "directory"}
      <span class="tree-icon">{isExpanded(path) ? "📂" : "📁"}</span>
    {:else}
      <span class="tree-icon">📄</span>
    {/if}
    <span class="tree-name">{node.name}</span>
  </button>
  {#if node.type === "directory" && isExpanded(path) && node.children}
    {#each node.children as child}
      <svelte:self
        node={child}
        path={child.path}
        level={level + 1}
        {selectedPath}
        {expandedNodes}
        {isExpanded}
        {toggleNode}
        on:select={(e) => dispatch("select", e.detail)}
      />
    {/each}
  {/if}
</div>

<style>
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

  .tree-item.selected {
    background: var(--color-bg);
    border-left: 2px solid var(--color-border-strong);
    font-weight: 500;
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
</style>
