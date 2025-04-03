#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Checking if FiveTenAlgo server is running..."

# Try different ports
for port in 8080 8082 5000; do
  echo "Trying port $port..."
  response=$(curl -s http://localhost:$port/api/test)
  
  if [[ $response == *"Server is running correctly"* ]]; then
    echo -e "${GREEN}Server is running on port $port!${NC}"
    echo "Response: $response"
    echo -e "\nYou can now view the application at: http://localhost:$port/"
    echo -e "Dashboard available at: http://localhost:$port/dashboard"
    exit 0
  fi
done

echo -e "${RED}Server doesn't seem to be running or accessible.${NC}"
echo "Check the server logs for more information."
exit 1 