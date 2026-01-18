import { writable, derived } from 'svelte/store';

// Store principal del estado del board
export const boardState = writable(null);

// Store de elementos seleccionados (Set de IDs)
export const selectedElements = writable(new Set());

// Store del viewport (posición y zoom)
export const viewport = writable({ x: 0, y: 0, zoom: 1 });

// Función para generar clave de localStorage
function getStorageKey(boardId: string): string {
  return `board_${boardId}`;
}

// Función para cargar estado desde localStorage
export function loadBoardState(boardId) {
  if (typeof window === 'undefined') return null;
  
  const key = getStorageKey(boardId);
  const stored = localStorage.getItem(key);
  
  if (!stored) {
    // Crear board vacío si no existe
    const emptyState = {
      id: boardId,
      elements: [],
      connections: [],
      viewport: { x: 0, y: 0, zoom: 1 },
      lastModified: new Date().toISOString()
    };
    return emptyState;
  }
  
  try {
    return JSON.parse(stored);
  } catch (error) {
    console.error('Error loading board state:', error);
    return null;
  }
}

// Función para guardar estado en localStorage
export function saveBoardState(state) {
  if (typeof window === 'undefined' || !state) return;
  
  const key = getStorageKey(state.id);
  state.lastModified = new Date().toISOString();
  
  try {
    localStorage.setItem(key, JSON.stringify(state));
  } catch (error) {
    console.error('Error saving board state:', error);
  }
}

// Suscripción automática para guardar cuando cambia el estado
let unsubscribe: (() => void) | null = null;

export function initializeBoardStore(boardId) {
  // Cargar estado inicial
  const initialState = loadBoardState(boardId);
  boardState.set(initialState);
  
  // Suscribirse a cambios y guardar automáticamente
  if (unsubscribe) {
    unsubscribe();
  }
  
  unsubscribe = boardState.subscribe((state) => {
    if (state) {
      saveBoardState(state);
    }
  });
}

// Función para limpiar suscripción
export function cleanupBoardStore() {
  if (unsubscribe) {
    unsubscribe();
    unsubscribe = null;
  }
}
