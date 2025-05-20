#!/usr/bin/env python3
"""
Quick Start Script for WebSocket Demo
Helps launch multiple servers and clients easily
"""

import subprocess
import sys
import time
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import inquirer

console = Console()

class WebSocketDemo:
    def __init__(self):
        self.processes = []
        self.servers = []
        self.clients = []
        
    def start_server(self, port: int, name: str, connect_to: str = None):
        """Start a server instance."""
        cmd = [sys.executable, "websocket_server.py", "--port", str(port), "--name", name]
        
        if connect_to:
            cmd.extend(["--connect", connect_to])
            
        process = subprocess.Popen(cmd, creationdate=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        self.processes.append(process)
        self.servers.append({
            "name": name,
            "port": port,
            "process": process
        })
        
        console.print(f"[green]Started server {name} on port {port}[/green]")
        
    def start_client(self, server_url: str, username: str):
        """Start a client instance."""
        cmd = [sys.executable, "websocket_client.py"]
        
        # Create temporary script to pass parameters
        temp_script = f"""
import asyncio
import sys
sys.path.append('.')
from websocket_client import ChatClient

async def main():
    client = ChatClient("{server_url}", "{username}")
    await client.run()

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        # Write temporary script
        temp_file = f"temp_client_{username}.py"
        with open(temp_file, "w") as f:
            f.write(temp_script)
            
        process = subprocess.Popen([sys.executable, temp_file], 
                                 creationdate=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        self.processes.append(process)
        self.clients.append({
            "username": username,
            "server_url": server_url,
            "process": process,
            "temp_file": temp_file
        })
        
        console.print(f"[green]Started client {username} connecting to {server_url}[/green]")
        
    def show_status(self):
        """Show status of all servers and clients."""
        table = Table(title="WebSocket Demo Status")
        table.add_column("Type", style="cyan")
        table.add_column("Name/User", style="magenta")
        table.add_column("Port/URL", style="yellow")
        table.add_column("Status", style="green")
        
        for server in self.servers:
            status = "Running" if server["process"].poll() is None else "Stopped"
            table.add_row("Server", server["name"], str(server["port"]), status)
            
        for client in self.clients:
            status = "Running" if client["process"].poll() is None else "Stopped"
            table.add_row("Client", client["username"], client["server_url"], status)
            
        console.print(table)
        
    def cleanup(self):
        """Clean up all processes and temporary files."""
        console.print("[yellow]Cleaning up...[/yellow]")
        
        # Terminate all processes
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                
        # Remove temporary files
        for client in self.clients:
            if os.path.exists(client["temp_file"]):
                os.remove(client["temp_file"])
                
        console.print("[green]Cleanup complete[/green]")
        
    def run_demo(self):
        """Run interactive demo."""
        console.print(Panel.fit(
            "[bold cyan]WebSocket Chat Demo[/bold cyan]\n\n"
            "This demo shows server-client and inter-server communication.\n"
            "Servers can communicate with each other to relay messages between clients.",
            border_style="cyan"
        ))
        
        while True:
            choices = [
                "Start a new server",
                "Start a new client",
                "Show status",
                "Run example scenario",
                "Quit"
            ]
            
            questions = [
                inquirer.List('action',
                            message="What would you like to do?",
                            choices=choices)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:
                break
                
            action = answers['action']
            
            if action == "Start a new server":
                questions = [
                    inquirer.Text('port',
                                message="Server port",
                                default=str(8000 + len(self.servers))),
                    inquirer.Text('name',
                                message="Server name",
                                default=f"Server{len(self.servers) + 1}"),
                    inquirer.Text('connect_to',
                                message="Connect to other servers (optional, format: host:port,host:port)",
                                default="")
                ]
                
                answers = inquirer.prompt(questions)
                if answers:
                    self.start_server(
                        int(answers['port']),
                        answers['name'],
                        answers['connect_to'] if answers['connect_to'] else None
                    )
                    
            elif action == "Start a new client":
                questions = [
                    inquirer.Text('server_url',
                                message="Server URL",
                                default="ws://localhost:8000"),
                    inquirer.Text('username',
                                message="Username",
                                default=f"User{len(self.clients) + 1}")
                ]
                
                answers = inquirer.prompt(questions)
                if answers:
                    self.start_client(answers['server_url'], answers['username'])
                    
            elif action == "Show status":
                self.show_status()
                
            elif action == "Run example scenario":
                self.run_example_scenario()
                
            elif action == "Quit":
                break
                
    def run_example_scenario(self):
        """Run an example scenario with multiple servers and clients."""
        console.print("[cyan]Starting example scenario...[/cyan]")
        
        # Start three servers
        console.print("[yellow]Starting 3 servers...[/yellow]")
        self.start_server(8000, "Server1")
        time.sleep(1)
        self.start_server(8001, "Server2", "localhost:8000")
        time.sleep(1)
        self.start_server(8002, "Server3", "localhost:8000,localhost:8001")
        time.sleep(2)
        
        # Start clients on different servers
        console.print("[yellow]Starting 4 clients on different servers...[/yellow]")
        self.start_client("ws://localhost:8000", "Alice")
        time.sleep(1)
        self.start_client("ws://localhost:8001", "Bob")
        time.sleep(1)
        self.start_client("ws://localhost:8002", "Charlie")
        time.sleep(1)
        self.start_client("ws://localhost:8000", "Diana")
        
        console.print("""
[green]Example scenario started![/green]

You now have:
- 3 interconnected servers (Server1, Server2, Server3)
- 4 clients connected to different servers

Try these experiments:
1. Send a broadcast message from any client - all clients should receive it
2. Send a private message between clients on different servers
3. Watch how servers relay messages to reach the correct recipient
4. Disconnect a server and see how it affects message routing

The servers are interconnected, so messages can route through the network
to reach any client regardless of which server they're connected to.
""")
        
def main():
    demo = WebSocketDemo()
    
    try:
        demo.run_demo()
    except KeyboardInterrupt:
        console.print("\n[red]Demo interrupted[/red]")
    finally:
        demo.cleanup()

if __name__ == "__main__":
    main()
