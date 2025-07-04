#!/bin/bash

echo "WARNING: This will remove all containers, container data, and data volumes. This action cannot be undone!"
read -p "Are you sure you want to proceed? (y/N) " -n 1 -r
echo    # Move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled."
    exit 1
fi

echo "Stopping and removing all containers with volumes..."
docker compose down -v --remove-orphans

echo "Cleaning up bind-mounted data directories..."
BIND_MOUNTS=(
  "./volumes/db/data"
)

for DIR in "${BIND_MOUNTS[@]}"; do
  if [ -d "$DIR" ]; then
    echo "Deleting $DIR..."
    rm -rf "$DIR"
  else
    echo "Directory $DIR does not exist. Skipping..."
  fi
done

echo "Removing named volumes (if any remain)..."
docker volume prune -f

echo "Regenerating JWT secrets..."
if [ -f "generate-jwt.mjs" ]; then
  echo "Generating new secrets..."
  node generate-jwt.mjs > /tmp/new_secrets.txt
  echo "New secrets generated. Please update your .env.development file with:"
  cat /tmp/new_secrets.txt
  rm /tmp/new_secrets.txt
else
  echo "generate-jwt.mjs not found. Skipping secret regeneration..."
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env.development with new secrets (if generated)"
echo "2. Run 'npm run dev' to start fresh"