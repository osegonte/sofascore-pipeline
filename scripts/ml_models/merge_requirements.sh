#!/bin/bash

# Merge Stage 6 requirements with existing requirements

echo "🔗 Merging Stage 6 ML requirements with existing requirements.txt"

if [ -f "requirements.txt" ]; then
    echo "# Original requirements" > requirements_stage6_merged.txt
    cat requirements.txt >> requirements_stage6_merged.txt
    echo "" >> requirements_stage6_merged.txt
    echo "# Stage 6: ML Model Development Requirements" >> requirements_stage6_merged.txt
    cat requirements_stage6.txt >> requirements_stage6_merged.txt
    
    echo "✅ Merged requirements saved to requirements_stage6_merged.txt"
    echo "📝 Review the merged file and update requirements.txt manually"
else
    cp requirements_stage6.txt requirements.txt
    echo "✅ Created new requirements.txt with Stage 6 dependencies"
fi
