import tkinter as tk

from src.services.app_service import AppService
from src.ui.cli_interface import GymInterface


def main():
    root = tk.Tk()
    service = AppService()
    GymInterface(root, service, demo=True)
    root.mainloop()


if __name__ == "__main__":
    main()