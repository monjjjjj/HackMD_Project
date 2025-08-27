#!/bin/bash

echo "Checking OpenSearch status..."
echo "================================"

# Check if container is running
CONTAINER_STATUS=$(docker ps --filter "name=opensearch" --format "{{.Status}}" 2>/dev/null)

if [ -z "$CONTAINER_STATUS" ]; then
    echo "❌ OpenSearch container is not running"
    echo ""
    echo "Trying to start OpenSearch..."
    docker-compose up -d opensearch
    echo ""
    echo "Please wait for the download to complete (5-10 minutes)"
    echo "The image is about 820MB"
else
    echo "✅ OpenSearch container is running: $CONTAINER_STATUS"
    echo ""
    echo "Testing connection..."
    curl -s http://localhost:9200 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ OpenSearch is ready!"
        echo ""
        echo "OpenSearch info:"
        curl -s http://localhost:9200 | python3 -m json.tool | head -10
    else
        echo "⏳ OpenSearch is starting up, please wait..."
    fi
fi

echo ""
echo "================================"
echo "You can run this script again to check status:"
echo "bash check_opensearch.sh"