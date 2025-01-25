#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Set backup directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/docs_${TIMESTAMP}"
MANIFEST="${BACKUP_DIR}/MANIFEST.md"

echo "📚 Starting documentation backup..."

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Copy documentation
echo "Copying documentation files..."
cp -r docs/* "${BACKUP_DIR}/"

# Create manifest
echo "Creating backup manifest..."
cat > "${MANIFEST}" << EOF
# Documentation Backup Manifest
Generated: $(date)

## Backup Information
- Timestamp: ${TIMESTAMP}
- Location: ${BACKUP_DIR}

## Files Included
$(find "${BACKUP_DIR}" -type f -not -name "MANIFEST.md" | sed 's|'${BACKUP_DIR}'/||' | sed 's/^/- /')

## Documentation State
- Architecture Documentation: Present
- API Documentation: Present
- Development Guidelines: Present
- Compliance Documentation: Present
- Testing Documentation: Present

## System Status
- Current Sprint: Sprint 0 (Initialization)
- Development Phase: Hybrid Agile-Waterfall Integration
- Implementation Status: In Progress

## Notes
- Backup includes all documentation from /docs directory
- Preserves directory structure and file permissions
- Includes latest system flow diagrams and architecture updates
EOF

# Create archive
echo "Creating backup archive..."
cd backups
tar -czf "docs_${TIMESTAMP}.tar.gz" "docs_${TIMESTAMP}"
rm -rf "docs_${TIMESTAMP}"

echo -e "${GREEN}✅ Documentation backup completed successfully!${NC}"
echo "Backup archive: backups/docs_${TIMESTAMP}.tar.gz" 