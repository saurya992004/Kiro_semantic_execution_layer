from tools.app_tools import open_app
from tools.web_tools import search_web
from tools.system_tools import (
    shutdown_pc,
    restart_pc,
    sleep_pc,
    lock_pc,
    kill_process,
    clean_temp,
    empty_recycle_bin,
)


def route_intent(command: dict):

    intent = command.get("intent")
    action = command.get("action")
    params = command.get("parameters", {})

    if intent == "open_app":
        open_app(params.get("app_name"))

    elif intent == "web_search":
        search_web(params.get("query"))

    elif intent == "system_control":
        if action == "shutdown":
          shutdown_pc()

        elif action == "restart":
            restart_pc()

        elif action == "sleep":
            sleep_pc()

        elif action == "lock":
            lock_pc()

        elif action == "kill_process":
            kill_process(params.get("process_name"))

        elif action == "clean_temp":
            clean_temp()

        elif action == "empty_recycle_bin":
            empty_recycle_bin()

    else:
        print("Intent not recognized.")
