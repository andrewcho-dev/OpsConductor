#!/bin/bash

# Script to standardize all datatable pages with CSS classes

echo "🔧 Standardizing all datatable pages..."

# Files to fix
files=(
  "/home/enabledrm/frontend/src/components/targets/UniversalTargetList.js"
  "/home/enabledrm/frontend/src/components/jobs/JobList.js"
  "/home/enabledrm/frontend/src/components/system/SystemManagement.js"
  "/home/enabledrm/frontend/src/components/jobs/AdvancedJobView.js"
  "/home/enabledrm/frontend/src/components/monitoring/InfrastructureMonitoring.js"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "Fixing: $file"
    
    # Replace pagination Box containers
    sed -i 's/sx={{ display: '\''flex'\'', justifyContent: '\''space-between'\'', alignItems: '\''center'\'', mt: 1, py: 1, px: 1, flexShrink: 0 }}/className="datatable-pagination-area"/g' "$file"
    
    # Replace table containers with calc heights
    sed -i 's/maxHeight: '\''calc(100vh - 140px)'\''/maxHeight: '\''100%'\''/g' "$file"
    sed -i 's/maxHeight: '\''calc(100vh - 200px)'\''/maxHeight: '\''100%'\''/g' "$file"
    
    echo "✅ Fixed: $file"
  else
    echo "❌ File not found: $file"
  fi
done

echo "🎉 All datatable pages standardized!"