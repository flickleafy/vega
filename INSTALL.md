# Summary

Informations about current install script practices included in the `build.sh` file

1. **Supports both system-wide and user-only installations**:
   - If the user has sudo access, they can choose to install system-wide
   - Otherwise, it defaults to a user-only installation

2. **Uses proper Linux filesystem hierarchy locations**:
   - System-wide installation:
     - Executables: bin
     - Application data: `/usr/local/share/vega_suit`
     - Desktop entries: applications
     - Icons: apps

   - User-only installation:
     - Executables: `~/.local/bin` (standard user binary location)
     - Application data: `~/.local/share/vega_suit`
     - Desktop entries: `~/.local/share/applications`
     - Icons: `~/.local/share/icons`

3. **Configures services properly**:
   - Regular services launch at login through `~/.config/autostart`
   - Root service is set up as a proper systemd service when installing system-wide

4. **Implements proper log management**:
   - Log files are stored in `~/.local/share/vega_suit/` directory
   - Each service logs to its own file

5. **Uses proper installation methods**:
   - Uses the `install` command rather than plain `cp` for correct permissions
   - Sets appropriate file modes (755 for executables, 644 for data files)
