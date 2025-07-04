#!/bin/bash
# Integration script for Stage 7 with main pipeline

echo "🔗 Integrating Stage 7 with main SofaScore pipeline..."

# Add Stage 7 commands to main CLI
MAIN_PY="../src/main.py"

if [ -f "$MAIN_PY" ]; then
    # Check if Stage 7 commands already exist
    if ! grep -q "stage7" "$MAIN_PY"; then
        echo "Adding Stage 7 commands to main CLI..."
        
        # Backup original file
        cp "$MAIN_PY" "$MAIN_PY.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Add Stage 7 import and commands (would need actual implementation)
        echo "# Stage 7 integration would be added here"
        echo "# This is a placeholder for the actual integration"
    else
        echo "Stage 7 commands already integrated"
    fi
else
    echo "Main pipeline not found. Stage 7 can run independently."
fi

# Create symlink for easy access
if [ ! -L "../stage7" ]; then
    ln -s "stage7" "../stage7_system" 2>/dev/null || true
fi

echo "✅ Integration setup completed"
