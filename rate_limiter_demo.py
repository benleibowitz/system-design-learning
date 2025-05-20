#!/usr/bin/env python3
"""
Rate Limiter Demonstrator with Live UI
An interactive tool to understand rate limiting with both leaky bucket and token bucket algorithms
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict
from queue import Queue
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.layout import Layout
import inquirer

console = Console()

class LeakyBucket:
    """Leaky bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.bucket = Queue(maxsize=capacity)
        self.last_leak_time = time.time()
        self.dropped_count = 0
        self.processed_count = 0
        self.total_requests = 0
        self.request_history = []
        self.drop_history = []
        self.running = True
        self._lock = threading.Lock()
        
        # Start the leak thread
        self.leak_thread = threading.Thread(target=self._leak_worker, daemon=True)
        self.leak_thread.start()
        
    def add_request(self, request_id: str = None) -> bool:
        """Try to add a request to the bucket"""
        with self._lock:
            self.total_requests += 1
            current_time = datetime.now()
            
            if request_id is None:
                request_id = f"req_{self.total_requests}"
                
            request_info = {
                'id': request_id,
                'timestamp': current_time,
                'size': self.bucket.qsize()
            }
            
            try:
                self.bucket.put(request_info, block=False)
                self.request_history.append(request_info)
                
                # Keep only recent history
                if len(self.request_history) > 10:
                    self.request_history.pop(0)
                    
                return True
            except:
                # Bucket is full, drop the request
                self.dropped_count += 1
                drop_info = {
                    'id': request_id,
                    'timestamp': current_time,
                    'reason': 'Bucket full'
                }
                self.drop_history.append(drop_info)
                
                # Keep only recent drop history
                if len(self.drop_history) > 10:
                    self.drop_history.pop(0)
                    
                return False
    
    def _leak_worker(self):
        """Background thread that processes requests at the configured rate"""
        while self.running:
            current_time = time.time()
            time_since_last_leak = current_time - self.last_leak_time
            
            # Calculate how many requests we should process
            requests_to_process = int(time_since_last_leak * self.leak_rate)
            
            if requests_to_process > 0:
                for _ in range(requests_to_process):
                    try:
                        request = self.bucket.get(block=False)
                        with self._lock:
                            self.processed_count += 1
                        self.bucket.task_done()
                    except:
                        break
                        
                self.last_leak_time = current_time
            
            time.sleep(0.1)
    
    def process_manual_request(self) -> bool:
        """Manually process one request from the bucket"""
        try:
            request = self.bucket.get(block=False)
            with self._lock:
                self.processed_count += 1
            self.bucket.task_done()
            return True
        except:
            return False
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self._lock:
            return {
                'current_size': self.bucket.qsize(),
                'capacity': self.capacity,
                'rate': self.leak_rate,
                'total_requests': self.total_requests,
                'processed_count': self.processed_count,
                'dropped_count': self.dropped_count,
                'drop_rate': (self.dropped_count / max(1, self.total_requests)) * 100,
                'algorithm': 'Leaky Bucket'
            }
    
    def reconfigure(self, capacity: int = None, rate: float = None):
        """Reconfigure the bucket parameters"""
        if capacity is not None:
            old_bucket = self.bucket
            self.capacity = capacity
            self.bucket = Queue(maxsize=capacity)
            
            # Transfer existing requests if they fit
            transferred = 0
            while not old_bucket.empty() and transferred < capacity:
                try:
                    request = old_bucket.get(block=False)
                    self.bucket.put(request, block=False)
                    transferred += 1
                except:
                    break
                    
        if rate is not None:
            self.leak_rate = rate
            
    def clear_bucket(self):
        """Clear all requests from the bucket"""
        while not self.bucket.empty():
            try:
                self.bucket.get(block=False)
            except:
                break
                
    def stop(self):
        """Stop the leaky bucket"""
        self.running = False


class TokenBucket:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity  # Start with a full bucket
        self.last_refill_time = time.time()
        self.dropped_count = 0
        self.processed_count = 0
        self.total_requests = 0
        self.request_history = []
        self.drop_history = []
        self.running = True
        self._lock = threading.Lock()
        
        # Start the refill thread
        self.refill_thread = threading.Thread(target=self._refill_worker, daemon=True)
        self.refill_thread.start()
        
    def add_request(self, request_id: str = None, tokens_needed: int = 1) -> bool:
        """Try to consume tokens for a request"""
        with self._lock:
            self.total_requests += 1
            current_time = datetime.now()
            
            if request_id is None:
                request_id = f"req_{self.total_requests}"
                
            # Check if we have enough tokens
            if self.tokens >= tokens_needed:
                # Consume tokens and process immediately
                self.tokens -= tokens_needed
                self.processed_count += 1
                
                request_info = {
                    'id': request_id,
                    'timestamp': current_time,
                    'tokens_consumed': tokens_needed,
                    'tokens_remaining': self.tokens
                }
                self.request_history.append(request_info)
                
                # Keep only recent history
                if len(self.request_history) > 10:
                    self.request_history.pop(0)
                    
                return True
            else:
                # Not enough tokens, drop the request
                self.dropped_count += 1
                drop_info = {
                    'id': request_id,
                    'timestamp': current_time,
                    'reason': f'Insufficient tokens (need {tokens_needed}, have {self.tokens})'
                }
                self.drop_history.append(drop_info)
                
                # Keep only recent drop history
                if len(self.drop_history) > 10:
                    self.drop_history.pop(0)
                    
                return False
    
    def _refill_worker(self):
        """Background thread that refills tokens at the configured rate"""
        while self.running:
            current_time = time.time()
            time_since_last_refill = current_time - self.last_refill_time
            
            # Calculate how many tokens to add
            tokens_to_add = time_since_last_refill * self.refill_rate
            
            if tokens_to_add >= 1:
                with self._lock:
                    # Add tokens but don't exceed capacity
                    self.tokens = min(self.capacity, self.tokens + int(tokens_to_add))
                self.last_refill_time = current_time
            
            time.sleep(0.1)
    
    def process_manual_request(self) -> bool:
        """Manually consume one token (for demonstration purposes)"""
        with self._lock:
            if self.tokens > 0:
                self.tokens -= 1
                return True
            return False
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        with self._lock:
            return {
                'current_size': self.tokens,
                'capacity': self.capacity,
                'rate': self.refill_rate,
                'total_requests': self.total_requests,
                'processed_count': self.processed_count,
                'dropped_count': self.dropped_count,
                'drop_rate': (self.dropped_count / max(1, self.total_requests)) * 100,
                'algorithm': 'Token Bucket'
            }
    
    def reconfigure(self, capacity: int = None, rate: float = None):
        """Reconfigure the bucket parameters"""
        with self._lock:
            if capacity is not None:
                self.capacity = capacity
                # Adjust current tokens if capacity changed
                self.tokens = min(self.tokens, capacity)
                
            if rate is not None:
                self.refill_rate = rate
    
    def clear_bucket(self):
        """Reset tokens to full capacity"""
        with self._lock:
            self.tokens = self.capacity
                
    def stop(self):
        """Stop the token bucket"""
        self.running = False


class RateLimiterDemo:
    """Interactive demo for both Leaky Bucket and Token Bucket Rate Limiters"""
    
    def __init__(self):
        self.algorithm = "leaky"  # or "token"
        self.bucket_capacity = 10
        self.rate = 2.0
        self.limiter = None
        self.create_limiter()
        self.last_action = ""
        self.action_timestamp = time.time()
        
    def create_limiter(self):
        """Initialize the rate limiter with current settings"""
        if self.limiter:
            self.limiter.stop()
            
        if self.algorithm == "leaky":
            self.limiter = LeakyBucket(self.bucket_capacity, self.rate)
        else:
            self.limiter = TokenBucket(self.bucket_capacity, self.rate)
        
    def draw_live_view(self) -> Layout:
        """Draw the live view with bucket visualization and controls"""
        if not self.limiter:
            return Layout(Panel("Bucket not initialized"))
            
        stats = self.limiter.get_stats()
        current_size = stats['current_size']
        capacity = stats['capacity']
        algorithm = stats['algorithm']
        
        # Create bucket visualization
        bucket_height = 8
        bucket_width = 14
        
        if self.algorithm == "leaky":
            # Leaky bucket: show water level
            fill_level = int((current_size / capacity) * bucket_height) if capacity > 0 else 0
            
            bucket_lines = []
            bucket_lines.append("┌" + "─" * bucket_width + "┐")
            
            for i in range(bucket_height):
                level = bucket_height - i - 1
                if level < fill_level:
                    bucket_lines.append("│" + "█" * bucket_width + "│")
                else:
                    bucket_lines.append("│" + " " * bucket_width + "│")
                    
            bucket_lines.append("└" + "─" * bucket_width + "┘")
            leak_arrows = "  " + "↓ " * (bucket_width // 3)
            bucket_lines.append(leak_arrows)
            bucket_lines.append(f"  Leak: {self.rate} req/s")
            
            bucket_visual = "\n".join(bucket_lines)
            fill_info = f"Queue: {current_size}/{capacity}"
            
        else:
            # Token bucket: show token level
            fill_level = int((current_size / capacity) * bucket_height) if capacity > 0 else 0
            
            bucket_lines = []
            bucket_lines.append("┌" + "─" * bucket_width + "┐")
            
            for i in range(bucket_height):
                level = bucket_height - i - 1
                if level < fill_level:
                    bucket_lines.append("│" + "○" * bucket_width + "│")
                else:
                    bucket_lines.append("│" + " " * bucket_width + "│")
                    
            bucket_lines.append("└" + "─" * bucket_width + "┘")
            refill_arrows = "  " + "↑ " * (bucket_width // 3)
            bucket_lines.append(refill_arrows)
            bucket_lines.append(f"  Refill: {self.rate} tok/s")
            
            bucket_visual = "\n".join(bucket_lines)
            fill_info = f"Tokens: {current_size}/{capacity}"
        
        # Calculate fill percentage
        fill_percentage = (current_size / capacity) * 100 if capacity > 0 else 0
        
        # Create bucket panel
        bucket_panel = Panel(
            f"{bucket_visual}\n\n[bold]{fill_info} ({fill_percentage:.0f}%)[/bold]",
            title=f"[bold cyan]{algorithm}[/bold cyan]",
            border_style="cyan"
        )
        
        # Create stats panel
        rate_label = "Leak Rate" if self.algorithm == "leaky" else "Refill Rate"
        
        stats_content = f"""[bold cyan]Statistics[/bold cyan]

Total Requests: {stats['total_requests']}
Processed: {stats['processed_count']}
Dropped: {stats['dropped_count']} ({stats['drop_rate']:.1f}%)
Current: {current_size}

[bold cyan]Configuration[/bold cyan]
Algorithm: {algorithm}
Capacity: {capacity} {'requests' if self.algorithm == 'leaky' else 'tokens'}
{rate_label}: {self.rate} {'req/s' if self.algorithm == 'leaky' else 'tok/s'}"""
        
        stats_panel = Panel(stats_content, title="Stats", border_style="green")
        
        # Create activity panel
        activity_content = "[bold cyan]Recent Activity[/bold cyan]\n\n"
        
        # Show last action with timestamp
        if self.last_action:
            time_since = time.time() - self.action_timestamp
            if time_since < 3:  # Show for 3 seconds
                activity_content += f"[yellow]Last Action:[/yellow] {self.last_action}\n\n"
        
        if self.limiter.request_history:
            activity_content += "[green]Recent Requests:[/green]\n"
            for req in self.limiter.request_history[-4:]:
                timestamp = req['timestamp'].strftime("%H:%M:%S")
                if self.algorithm == "token":
                    activity_content += f"  {timestamp} - {req['id']} (used {req.get('tokens_consumed', 1)} tok)\n"
                else:
                    activity_content += f"  {timestamp} - {req['id']}\n"
        else:
            activity_content += "[green]Recent Requests:[/green] None\n"
        
        activity_content += "\n"
        
        if self.limiter.drop_history:
            activity_content += "[red]Recent Drops:[/red]\n"
            for drop in self.limiter.drop_history[-4:]:
                timestamp = drop['timestamp'].strftime("%H:%M:%S")
                activity_content += f"  {timestamp} - {drop['id']}\n"
        else:
            activity_content += "[red]Recent Drops:[/red] None"
            
        activity_panel = Panel(activity_content, title="Activity", border_style="yellow")
        
        # Create controls panel
        algorithm_switch = "'s' - Switch algorithm"
        manual_action = "'p' - Process 1 manually" if self.algorithm == "leaky" else "'p' - Consume 1 token"
        
        controls_content = f"""[bold cyan]Live Controls[/bold cyan]

[bold green]'a'[/bold green] - Add 1 request
[bold green]'5'[/bold green] - Add 5 request burst
[bold green]'0'[/bold green] - Add 10 request burst
[bold blue]'t'[/bold blue] - Add expensive request (3 tokens)
[bold blue]{manual_action.split(' - ')[0]}[/bold blue] - {manual_action.split(' - ')[1]}
[bold yellow]'c'[/bold yellow] - Configure limiter
[bold yellow]'s'[/bold yellow] - Switch algorithm
[bold yellow]'r'[/bold yellow] - Reset statistics
[bold red]'q'[/bold red] - Exit demo

[dim]Tip: Try both algorithms with bursts to see the difference![/dim]"""
        
        controls_panel = Panel(controls_content, title="Controls", border_style="blue")
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(
                Panel(
                    Align.center(f"[bold cyan]Rate Limiter Demo - {algorithm}[/bold cyan] - Total: {stats['total_requests']} | Processed: {stats['processed_count']} | Dropped: {stats['dropped_count']}"),
                    border_style="magenta"
                ), 
                size=3
            ),
            Layout(name="main", ratio=1)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=1)
        )
        
        layout["left"].split_column(
            Layout(bucket_panel, ratio=2),
            Layout(controls_panel, ratio=1)
        )
        
        layout["right"].split_column(
            Layout(stats_panel, ratio=1),
            Layout(activity_panel, ratio=1)
        )
        
        return layout
    
    def set_last_action(self, action: str):
        """Set the last action performed"""
        self.last_action = action
        self.action_timestamp = time.time()
        
    def show_help(self):
        """Show help"""
        help_text = """
[bold cyan]Rate Limiting Algorithms[/bold cyan]

[bold green]Leaky Bucket:[/bold green]
• Stores requests in a fixed-size queue
• Processes them at a constant rate (leak)
• Smooths out request bursts
• Drops excess requests when queue is full

[bold blue]Token Bucket:[/bold blue]
• Maintains a bucket of tokens
• Each request consumes tokens
• Tokens refill at a constant rate
• Allows bursts up to bucket capacity

[bold cyan]Key Differences:[/bold cyan]
• [green]Leaky Bucket[/green]: Enforces a steady output rate
• [blue]Token Bucket[/blue]: Allows bursts, then rate-limits

[bold cyan]Experiment:[/bold cyan]
• Try bursts in both algorithms
• Notice how token bucket allows immediate processing
• See how leaky bucket queues requests

[bold cyan]Real-world Uses:[/bold cyan]
• API rate limiting
• Network traffic shaping
• Cloud resource management
• Load balancing
        """
        
        console.print(Panel(help_text, title="Help", border_style="cyan"))
        input("\nPress Enter to return to live view...")
        
    def configure_limiter(self):
        """Configure the limiter parameters"""
        questions = [
            inquirer.List('algorithm',
                        message="Algorithm:",
                        choices=['Leaky Bucket', 'Token Bucket'],
                        default='Leaky Bucket' if self.algorithm == 'leaky' else 'Token Bucket'),
            inquirer.Text('capacity',
                        message="Capacity:",
                        default=str(self.bucket_capacity),
                        validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 30),
            inquirer.Text('rate',
                        message="Rate (per second):",
                        default=str(self.rate),
                        validate=lambda _, x: self._validate_float(x) and 0.1 <= float(x) <= 10.0)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return
            
        new_algorithm = "leaky" if answers['algorithm'] == 'Leaky Bucket' else "token"
        self.bucket_capacity = int(answers['capacity'])
        self.rate = float(answers['rate'])
        
        # If algorithm changed, create new limiter
        if new_algorithm != self.algorithm:
            self.algorithm = new_algorithm
            self.create_limiter()
            self.set_last_action(f"Switched to {answers['algorithm']}")
        else:
            # Just reconfigure existing limiter
            self.limiter.reconfigure(capacity=self.bucket_capacity, rate=self.rate)
            self.set_last_action(f"Configured: cap={self.bucket_capacity}, rate={self.rate}")
        
    def switch_algorithm(self):
        """Switch between leaky bucket and token bucket"""
        self.algorithm = "token" if self.algorithm == "leaky" else "leaky"
        self.create_limiter()
        algorithm_name = "Token Bucket" if self.algorithm == "token" else "Leaky Bucket"
        self.set_last_action(f"Switched to {algorithm_name}")
        
    def _validate_float(self, value: str) -> bool:
        """Validate if string can be converted to float"""
        try:
            float(value)
            return True
        except ValueError:
            return False
            
    def reset_statistics(self):
        """Reset all statistics"""
        self.limiter.total_requests = 0
        self.limiter.processed_count = 0
        self.limiter.dropped_count = 0
        self.limiter.request_history = []
        self.limiter.drop_history = []
        self.set_last_action("Statistics reset")
        
    def run_live_demo(self):
        """Run the live demonstration with keyboard input"""
        console.print(Panel.fit(
            "[bold cyan]Rate Limiter Live Demo[/bold cyan]\n"
            "Watch both algorithms in real-time as you interact with them!",
            border_style="cyan"
        ))
        
        time.sleep(1)
        
        # Try to set up non-blocking input
        try:
            import termios
            import tty
            import select
            
            # Check if we have a TTY
            if not sys.stdin.isatty():
                raise OSError("Not a TTY")
            
            # Save terminal settings
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            # Set terminal to cbreak mode
            try:
                tty.setcbreak(fd)
            except AttributeError:
                # Fallback if setcbreak doesn't exist
                tty.cbreak(fd)
            
            try:
                with Live(self.draw_live_view(), refresh_per_second=5) as live:
                    while True:
                        # Update display
                        live.update(self.draw_live_view())
                        
                        # Check for input (non-blocking)
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            char = sys.stdin.read(1).lower()
                            
                            if char == 'q':
                                break
                            elif char == 'a':
                                # Add one request
                                added = self.limiter.add_request()
                                if added:
                                    self.set_last_action("✓ Added 1 request")
                                else:
                                    reason = "bucket full" if self.algorithm == "leaky" else "insufficient tokens"
                                    self.set_last_action(f"✗ Request dropped ({reason})")
                            elif char == '5':
                                # Add 5 requests
                                added = 0
                                for i in range(5):
                                    if self.limiter.add_request(f"burst5_{i+1}"):
                                        added += 1
                                self.set_last_action(f"Burst 5: {added} added, {5-added} dropped")
                            elif char == '0':
                                # Add 10 requests
                                added = 0
                                for i in range(10):
                                    if self.limiter.add_request(f"burst10_{i+1}"):
                                        added += 1
                                self.set_last_action(f"Burst 10: {added} added, {10-added} dropped")
                            elif char == 't':
                                # Add expensive request (3 tokens for token bucket)
                                if self.algorithm == "token":
                                    added = self.limiter.add_request("expensive_req", tokens_needed=3)
                                    if added:
                                        self.set_last_action("✓ Added expensive request (3 tokens)")
                                    else:
                                        self.set_last_action("✗ Expensive request dropped")
                                else:
                                    # For leaky bucket, just add a regular request
                                    added = self.limiter.add_request("expensive_req")
                                    if added:
                                        self.set_last_action("✓ Added request")
                                    else:
                                        self.set_last_action("✗ Request dropped (bucket full)")
                            elif char == 'p':
                                # Process manually
                                if self.limiter.process_manual_request():
                                    action = "Processed 1 request manually" if self.algorithm == "leaky" else "Consumed 1 token manually"
                                    self.set_last_action(f"✓ {action}")
                                else:
                                    reason = "No requests to process" if self.algorithm == "leaky" else "No tokens available"
                                    self.set_last_action(reason)
                            elif char == 'c':
                                # Configure
                                live.stop()
                                self.configure_limiter()
                                live.start()
                            elif char == 's':
                                # Switch algorithm
                                self.switch_algorithm()
                            elif char == 'r':
                                # Reset
                                self.reset_statistics()
                            elif char == 'h':
                                # Help
                                live.stop()
                                self.show_help()
                                live.start()
            finally:
                # Restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except (ImportError, AttributeError, OSError) as e:
            # Fallback for systems without proper terminal support
            console.print(f"[yellow]Live keyboard input not available: {type(e).__name__}[/yellow]")
            console.print("[yellow]Using menu-based interface instead...[/yellow]")
            time.sleep(2)
            self.run_menu_demo()
            
    def run_menu_demo(self):
        """Fallback menu-based demo for systems without live input"""
        while True:
            console.clear()
            console.print(self.draw_live_view())
            
            choices = [
                "Add 1 Request",
                "Add 5 Requests",
                "Add 10 Requests", 
                "Add Expensive Request (3 tokens)" if self.algorithm == "token" else "Add Request",
                "Process 1 Manually" if self.algorithm == "leaky" else "Consume 1 Token",
                "Configure",
                "Switch Algorithm",
                "Reset Stats",
                "Help",
                "Exit"
            ]
            
            questions = [
                inquirer.List('action',
                            message="Action:",
                            choices=choices)
            ]
            
            answers = inquirer.prompt(questions)
            if not answers:
                break
                
            action = answers['action']
            
            if action == "Add 1 Request":
                added = self.limiter.add_request()
                status = "✓ Added" if added else "✗ Dropped"
                self.set_last_action(status)
                
            elif action == "Add 5 Requests":
                added = sum(1 for i in range(5) if self.limiter.add_request(f"burst5_{i+1}"))
                self.set_last_action(f"Burst 5: {added} added, {5-added} dropped")
                
            elif action == "Add 10 Requests":
                added = sum(1 for i in range(10) if self.limiter.add_request(f"burst10_{i+1}"))
                self.set_last_action(f"Burst 10: {added} added, {10-added} dropped")
                
            elif "Expensive Request" in action:
                if self.algorithm == "token":
                    added = self.limiter.add_request("expensive_req", tokens_needed=3)
                    status = "✓ Added expensive request (3 tokens)" if added else "✗ Expensive request dropped"
                else:
                    added = self.limiter.add_request("expensive_req")
                    status = "✓ Added request" if added else "✗ Request dropped"
                self.set_last_action(status)
                
            elif action.startswith("Process") or action.startswith("Consume"):
                if self.limiter.process_manual_request():
                    action_name = "Processed 1 request manually" if self.algorithm == "leaky" else "Consumed 1 token manually"
                    self.set_last_action(f"✓ {action_name}")
                else:
                    reason = "No requests to process" if self.algorithm == "leaky" else "No tokens available"
                    self.set_last_action(reason)
                    
            elif action == "Configure":
                self.configure_limiter()
                
            elif action == "Switch Algorithm":
                self.switch_algorithm()
                
            elif action == "Reset Stats":
                self.reset_statistics()
                
            elif action == "Help":
                self.show_help()
                
            elif action == "Exit":
                break

def main():
    """Main entry point"""
    try:
        demo = RateLimiterDemo()
        demo.run_live_demo()
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[green]Thanks for exploring rate limiting![/green]")

if __name__ == "__main__":
    main()
