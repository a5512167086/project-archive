from typing import Any, Dict, List


def get_enabled_commands(
    command_list: List[Dict[str, Any]], module_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    enabled_commands = []

    for command in command_list:
        if command["type"] == "Custom":
            continue

        matched_module = next(
            (
                module
                for module in module_list
                if module["chinese_name"]
                == command["chinese_name"].replace(" Command", "")
            ),
            None,
        )

        if matched_module and matched_module["is_enabled"]:
            enabled_commands.append(
                {
                    "command_keyword": command["command_keyword"],
                    "type": command["type"],
                    "status": True,
                }
            )

    return enabled_commands
