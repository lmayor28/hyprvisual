import sys
from tui_app import DisplayTUIApp

def main():
    """Entry point for hyprmonitor display-tui."""
    app = DisplayTUIApp()
    app.run()

if __name__ == "__main__":
    main()
