// Tipos para el Feature Board

export interface BoardState {
  id: string; // session_id o day_id
  elements: BoardElement[];
  connections: Connection[];
  viewport: {
    x: number;
    y: number;
    zoom: number;
  };
  lastModified: string; // ISO timestamp
}

export interface BoardElement {
  id: string; // UUID
  type: 'note' | 'task' | 'session' | 'error' | 'custom';
  position: { x: number; y: number };
  size: { width: number; height: number };
  content: ElementContent;
  metadata: {
    createdAt: string;
    modifiedAt: string;
    tags?: string[];
    color?: string;
  };
  zIndex: number;
}

export interface ElementContent {
  title?: string;
  body?: string; // Markdown support
  data?: any; // Datos específicos del tipo
}

export interface Connection {
  id: string;
  from: string; // elementId
  to: string; // elementId
  type: 'related' | 'depends' | 'blocks';
  label?: string;
}
