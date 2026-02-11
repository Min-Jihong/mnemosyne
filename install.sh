#!/bin/bash
# =============================================================================
# Mnemosyne Installation Script
# =============================================================================
# One-liner: curl -fsSL https://raw.githubusercontent.com/Min-Jihong/mnemosyne/main/install.sh | bash
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emojis
BRAIN="🧠"
CHECK="✓"
CROSS="✗"
ARROW="→"

echo ""
echo -e "${PURPLE}${BRAIN} Mnemosyne Installation Script${NC}"
echo -e "${CYAN}   Your Digital Twin - Learn to Think Like You${NC}"
echo ""

# -----------------------------------------------------------------------------
# Check Prerequisites
# -----------------------------------------------------------------------------

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "  ${GREEN}${CHECK}${NC} $1 found"
        return 0
    else
        echo -e "  ${RED}${CROSS}${NC} $1 not found"
        return 1
    fi
}

echo -e "${BLUE}${ARROW} Checking prerequisites...${NC}"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
    PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
        echo -e "  ${GREEN}${CHECK}${NC} Python $PYTHON_VERSION found"
    else
        echo -e "  ${RED}${CROSS}${NC} Python 3.11+ required (found $PYTHON_VERSION)"
        echo -e "  ${YELLOW}Please install Python 3.11 or higher${NC}"
        exit 1
    fi
else
    echo -e "  ${RED}${CROSS}${NC} Python not found"
    echo -e "  ${YELLOW}Please install Python 3.11 or higher${NC}"
    exit 1
fi

check_command git || { echo -e "${RED}Please install git${NC}"; exit 1; }
check_command pip3 || check_command pip || { echo -e "${RED}Please install pip${NC}"; exit 1; }

echo ""

# -----------------------------------------------------------------------------
# Installation Options
# -----------------------------------------------------------------------------

INSTALL_DIR="${MNEMOSYNE_INSTALL_DIR:-$HOME/.local/mnemosyne}"
INSTALL_TYPE="${MNEMOSYNE_INSTALL_TYPE:-user}"

echo -e "${BLUE}${ARROW} Installation options:${NC}"
echo -e "  ${CYAN}Directory:${NC} $INSTALL_DIR"
echo -e "  ${CYAN}Type:${NC} $INSTALL_TYPE"
echo ""

# -----------------------------------------------------------------------------
# Clone Repository
# -----------------------------------------------------------------------------

echo -e "${BLUE}${ARROW} Cloning Mnemosyne repository...${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${YELLOW}Directory exists, updating...${NC}"
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    git clone https://github.com/Min-Jihong/mnemosyne.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "  ${GREEN}${CHECK}${NC} Repository ready"
echo ""

# -----------------------------------------------------------------------------
# Create Virtual Environment (optional)
# -----------------------------------------------------------------------------

USE_VENV="${MNEMOSYNE_USE_VENV:-true}"

if [ "$USE_VENV" = "true" ]; then
    echo -e "${BLUE}${ARROW} Creating virtual environment...${NC}"
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    echo -e "  ${GREEN}${CHECK}${NC} Virtual environment activated"
    echo ""
fi

# -----------------------------------------------------------------------------
# Install Dependencies
# -----------------------------------------------------------------------------

echo -e "${BLUE}${ARROW} Installing dependencies...${NC}"

pip install --upgrade pip --quiet
pip install -e ".[web]" --quiet

echo -e "  ${GREEN}${CHECK}${NC} Dependencies installed"
echo ""

# -----------------------------------------------------------------------------
# macOS Specific Setup
# -----------------------------------------------------------------------------

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}${ARROW} macOS detected, installing native capture support...${NC}"
    pip install -e ".[macos]" --quiet 2>/dev/null || {
        echo -e "  ${YELLOW}Note: macOS native capture requires additional setup${NC}"
    }
    echo -e "  ${GREEN}${CHECK}${NC} macOS support installed"
    echo ""
fi

# -----------------------------------------------------------------------------
# Create Shell Integration
# -----------------------------------------------------------------------------

echo -e "${BLUE}${ARROW} Setting up shell integration...${NC}"

# Detect shell
SHELL_NAME=$(basename "$SHELL")
SHELL_RC=""

case "$SHELL_NAME" in
    bash)
        SHELL_RC="$HOME/.bashrc"
        ;;
    zsh)
        SHELL_RC="$HOME/.zshrc"
        ;;
    fish)
        SHELL_RC="$HOME/.config/fish/config.fish"
        ;;
esac

if [ -n "$SHELL_RC" ]; then
    ALIAS_LINE="alias mnemosyne='$INSTALL_DIR/.venv/bin/mnemosyne'"
    PATH_LINE="export PATH=\"\$PATH:$INSTALL_DIR/.venv/bin\""
    
    if ! grep -q "mnemosyne" "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo "# Mnemosyne" >> "$SHELL_RC"
        echo "$PATH_LINE" >> "$SHELL_RC"
        echo -e "  ${GREEN}${CHECK}${NC} Added to $SHELL_RC"
    else
        echo -e "  ${YELLOW}Already configured in $SHELL_RC${NC}"
    fi
fi

echo ""

# -----------------------------------------------------------------------------
# Create Data Directory
# -----------------------------------------------------------------------------

echo -e "${BLUE}${ARROW} Creating data directory...${NC}"

mkdir -p "$HOME/.mnemosyne"
echo -e "  ${GREEN}${CHECK}${NC} Data directory: $HOME/.mnemosyne"
echo ""

# -----------------------------------------------------------------------------
# macOS Permissions Reminder
# -----------------------------------------------------------------------------

if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  macOS Permissions Required${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  To enable full functionality, grant these permissions:"
    echo ""
    echo -e "  ${CYAN}System Settings → Privacy & Security → Privacy:${NC}"
    echo -e "    ${ARROW} Accessibility"
    echo -e "    ${ARROW} Input Monitoring"
    echo -e "    ${ARROW} Screen Recording"
    echo ""
fi

# -----------------------------------------------------------------------------
# Success!
# -----------------------------------------------------------------------------

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ${BRAIN} Mnemosyne installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${CYAN}Get started:${NC}"
echo ""
echo -e "    ${ARROW} Run setup wizard:     ${GREEN}mnemosyne setup${NC}"
echo -e "    ${ARROW} Start web interface:  ${GREEN}mnemosyne web${NC}"
echo -e "    ${ARROW} Start recording:      ${GREEN}mnemosyne record${NC}"
echo ""
echo -e "  ${CYAN}Documentation:${NC}"
echo -e "    ${ARROW} https://github.com/Min-Jihong/mnemosyne"
echo ""

if [ "$USE_VENV" = "true" ]; then
    echo -e "  ${YELLOW}Note: Activate the environment first:${NC}"
    echo -e "    ${GREEN}source $INSTALL_DIR/.venv/bin/activate${NC}"
    echo ""
fi

echo -e "  ${PURPLE}Happy cloning yourself! ${BRAIN}${NC}"
echo ""
