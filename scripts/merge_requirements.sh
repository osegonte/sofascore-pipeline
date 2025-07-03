#!/bin/bash

# Merge Stage 5 requirements with existing requirements

echo "🔗 Merging Stage 5 requirements with existing requirements.txt"

if [ -f "requirements.txt" ]; then
    echo "# Original requirements" > requirements_merged.txt
    cat requirements.txt >> requirements_merged.txt
    echo "" >> requirements_merged.txt
    echo "# Stage 5: Feature Engineering Requirements" >> requirements_merged.txt
    cat requirements_stage5.txt >> requirements_merged.txt
    
    echo "✅ Merged requirements saved to requirements_merged.txt"
    echo "📝 Review the merged file and update requirements.txt manually"
else
    cp requirements_stage5.txt requirements.txt
    echo "✅ Created new requirements.txt with Stage 5 dependencies"
fi
