# Scrcpy GUI

A GTK 4 and libadwaita graphical interface for `scrcpy`.

## Install on Linux

Install Python GObject, GTK 4, libadwaita 1, `scrcpy`, and `adb` using your
distribution's package manager. Then, from this directory, run:

```sh
chmod +x install.sh
./install.sh
```

This installs the application for the current user under `~/.local`. To install
it system-wide, run `sudo ./install.sh` instead.

Do not install this application with `pip install .`. The GUI depends on native
GTK libraries and Python bindings supplied by the operating system. On Arch and
other distributions that enforce PEP 668, pip blocks system-wide package
installation by design. The provided installer copies the application files
without modifying the system Python environment.
