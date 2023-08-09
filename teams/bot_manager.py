import subprocess
from common.rabbit_comms import publish, clear_queue

class BotManager:
    def __init__(self):
        self.user_processes = {}

    def handle_command(self, command, user_id=None, tenant_id=None, user_name=None, email_address=None):
        if user_id:
            if command.lower() == "start":
                #start the bot
                """start the bot"""
                publish(f"Starting bot for user {user_id}...", user_id)
                if user_id in self.user_processes and self.user_processes[user_id].poll() is None:
                    publish(f"Bot is already running for user {user_id}", user_id)
                else:
                    clear_queue(user_id)
                    process = subprocess.Popen(['python', 'ai.py', user_id, tenant_id, user_name, email_address])
                    self.user_processes[user_id] = process

            elif command.lower() == "quiet_start":
                #start the bot
                """start the bot"""
                if user_id in self.user_processes and self.user_processes[user_id].poll() is None:
                    #publish(f"Bot is already running for user {user_id}", user_id)
                    """do nothing"""
                    return
                else:
                    publish(f"Starting bot for user {user_id}...", user_id)
                    clear_queue(user_id)
                    process = subprocess.Popen(['python', 'ai.py', user_id, tenant_id, user_name, email_address])
                    self.user_processes[user_id] = process
                    return

            elif command.lower() == "stop":
                #stop the bot
                """stop the bot"""
                publish(f"Stopping bot.", user_id)
                if user_id in self.user_processes:
                    self.user_processes[user_id].terminate()
                    self.user_processes[user_id].wait()
                    del self.user_processes[user_id]
                    publish(f"Bot stopped.", user_id)
                else:
                    publish(f"No bot to stop.", user_id)

            elif command.lower() == "restart":
                #stop the bot
                """restart the bot"""
                clear_queue(user_id)
                publish(f"Restarting bot.", user_id)
                if user_id in self.user_processes:
                    self.user_processes[user_id].terminate()
                    self.user_processes[user_id].wait()
                    del self.user_processes[user_id]
                process = subprocess.Popen(['python', 'ai.py', user_id, tenant_id, user_name, email_address])
                self.user_processes[user_id] = process
                publish(f"Bot restarted.", user_id)
            elif command.lower() == "list_bots":
                for process in self.user_processes:
                    publish(f"Instances: {process} for {user_id}", user_id)
            elif command.lower() == "stop_bots":
                self.stop_all_processes(user_id)

    def stop_all_processes(self, request_user_id):
        """Stop all running bots."""
        for user_id, process in self.user_processes.items():
            if process.poll() is None:  # Check if the process is running
                publish(f"Stopping bot for user {user_id}...", request_user_id)
                process.terminate()
                process.wait()
                publish(f"Bot stopped for user {user_id}", request_user_id)

        # Clear the dictionary after stopping all processes
        self.user_processes.clear()