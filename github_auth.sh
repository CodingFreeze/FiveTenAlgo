#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}FiveTenAlgo GitHub Authentication Script${NC}"
echo "This script will update the remote URL with your GitHub credentials and push the code."
echo

# Ask for GitHub username
read -p "Enter your GitHub username: " github_username

# Ask for personal access token (PAT) securely
echo "Enter your GitHub Personal Access Token (input will be hidden):"
read -s github_token
echo

if [ -z "$github_username" ] || [ -z "$github_token" ]; then
    echo -e "${RED}Error: Username or token cannot be empty${NC}"
    exit 1
fi

# Update the remote URL
echo -e "${YELLOW}Updating remote URL with credentials...${NC}"
git remote set-url origin "https://$github_username:$github_token@github.com/CodingFreeze/FiveTenAlgo.git"

# Push to GitHub
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push -u origin main

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pushed to GitHub!${NC}"
    echo -e "Visit https://github.com/CodingFreeze/FiveTenAlgo to view your repository."
else
    echo -e "${RED}Failed to push to GitHub.${NC}"
    echo "Check your credentials and make sure you have the correct permissions."
fi 