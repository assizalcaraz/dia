"""Utilidad para analizar errores con LLM y generar títulos automáticamente."""

from __future__ import annotations

import os
import json
from typing import Optional


def analyze_error_with_llm(content: str, kind: str = "error") -> Optional[str]:
    """
    Analiza un error/log con LLM y genera un título descriptivo.
    
    Args:
        content: Contenido del error/log
        kind: Tipo de captura ("error" o "log")
    
    Returns:
        Título generado o None si falla
    """
    # Intentar usar OpenAI si está configurado
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return _analyze_with_openai(content, kind, api_key)
    
    # Fallback: análisis simple basado en patrones
    return _analyze_simple(content, kind)


def _analyze_with_openai(content: str, kind: str, api_key: str) -> Optional[str]:
    """Analiza usando OpenAI API."""
    try:
        try:
            import requests
        except ImportError:
            # requests no está instalado, usar análisis simple
            return None
        
        # Preparar prompt
        prompt = f"""Analiza este {kind} y genera un título breve y descriptivo (máximo 60 caracteres).

El título debe:
- Ser específico sobre el problema
- Incluir el archivo/componente afectado si es visible
- Ser claro y conciso
- Estar en español

{kind.upper()}:
{content[:2000]}  # Limitar a 2000 caracteres

Título:"""

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",  # Modelo económico y rápido
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente que analiza errores de código y genera títulos descriptivos y concisos."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 100,
                "temperature": 0.3,
            },
            timeout=10,
        )
        
        if response.status_code == 200:
            result = response.json()
            title = result["choices"][0]["message"]["content"].strip()
            # Limpiar comillas si las tiene
            title = title.strip('"\'')
            return title[:60]  # Limitar longitud
        
    except Exception as e:
        # Si falla, usar análisis simple
        pass
    
    return None


def _analyze_simple(content: str, kind: str) -> str:
    """
    Análisis simple basado en patrones cuando no hay LLM disponible.
    Extrae información clave del error.
    """
    lines = content.split("\n")
    
    # Buscar archivo y línea
    file_line = None
    error_type = None
    error_message = None
    
    for line in lines[:10]:  # Revisar primeras 10 líneas
        # Patrón: /path/to/file:line:column
        if ":" in line and ("/" in line or "\\" in line):
            parts = line.split(":")
            if len(parts) >= 2:
                file_path = parts[0].strip()
                # Extraer solo nombre del archivo
                file_name = file_path.split("/")[-1].split("\\")[-1]
                if file_name.endswith((".py", ".js", ".ts", ".svelte", ".tsx", ".jsx")):
                    line_num = parts[1].strip() if len(parts) > 1 else ""
                    file_line = f"{file_name}:{line_num}" if line_num else file_name
                    break
        
        # Buscar tipo de error común
        if not error_type:
            for err_type in ["Error", "TypeError", "SyntaxError", "ReferenceError", "AttributeError"]:
                if err_type in line:
                    error_type = err_type
                    break
        
        # Buscar mensaje de error
        if not error_message and ("error" in line.lower() or "failed" in line.lower()):
            # Limpiar y tomar primeros 40 caracteres
            error_message = line.strip()[:40]
    
    # Construir título
    if file_line:
        if error_type:
            return f"{error_type} en {file_line}"
        elif error_message:
            return f"Error en {file_line}: {error_message}"
        else:
            return f"Error en {file_line}"
    elif error_type:
        return f"{error_type} detectado"
    elif error_message:
        return error_message
    else:
        # Título genérico basado en primeras palabras
        first_line = lines[0].strip()[:50] if lines else "Error desconocido"
        return first_line if first_line else f"{kind.capitalize()} capturado"
