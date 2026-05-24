import subprocess
import asyncio

async def execute_system_command(command: str):
    """
    Executes a shell command asynchronously and silently.
    Used for opening applications and controlling MacOS.
    """
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            print(f"Command execution failed: {command}")
            if stderr:
                print(f"Error: {stderr.decode('utf-8')}")
    except Exception as e:
        print(f"Failed to execute command '{command}': {str(e)}")
