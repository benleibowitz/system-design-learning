#!/usr/bin/env python3
"""
WebSocket Client with Interactive Chat Interface
Connects to a server and allows chatting with other clients
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.prompt import Prompt
from rich.align import Align
from rich.text import Text
import inquirer
import threading
from queue import Queue

console = Console()

class ChatClient:
    def __init__(self, server_url: str, username: str = None):
        self.server_url = server_url
        self.username = username
        self.client_id = None
        self.websocket = None
        self.messages = []
        self.users = []
        self.input_queue = Queue()
        self.connected = False
        self.server_name = None
        
    async def connect(self):
        """Connect to the server."""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            console.print(f"[green]Connected to {self.server_url}[/green]")
            
            # Start message receiver
            asyncio.create_task(self.receive_messages())
            
            # Send username if provided
            if self.username:
                await self.set_username(self.username)
                
            return True
        except Exception as e:
            console.print(f"[red]Failed to connect: {e}[/red]")
            return False
    
    async def receive_messages(self):
        """Receive messages from the server."""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_server_message(data)
        except websockets.exceptions.ConnectionClosed:
            self.connected = False
            console.print("[red]Disconnected from server[/red]")
    
    async def handle_server_message(self, data):
        """Process messages from the server."""
        msg_type = data.get("type")
        
        if msg_type == "welcome":
            self.client_id = data["client_id"]
            self.server_name = data["server"]
            self.log_message(f"System: {data['message']}")
            
        elif msg_type == "message":
            timestamp = datetime.fromisoformat(data["timestamp"]).strftime("%H:%M:%S")
            if data["to"] != "all":
                self.log_message(f"[{timestamp}] {data['from']} -> {data['to']}: {data['content']}")
            else:
                self.log_message(f"[{timestamp}] {data['from']}: {data['content']}")
                
        elif msg_type == "user_list":
            self.users.extend(data["users"])
            
        elif msg_type == "error":
            self.log_message(f"Error: {data['message']}")
    
    async def set_username(self, username: str):
        """Set the client's username."""
        self.username = username
        await self.send_message({
            "type": "set_name",
            "name": username
        })
    
    async def send_chat_message(self, content: str, to: str = "all"):
        """Send a chat message."""
        await self.send_message({
            "type": "message",
            "content": content,
            "to": to
        })
    
    async def request_user_list(self):
        """Request list of all users."""
        self.users = []  # Clear current list
        await self.send_message({
            "type": "list_users"
        })
    
    async def send_message(self, message: dict):
        """Send a message to the server."""
        if self.websocket and self.connected:
            await self.websocket.send(json.dumps(message))
    
    def log_message(self, message: str):
        """Add message to the log."""
        self.messages.append(message)
        if len(self.messages) > 50:
            self.messages.pop(0)
    
    def create_header_panel(self) -> Panel:
        """Create header panel."""
        text = f"[bold cyan]WebSocket Chat Client[/bold cyan]\n"
        text += f"Connected to: {self.server_name or 'Not connected'}\n"
        text += f"Username: {self.username or 'Not set'} | ID: {self.client_id or 'N/A'}"
        
        return Panel(
            Align.center(text),
            style="white on blue",
            height=5
        )
    
    def create_messages_panel(self) -> Panel:
        """Create messages panel."""
        msg_text = "\n".join(self.messages[-30:]) if self.messages else "No messages yet"
        return Panel(
            msg_text,
            title="Chat Messages",
            border_style="green",
            padding=(1, 2)
        )
    
    def create_users_panel(self) -> Panel:
        """Create online users panel."""
        if not self.users:
            users_text = "No users online"
        else:
            users_text = "Online Users:\n\n"
            for user in self.users:
                name = user.get("name", "Unknown")
                user_id = user.get("id", "")
                server = user.get("server", "")
                users_text += f"• {name} ({user_id}) @ {server}\n"
        
        return Panel(
            users_text,
            title="Users",
            border_style="yellow",
            width=30
        )
    
    async def interactive_input(self):
        """Handle interactive user input."""
        while self.connected:
            try:
                # Use a thread to handle blocking input
                loop = asyncio.get_event_loop()
                user_input = await loop.run_in_executor(None, self.get_user_input)
                
                if user_input:
                    await self.process_command(user_input)
                    
            except Exception as e:
                console.print(f"[red]Input error: {e}[/red]")
    
    def get_user_input(self) -> str:
        """Get input from user."""
        options = [
            "Send message",
            "Send private message",
            "List users",
            "Change username",
            "Quit"
        ]
        
        questions = [
            inquirer.List('action',
                        message="What would you like to do?",
                        choices=options)
        ]
        
        answers = inquirer.prompt(questions)
        if answers:
            return answers['action']
        return None
    
    async def process_command(self, action: str):
        """Process user commands."""
        if action == "Send message":
            message = Prompt.ask("Enter message")
            if message:
                await self.send_chat_message(message)
                
        elif action == "Send private message":
            # First get user list
            await self.request_user_list()
            await asyncio.sleep(0.5)  # Wait for response
            
            if self.users:
                choices = []
                for user in self.users:
                    name = user.get("name") or user.get("id")
                    choices.append(f"{name} ({user.get('server')})")
                
                questions = [
                    inquirer.List('recipient',
                                message="Select recipient:",
                                choices=choices)
                ]
                
                answers = inquirer.prompt(questions)
                if answers:
                    # Extract recipient name
                    recipient = answers['recipient'].split(' (')[0]
                    message = Prompt.ask(f"Message to {recipient}")
                    if message:
                        await self.send_chat_message(message, recipient)
            else:
                self.log_message("No users available")
                
        elif action == "List users":
            await self.request_user_list()
            
        elif action == "Change username":
            new_username = Prompt.ask("Enter new username")
            if new_username:
                await self.set_username(new_username)
                
        elif action == "Quit":
            if self.websocket:
                await self.websocket.close()
            self.connected = False
    
    async def run(self):
        """Run the client."""
        if not await self.connect():
            return
        
        # Create display
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="main"),
            Layout(name="input", size=3)
        )
        
        layout["header"].update(self.create_header_panel())
        
        layout["main"].split_row(
            Layout(self.create_messages_panel(), ratio=3),
            Layout(self.create_users_panel(), ratio=1)
        )
        
        layout["input"].update(Panel(
            "[cyan]Use the menu to send messages or perform actions[/cyan]",
            border_style="cyan"
        ))
        
        with Live(layout, console=console, screen=True, auto_refresh=False) as live:
            # Start input handler
            input_task = asyncio.create_task(self.interactive_input())
            
            while self.connected:
                # Update display
                layout["header"].update(self.create_header_panel())
                layout["main"].split_row(
                    Layout(self.create_messages_panel(), ratio=3),
                    Layout(self.create_users_panel(), ratio=1)
                )
                
                live.update(layout, refresh=True)
                await asyncio.sleep(0.1)
            
            input_task.cancel()

async def main():
    # Get connection details
    questions = [
        inquirer.Text('server',
                    message="Server URL (e.g., ws://localhost:8000)",
                    default="ws://localhost:8000"),
        inquirer.Text('username',
                    message="Your username",
                    default=f"User_{datetime.now().strftime('%H%M%S')}")
    ]
    
    answers = inquirer.prompt(questions)
    if not answers:
        return
    
    client = ChatClient(answers['server'], answers['username'])
    
    try:
        await client.run()
    except KeyboardInterrupt:
        console.print("\n[red]Client disconnected[/red]")
    finally:
        if client.websocket:
            await client.websocket.close()

if __name__ == "__main__":
    asyncio.run(main())
