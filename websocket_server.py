#!/usr/bin/env python3
"""
WebSocket Server with Inter-Server Communication
Handles client connections and communicates with other servers
"""

import asyncio
import websockets
import json
import sys
import time
from datetime import datetime
from typing import Set, Dict, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text
import argparse

console = Console()

class ChatServer:
    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self.clients: Dict[str, Dict] = {}  # websocket -> client info
        self.servers: Set[websockets.WebSocketClientProtocol] = set()
        self.server_ports: Set[int] = {port}  # Track known server ports
        self.messages = []
        self.start_time = datetime.now()
        
    async def register_client(self, websocket, path):
        """Handle new client connection."""
        client_id = f"client_{len(self.clients) + 1}"
        
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "welcome",
            "client_id": client_id,
            "server": self.name,
            "message": f"Connected to {self.name}"
        }))
        
        # Store client info
        self.clients[websocket] = {
            "id": client_id,
            "name": None,
            "connected_at": datetime.now()
        }
        
        self.log_message(f"Client {client_id} connected")
        
        # Notify other servers about new client
        await self.broadcast_to_servers({
            "type": "client_connected",
            "client_id": client_id,
            "server": self.name
        })
        
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def handle_client_message(self, websocket, raw_message):
        """Process messages from clients."""
        try:
            message = json.loads(raw_message)
            client_info = self.clients[websocket]
            
            if message["type"] == "set_name":
                client_info["name"] = message["name"]
                self.log_message(f"Client {client_info['id']} set name to {message['name']}")
                
            elif message["type"] == "message":
                # Create message packet
                msg_packet = {
                    "type": "message",
                    "from": client_info["name"] or client_info["id"],
                    "to": message.get("to", "all"),
                    "content": message["content"],
                    "server": self.name,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.log_message(f"Message from {msg_packet['from']}: {msg_packet['content'][:50]}...")
                
                # If it's a direct message, forward to other servers
                if message.get("to") and message["to"] != "all":
                    await self.broadcast_to_servers(msg_packet)
                    # Also check if recipient is on this server
                    await self.deliver_to_local_client(msg_packet)
                else:
                    # Broadcast to all
                    await self.broadcast_to_clients(msg_packet)
                    await self.broadcast_to_servers(msg_packet)
                    
            elif message["type"] == "list_users":
                # Request user list from all servers
                await self.broadcast_to_servers({
                    "type": "list_users_request",
                    "requester": client_info["id"],
                    "server": self.name
                })
                # Include local users
                await self.send_user_list(websocket)
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid message format"
            }))
    
    async def deliver_to_local_client(self, message):
        """Deliver message to a client on this server."""
        if message["to"] != "all":
            for ws, client_info in self.clients.items():
                if client_info["name"] == message["to"] or client_info["id"] == message["to"]:
                    await ws.send(json.dumps(message))
                    return True
        return False
    
    async def unregister_client(self, websocket):
        """Handle client disconnection."""
        if websocket in self.clients:
            client_info = self.clients[websocket]
            del self.clients[websocket]
            self.log_message(f"Client {client_info['id']} disconnected")
            
            # Notify other servers
            await self.broadcast_to_servers({
                "type": "client_disconnected",
                "client_id": client_info["id"],
                "server": self.name
            })
    
    async def connect_to_server(self, host: str, port: int):
        """Connect to another server."""
        if port == self.port or port in self.server_ports:
            return  # Don't connect to self or already connected servers
            
        try:
            uri = f"ws://{host}:{port}/server"
            websocket = await websockets.connect(uri)
            self.servers.add(websocket)
            self.server_ports.add(port)
            
            # Send identification
            await websocket.send(json.dumps({
                "type": "server_hello",
                "name": self.name,
                "port": self.port
            }))
            
            self.log_message(f"Connected to server at {host}:{port}")
            
            # Handle messages from other server
            asyncio.create_task(self.handle_server_messages(websocket, port))
            
        except Exception as e:
            self.log_message(f"Failed to connect to {host}:{port}: {e}")
    
    async def handle_server_messages(self, websocket, port):
        """Handle messages from other servers."""
        try:
            async for message in websocket:
                data = json.loads(message)
                
                if data["type"] == "server_hello":
                    self.log_message(f"Server {data['name']} connected")
                    
                elif data["type"] == "message":
                    # Try to deliver to local client
                    if data["to"] != "all":
                        delivered = await self.deliver_to_local_client(data)
                        if not delivered and data["server"] != self.name:
                            # Forward to other servers if not delivered locally
                            await self.broadcast_to_servers(data, exclude=websocket)
                    else:
                        # Broadcast message
                        await self.broadcast_to_clients(data)
                        if data["server"] != self.name:
                            await self.broadcast_to_servers(data, exclude=websocket)
                
                elif data["type"] == "list_users_request":
                    # Send our user list back
                    users = []
                    for client_info in self.clients.values():
                        users.append({
                            "id": client_info["id"],
                            "name": client_info["name"],
                            "server": self.name
                        })
                    
                    await websocket.send(json.dumps({
                        "type": "user_list",
                        "users": users,
                        "server": self.name
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            self.servers.remove(websocket)
            self.server_ports.discard(port)
            self.log_message(f"Server at port {port} disconnected")
    
    async def broadcast_to_clients(self, message):
        """Send message to all local clients."""
        if self.clients:
            await asyncio.gather(
                *[ws.send(json.dumps(message)) for ws in self.clients.keys()],
                return_exceptions=True
            )
    
    async def broadcast_to_servers(self, message, exclude=None):
        """Send message to all connected servers."""
        if self.servers:
            tasks = []
            for server in self.servers:
                if server != exclude:
                    tasks.append(server.send(json.dumps(message)))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_user_list(self, websocket):
        """Send list of users on this server to a client."""
        users = []
        for client_info in self.clients.values():
            users.append({
                "id": client_info["id"],
                "name": client_info["name"],
                "server": self.name
            })
        
        await websocket.send(json.dumps({
            "type": "user_list",
            "users": users,
            "server": self.name
        }))
    
    def log_message(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.messages.append(f"[{timestamp}] {message}")
        if len(self.messages) > 20:
            self.messages.pop(0)
    
    def create_status_panel(self) -> Panel:
        """Create server status panel."""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        table.add_row("Server Name", self.name)
        table.add_row("Port", str(self.port))
        table.add_row("Connected Clients", str(len(self.clients)))
        table.add_row("Connected Servers", str(len(self.servers)))
        table.add_row("Uptime", str(datetime.now() - self.start_time).split('.')[0])
        
        return Panel(table, title="Server Status", border_style="cyan")
    
    def create_clients_panel(self) -> Panel:
        """Create connected clients panel."""
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Connected", style="green")
        
        for client_info in self.clients.values():
            connected_time = datetime.now() - client_info["connected_at"]
            table.add_row(
                client_info["id"],
                client_info["name"] or "Not set",
                str(connected_time).split('.')[0]
            )
        
        return Panel(table, title="Connected Clients", border_style="yellow")
    
    def create_log_panel(self) -> Panel:
        """Create log panel."""
        log_text = "\n".join(self.messages[-15:]) if self.messages else "No messages yet"
        return Panel(
            log_text,
            title="Server Log",
            border_style="green",
            padding=(1, 2)
        )
    
    async def update_display(self):
        """Update the display continuously."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="log", size=20)
        )
        
        layout["header"].update(Panel(
            f"[bold cyan]WebSocket Server: {self.name}[/bold cyan]",
            style="white on blue"
        ))
        
        layout["main"].split_row(
            Layout(self.create_status_panel()),
            Layout(self.create_clients_panel())
        )
        
        layout["log"].update(self.create_log_panel())
        
        with Live(layout, console=console, screen=True, auto_refresh=False) as live:
            while True:
                layout["main"].split_row(
                    Layout(self.create_status_panel()),
                    Layout(self.create_clients_panel())
                )
                layout["log"].update(self.create_log_panel())
                live.update(layout, refresh=True)
                await asyncio.sleep(0.5)
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.log_message(f"Starting server {self.name} on port {self.port}")
        
        # Start display update task
        asyncio.create_task(self.update_display())
        
        # Start WebSocket server
        async with websockets.serve(self.register_client, "localhost", self.port):
            await asyncio.Future()  # Run forever

async def main():
    parser = argparse.ArgumentParser(description="WebSocket Chat Server")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--name", type=str, default="Server1", help="Server name")
    parser.add_argument("--connect", type=str, help="Connect to other servers (format: host:port,host:port)")
    
    args = parser.parse_args()
    
    server = ChatServer(args.port, args.name)
    
    # Connect to other servers if specified
    if args.connect:
        for server_addr in args.connect.split(","):
            host, port = server_addr.split(":")
            asyncio.create_task(server.connect_to_server(host, int(port)))
    
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())
