---
description: Backup all critical project data and configurations
argument-hint: [--target db|files|config|docker|all] [--location <path>] [--upload s3|gcs] [--rotate 7]
model: claude-sonnet-4-5-20250929
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# /system:backup-all

Backup: **${ARGUMENTS:-all systems}**

## Step 1: Create Backup Directory

```bash
BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"
```

## Step 2: Backup Database

```bash
# PostgreSQL
pg_dump $DB_NAME > "$BACKUP_DIR/database.sql"

# Verify
if [ -s "$BACKUP_DIR/database.sql" ]; then
  echo "✅ Database backed up"
fi
```

## Step 3: Backup Files

```bash
# Uploads, assets, etc.
tar -czf "$BACKUP_DIR/files.tar.gz" uploads/ public/assets/

# Config files
cp .env "$BACKUP_DIR/.env.backup"
cp -r config/ "$BACKUP_DIR/config/"
```

## Step 4: Backup Docker Volumes

```bash
docker run --rm -v volume_name:/data -v $BACKUP_DIR:/backup \
  ubuntu tar czf /backup/volume.tar.gz /data
```

## Step 5: Create Manifest

```bash
cat > "$BACKUP_DIR/manifest.json" << MANIFEST
{
  "timestamp": "$(date -Iseconds)",
  "database": { "size": "$(du -h $BACKUP_DIR/database.sql | cut -f1)" },
  "files": { "size": "$(du -h $BACKUP_DIR/files.tar.gz | cut -f1)" },
  "checksums": {
    "database": "$(sha256sum $BACKUP_DIR/database.sql | cut -d' ' -f1)",
    "files": "$(sha256sum $BACKUP_DIR/files.tar.gz | cut -d' ' -f1)"
  }
}
MANIFEST
```

## Step 6: Compress and Verify

```bash
cd backups
tar -czf "$(basename $BACKUP_DIR).tar.gz" "$(basename $BACKUP_DIR)"
sha256sum "$(basename $BACKUP_DIR).tar.gz" > "$(basename $BACKUP_DIR).tar.gz.sha256"
```

## Step 7: Upload (if requested)

```bash
if [ "$UPLOAD_TO_S3" = "true" ]; then
  aws s3 cp "$BACKUP_FILE" "s3://backups/$PROJECT_NAME/"
fi
```

## Step 8: Rotate Old Backups

```bash
# Keep last N backups
ls -t backups/*.tar.gz | tail -n +$((KEEP_LAST + 1)) | xargs rm -f
```

**Command Complete** 💾
