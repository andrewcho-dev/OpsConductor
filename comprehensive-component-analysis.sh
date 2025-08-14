#!/bin/bash

echo "=== COMPREHENSIVE FRONTEND COMPONENT ANALYSIS ==="
echo "Analyzing every single component, button, link, and feature..."

BASE_DIR="/home/enabledrm/frontend/src"

echo ""
echo "=== 1. AUTHENTICATION COMPONENTS ==="
find "$BASE_DIR/components/auth" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href" "$file" | head -5
    echo ""
done

echo ""
echo "=== 2. DASHBOARD COMPONENTS ==="
find "$BASE_DIR/components/dashboard" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file" 
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href\|Card" "$file" | head -5
    echo ""
done

echo ""
echo "=== 3. TARGETS COMPONENTS ==="
find "$BASE_DIR/components/targets" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href" "$file" | head -5
    echo ""
done

echo ""
echo "=== 4. JOBS COMPONENTS ==="
find "$BASE_DIR/components/jobs" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href" "$file" | head -5
    echo ""
done

echo ""
echo "=== 5. USERS COMPONENTS ==="
find "$BASE_DIR/components/users" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href" "$file" | head -5
    echo ""
done

echo ""
echo "=== 6. SYSTEM COMPONENTS ==="
find "$BASE_DIR/components/system" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -5
    echo "   UI Elements:"
    grep -n "Button\|TextField\|Modal\|Dialog\|onClick\|onSubmit\|href" "$file" | head -5
    echo ""
done

echo ""
echo "=== 7. LAYOUT COMPONENTS ==="
find "$BASE_DIR/components/layout" -name "*.js" -o -name "*.jsx" | while read file; do
    echo "📁 ANALYZING: $file"
    echo "   Functions/Components:"
    grep -n "const\|function\|class.*extends\|export.*function" "$file" | head -3
    echo "   Navigation Elements:"
    grep -n "Link\|NavLink\|href\|to=\|onClick" "$file" | head -5
    echo ""
done

echo ""
echo "=== COMPREHENSIVE ANALYSIS COMPLETE ==="