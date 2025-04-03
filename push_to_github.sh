#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}FiveTenAlgo GitHub Push Script${NC}"
echo -e "This script will push your code to GitHub at: https://github.com/CodingFreeze/FiveTenAlgo.git"
echo

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    exit 1
fi

# Check if the repository is already initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    
    echo -e "${YELLOW}Adding remote repository...${NC}"
    git remote add origin https://github.com/CodingFreeze/FiveTenAlgo.git
else
    echo -e "${GREEN}Git repository already initialized${NC}"
    
    # Check if the remote is already set
    if ! git remote -v | grep -q "origin"; then
        echo -e "${YELLOW}Adding remote repository...${NC}"
        git remote add origin https://github.com/CodingFreeze/FiveTenAlgo.git
    else
        echo -e "${GREEN}Remote repository already set${NC}"
    fi
fi

# Create .gitignore file if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}Creating .gitignore file...${NC}"
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/

# Data files
data/*.json

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
EOF
    echo -e "${GREEN}.gitignore file created${NC}"
else
    echo -e "${GREEN}.gitignore file already exists${NC}"
fi

# Stage all files
echo -e "${YELLOW}Staging files...${NC}"
git add .

# Commit changes
echo -e "${YELLOW}Committing changes...${NC}"
git commit -m "Initial commit of FiveTenAlgo"

# Push to GitHub
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push -u origin master

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pushed to GitHub!${NC}"
    echo -e "Visit https://github.com/CodingFreeze/FiveTenAlgo to view your repository."
else
    echo -e "${RED}Failed to push to GitHub.${NC}"
    echo "You might need to authenticate with your GitHub credentials."
    echo "If you're using GitHub CLI, try running 'gh auth login' first."
    echo "If you're using Git credentials, make sure they're correctly configured."
fi 