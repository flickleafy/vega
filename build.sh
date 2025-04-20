#!/bin/bash

# Set up directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/dist"
AUTOSTART_DIR="$SCRIPT_DIR/autostart"

echo "Building executables..."
# Build all executables
pyinstaller -F -n vega-server-gateway vega_server/gateway/main.py
pyinstaller -F -n vega-server-root vega_server/rootspace/main.py
pyinstaller -F -n vega-server-user vega_server/userspace/main.py
pyinstaller -F -n vega-client vega_client/main.py

# Ensure the dist directory exists
mkdir -p "$BUILD_DIR"

echo "Copying autostart files to dist folder..."
# Copy autostart files to dist folder
cp -r "$AUTOSTART_DIR"/*.desktop "$BUILD_DIR"

# Create icons directory
mkdir -p "$BUILD_DIR/icons"

# Copy any icons (assuming they're in vega_client)
if [ -f "$SCRIPT_DIR/vega_client/cpu_v.png" ]; then
    cp "$SCRIPT_DIR/vega_client/cpu_v.png" "$BUILD_DIR/icons/vega-icon.png"
fi

echo "Creating installer.sh script..."
# Create installer script
cat > "$BUILD_DIR/installer.sh" << 'EOF'
#!/bin/bash

# Vega Application Installer Script

# Exit on any error
set -e

# Get the directory where the installer script is located
INSTALLER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define default install paths for the application
# System-wide install locations (require sudo)
SYSTEM_BIN_DIR="/usr/local/bin/vega_suit"
SYSTEM_APP_DIR="/usr/local/share/vega_suit"
SYSTEM_APPS_DIR="/usr/share/applications"
SYSTEM_ICONS_DIR="/usr/share/icons/hicolor/256x256/apps"

# User-specific install locations (don't require sudo)
USER_BIN_DIR="$HOME/.local/bin/vega_suit"
USER_APP_DIR="$HOME/.local/share/vega_suit"
USER_APPS_DIR="$HOME/.local/share/applications"
USER_ICONS_DIR="$HOME/.local/share/icons"

# Common directories
AUTOSTART_DIR="$HOME/.config/autostart"
CONFIG_DIR="$HOME/.config/vega_suit"
DESKTOP_DIR="$HOME/Desktop"

echo "Vega Application Installer"
echo "=========================="
echo ""

# Check for sudo privileges to determine installation type
SYSTEM_INSTALL=0
if sudo -n true 2>/dev/null; then
    echo "Sudo access available. Would you like to install Vega system-wide? (y/n)"
    read -r choice
    if [[ "$choice" =~ ^[Yy]$ ]]; then
        SYSTEM_INSTALL=1
        echo "Proceeding with system-wide installation."
    else
        echo "Proceeding with user-only installation."
    fi
else
    echo "No sudo access detected. Proceeding with user-only installation."
fi

# Set installation directories based on install type
if [ $SYSTEM_INSTALL -eq 1 ]; then
    BIN_DIR="$SYSTEM_BIN_DIR"
    APP_DIR="$SYSTEM_APP_DIR"
    APPS_DIR="$SYSTEM_APPS_DIR"
    ICONS_DIR="$SYSTEM_ICONS_DIR"
else
    BIN_DIR="$USER_BIN_DIR"
    APP_DIR="$USER_APP_DIR"
    APPS_DIR="$USER_APPS_DIR"
    ICONS_DIR="$USER_ICONS_DIR"
fi

echo "Installing Vega application..."

# Create destination directories if they don't exist
mkdir -p "$BIN_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$APPS_DIR"
mkdir -p "$ICONS_DIR"
mkdir -p "$AUTOSTART_DIR"
mkdir -p "$CONFIG_DIR"

# Install executables
echo "Installing Vega executables to $BIN_DIR..."
if [ $SYSTEM_INSTALL -eq 1 ]; then
    # System-wide installation requires sudo
    sudo install -m 755 "$INSTALLER_DIR/vega-client" "$BIN_DIR/"
    sudo install -m 755 "$INSTALLER_DIR/vega-server-gateway" "$BIN_DIR/"
    sudo install -m 755 "$INSTALLER_DIR/vega-server-user" "$BIN_DIR/"
    sudo install -m 755 "$INSTALLER_DIR/vega-server-root" "$BIN_DIR/"
else
    # User-only installation
    install -m 755 "$INSTALLER_DIR/vega-client" "$BIN_DIR/"
    install -m 755 "$INSTALLER_DIR/vega-server-gateway" "$BIN_DIR/"
    install -m 755 "$INSTALLER_DIR/vega-server-user" "$BIN_DIR/"
    install -m 755 "$INSTALLER_DIR/vega-server-root" "$BIN_DIR/"
fi

# Install icons
echo "Installing icons..."
if [ -d "$INSTALLER_DIR/icons" ]; then
    if [ $SYSTEM_INSTALL -eq 1 ]; then
        sudo install -m 644 "$INSTALLER_DIR/icons/vega-icon.png" "$ICONS_DIR/"
    else
        install -m 644 "$INSTALLER_DIR/icons/vega-icon.png" "$ICONS_DIR/"
    fi
fi

# Create desktop file for client (visible in applications menu)
echo "Creating application menu entry..."
DESKTOP_FILE_CONTENT="[Desktop Entry]
Type=Application
Name=Vega Client
Comment=Vega Client Application
Exec=$BIN_DIR/vega-client
Icon=vega-icon
Terminal=false
Categories=Utility;System;"

if [ $SYSTEM_INSTALL -eq 1 ]; then
    echo "$DESKTOP_FILE_CONTENT" | sudo tee "$APPS_DIR/vega-client.desktop" > /dev/null
else
    echo "$DESKTOP_FILE_CONTENT" > "$APPS_DIR/vega-client.desktop"
fi

# Create desktop shortcut
echo "Creating desktop shortcut..."
echo "$DESKTOP_FILE_CONTENT" > "$DESKTOP_DIR/vega-client.desktop"
chmod +x "$DESKTOP_DIR/vega-client.desktop"

# Setup autostart for background services
echo "Setting up autostart services..."

# Create autostart entry for vega-server-gateway
cat > "$AUTOSTART_DIR/vega-server-gateway.desktop" << EOT
[Desktop Entry]
Type=Application
Exec=sh -c "$BIN_DIR/vega-server-gateway >> $HOME/.local/share/vega_suit/vega-server-gateway.log 2>&1"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Vega Server Gateway
Comment=Vega Server Gateway background service
EOT

# Create autostart entry for vega-server-user
cat > "$AUTOSTART_DIR/vega-server-user.desktop" << EOT
[Desktop Entry]
Type=Application
Exec=sh -c "$BIN_DIR/vega-server-user >> $HOME/.local/share/vega_suit/vega-server-user.log 2>&1"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Vega Server User
Comment=Vega Server User background service
EOT

# Create log directory
mkdir -p "$HOME/.local/share/vega_suit"

# For root service, we need to create a system service that runs early
if [ $SYSTEM_INSTALL -eq 1 ]; then
    echo "Setting up root service as a systemd service..."
    
    # Create systemd service file
    SERVICE_FILE="/etc/systemd/system/vega-server-root.service"
    sudo tee $SERVICE_FILE > /dev/null << EOT
[Unit]
Description=Vega Server Root Service
After=network.target

[Service]
ExecStart=$BIN_DIR/vega-server-root
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
EOT
    
    # Enable and start the service
    sudo systemctl daemon-reload
    sudo systemctl enable vega-server-root.service
    sudo systemctl start vega-server-root.service
    
    echo "Root service installed and started as a systemd service."
else
    echo "Warning: Without system-wide installation, the root service cannot be properly set up as a systemd service."
    echo "The root service will be available at $BIN_DIR/vega-server-root but will need to be run manually with sudo privileges."
    echo ""
    echo "To properly install the root service, you may run the following commands later with sudo privileges:"
    echo "sudo cp \"$BIN_DIR/vega-server-root\" /usr/local/bin/"
    echo "sudo bash -c 'cat > /etc/systemd/system/vega-server-root.service << EOT"
    echo "[Unit]"
    echo "Description=Vega Server Root Service"
    echo "After=network.target"
    echo ""
    echo "[Service]"
    echo "ExecStart=/usr/local/bin/vega-server-root"
    echo "Restart=on-failure"
    echo "User=root"
    echo ""
    echo "[Install]"
    echo "WantedBy=multi-user.target"
    echo "EOT'"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable vega-server-root.service"
    echo "sudo systemctl start vega-server-root.service"
fi

echo ""
echo "Installation complete!"
echo "You can find the Vega Client in your applications menu and on your desktop."
echo "Background services have been configured to start automatically at system boot."
echo "Logs will be stored in $HOME/.local/share/vega/"
EOF

# Make the installer script executable
chmod +x "$BUILD_DIR/installer.sh"

echo "Build complete! Installer created at $BUILD_DIR/installer.sh"