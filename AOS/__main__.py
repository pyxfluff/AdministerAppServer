# pyxfluff 2024 - 2025

import il
import asyncio
import logging
import platform

from sys import argv
from pathlib import Path
from fastapi import FastAPI

from AOS import AOSError, globals as var

if not var.is_dev:
    il.set_log_file(Path("/etc/adm/log"))
    logging.getLogger("uvicorn.error").disabled = True

def serve_web_server():
    il.cprint("[-] Loading Uvicorn...", 32)

    from AOS import load_fastapi_app
    app = load_fastapi_app()

def help_command():
    pass


il.box(45, f"Administer App Server", f"v{var.version}")

if __name__ != "__main__":
    # il.cprint("AOS is running as a module, disregarding.", 31)
    #return
    pass

try:
    _ = argv[1]
except IndexError:
    help_command()
    raise AOSError("A command is required.")

match argv[1]:
    case "serve":
        try:
            serve_web_server()
        except IndexError:
            il.cprint("\n[x]: incorrect usage of `serve`\n\nusage: AOS serve [host] [port]", 31)

    case "help":
        help_command()

    case "usage":
        from AOS.reporting.GraphReporter import *

    case _:
        il.cprint("\n[x]: command not found, showing help", 31)
        help_command()

def main():
    # diseregard
    pass
