#!/bin/bash
# Setup script para agregar helpers de git al PATH
# Uso: source setup-helpers.sh

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Agregar al PATH si no está ya
if [[ ":$PATH:" != *":$CLI_DIR:"* ]]; then
    export PATH="$PATH:$CLI_DIR"
    echo "✓ Helpers agregados al PATH:"
    echo "  - git-commit-cursor (commits de Cursor/IA)"
    echo "  - git-M (commits manuales)"
    echo ""
    echo "Para hacer permanente, agregá a tu ~/.zshrc o ~/.bashrc:"
    echo "  export PATH=\"\$PATH:$CLI_DIR\""
else
    echo "✓ Helpers ya están en PATH"
fi
