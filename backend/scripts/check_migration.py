#!/usr/bin/env python3
"""
Migration validation script to catch common Alembic issues before they cause problems.
"""

import os
import re
import sys
from pathlib import Path


def check_enum_conversions(migration_content: str, filename: str) -> list:
    """Check for problematic enum conversions in migration files."""
    issues = []
    
    # Pattern to detect alter_column with enum types
    enum_alter_pattern = r'op\.alter_column\([^)]*ENUM\([^)]*\)[^)]*\)'
    
    if re.search(enum_alter_pattern, migration_content, re.DOTALL):
        issues.append(f"❌ {filename}: Found alter_column with ENUM type - use raw SQL with USING clause instead")
    
    # Pattern to detect enum type changes without USING clause
    enum_type_pattern = r'type_=.*Enum\('
    using_pattern = r'USING.*::text::'
    
    if re.search(enum_type_pattern, migration_content) and not re.search(using_pattern, migration_content):
        issues.append(f"⚠️  {filename}: Enum type change detected but no USING clause found")
    
    return issues


def check_default_handling(migration_content: str, filename: str) -> list:
    """Check for proper default value handling in enum conversions."""
    issues = []
    
    # Check if there are enum conversions with defaults but no DROP DEFAULT
    if 'existing_server_default' in migration_content and 'DROP DEFAULT' not in migration_content:
        if 'ENUM' in migration_content or 'Enum' in migration_content:
            issues.append(f"⚠️  {filename}: Enum conversion with default value but no DROP DEFAULT found")
    
    return issues


def check_migration_structure(migration_content: str, filename: str) -> list:
    """Check for proper migration structure."""
    issues = []
    
    # Check if both upgrade and downgrade functions exist
    if 'def upgrade()' not in migration_content:
        issues.append(f"❌ {filename}: Missing upgrade() function")
    
    if 'def downgrade()' not in migration_content:
        issues.append(f"❌ {filename}: Missing downgrade() function")
    
    # Check for empty downgrade function
    downgrade_match = re.search(r'def downgrade\(\)[^:]*:\s*(.*?)(?=def|\Z)', migration_content, re.DOTALL)
    if downgrade_match:
        downgrade_body = downgrade_match.group(1).strip()
        if not downgrade_body or downgrade_body == 'pass':
            issues.append(f"⚠️  {filename}: Empty downgrade() function - consider implementing proper rollback")
    
    return issues


def check_permissions(filepath: Path) -> list:
    """Check file permissions."""
    issues = []
    
    stat = filepath.stat()
    if stat.st_uid == 0:  # Root owned
        issues.append(f"❌ {filepath.name}: File is owned by root - run: sudo chown enabledrm:enabledrm {filepath}")
    
    return issues


def main():
    """Main validation function."""
    # Find all migration files
    migrations_dir = Path(__file__).parent.parent / 'alembic' / 'versions'
    
    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        sys.exit(1)
    
    migration_files = list(migrations_dir.glob('*.py'))
    
    if not migration_files:
        print("✅ No migration files found")
        return
    
    all_issues = []
    
    for migration_file in migration_files:
        try:
            content = migration_file.read_text()
            filename = migration_file.name
            
            # Run all checks
            issues = []
            issues.extend(check_enum_conversions(content, filename))
            issues.extend(check_default_handling(content, filename))
            issues.extend(check_migration_structure(content, filename))
            issues.extend(check_permissions(migration_file))
            
            all_issues.extend(issues)
            
        except Exception as e:
            all_issues.append(f"❌ Error reading {migration_file.name}: {e}")
    
    # Report results
    if all_issues:
        print("🚨 MIGRATION ISSUES FOUND:")
        print("=" * 50)
        for issue in all_issues:
            print(issue)
        print("=" * 50)
        print("\n📖 See /backend/alembic/migration_best_practices.md for solutions")
        sys.exit(1)
    else:
        print("✅ All migration files look good!")


if __name__ == '__main__':
    main()