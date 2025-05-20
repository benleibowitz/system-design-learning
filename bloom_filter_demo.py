#!/usr/bin/env python3
"""
Bloom Filter Demonstrator with Beautiful UI (Compact Version)
An interactive tool to understand how bloom filters work
"""

import os
import sys
import math
import hashlib
import time
import random
from typing import List, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, BarColumn
from rich.live import Live
import inquirer

console = Console()

class BloomFilter:
    """Bloom filter implementation with configurable hash functions"""
    
    def __init__(self, size: int, hash_functions: List[Callable]):
        self.size = size
        self.bit_array = [0] * size
        self.hash_functions = hash_functions
        self.items_count = 0
        self.insert_history = []  # Track items added
        self.check_history = []   # Track items checked
        
    def insert(self, item: str) -> List[int]:
        """Insert an item into the bloom filter"""
        positions = []
        self.items_count += 1
        
        for hash_function in self.hash_functions:
            position = hash_function(item) % self.size
            self.bit_array[position] = 1
            positions.append(position)
            
        # Track history of inserts
        self.insert_history.append({
            'item': item,
            'positions': positions.copy()
        })
            
        return positions
        
    def check(self, item: str) -> dict:
        """Check if an item might be in the set"""
        positions = []
        is_present = True
        
        for hash_function in self.hash_functions:
            position = hash_function(item) % self.size
            positions.append(position)
            if self.bit_array[position] == 0:
                is_present = False
                
        # Track history of checks
        self.check_history.append({
            'item': item,
            'positions': positions.copy(),
            'result': is_present
        })
                
        return {
            'is_present': is_present,
            'positions': positions
        }
        
    def clear(self):
        """Reset the bloom filter"""
        self.bit_array = [0] * self.size
        self.items_count = 0
        self.insert_history = []
        self.check_history = []
        
    def get_false_positive_probability(self) -> float:
        """Calculate the current false positive probability"""
        k = len(self.hash_functions)
        n = self.items_count
        m = self.size
        
        if n == 0:
            return 0.0
            
        return (1 - math.exp(-k * n / m)) ** k
        
    @staticmethod
    def get_optimal_hash_count(size: int, expected_items: int) -> int:
        """Calculate the optimal number of hash functions"""
        m = size
        n = expected_items
        
        if n == 0:
            return 1
            
        return max(1, int(round((m / n) * math.log(2))))

def create_hash_functions(count: int) -> List[Callable]:
    """Create specified number of hash functions using different algorithms"""
    hash_algorithms = [
        hashlib.md5,
        hashlib.sha1,
        hashlib.sha256,
        hashlib.sha512,
        hashlib.sha3_256,
        hashlib.blake2b,
        hashlib.blake2s
    ]
    
    hash_functions = []
    
    for i in range(count):
        algorithm = hash_algorithms[i % len(hash_algorithms)]
        salt = str(i).encode()
        
        def hash_function(item: str, alg=algorithm, salt=salt) -> int:
            data = item.encode() + salt
            hash_value = alg(data).hexdigest()
            return int(hash_value, 16)
            
        hash_functions.append(hash_function)
        
    return hash_functions

class BloomFilterDemo:
    """Interactive demo for the Bloom Filter"""
    
    def __init__(self):
        self.bit_array_size = 40  # Default size
        self.hash_function_count = 3  # Default number of hash functions
        self.bloom_filter = None
        self.create_bloom_filter()
        
    def create_bloom_filter(self):
        """Initialize the bloom filter with current settings"""
        hash_functions = create_hash_functions(self.hash_function_count)
        self.bloom_filter = BloomFilter(self.bit_array_size, hash_functions)
        
    def draw_bit_array(self, highlight_positions: List[int] = None) -> Panel:
        """Draw the bit array visualization (compact)"""
        if not self.bloom_filter:
            return Panel("Bloom filter not initialized")
            
        # Create bit array representation
        array = self.bloom_filter.bit_array
        
        # Format the bits with colors
        formatted_bits = []
        for i, bit in enumerate(array):
            # Determine if this position should be highlighted
            is_highlighted = highlight_positions and i in highlight_positions
            
            if bit == 1:
                if is_highlighted:
                    formatted_bits.append(f"[bold white on red]{bit}[/bold white on red]")
                else:
                    formatted_bits.append(f"[bold white on green]{bit}[/bold white on green]")
            else:
                if is_highlighted:
                    formatted_bits.append(f"[bold black on yellow]{bit}[/bold black on yellow]")
                else:
                    formatted_bits.append(f"[dim]{bit}[/dim]")
        
        # Split into rows for better display
        rows_per_line = 2  # Reduce vertical space
        bits_per_row = self.bit_array_size // rows_per_line + (1 if self.bit_array_size % rows_per_line else 0)
        
        bit_rows = []
        for i in range(0, len(formatted_bits), bits_per_row):
            bit_rows.append(" ".join(formatted_bits[i:i+bits_per_row]))
            
        # Add compact position markers
        position_markers = []
        for i in range(0, len(array), bits_per_row):
            markers = []
            for j in range(0, bits_per_row, 5):  # Mark every 5th position
                if i + j < len(array):
                    markers.append(f"[dim]{i+j}[/dim]")
                else:
                    markers.append("")
            position_markers.append(" ".join(markers))
            
        # Combine everything in a compact format
        content = []
        for i, row in enumerate(bit_rows):
            if i < len(position_markers):
                content.append(f"{position_markers[i]}")
            content.append(row)
            
        # Create compact panel with the bit array
        prob = self.bloom_filter.get_false_positive_probability()
        
        return Panel(
            "\n".join(content),
            title="[bold]Bloom Filter Bit Array[/bold]",
            subtitle=f"Size: {self.bloom_filter.size} | Items: {self.bloom_filter.items_count} | FP Prob: {prob:.5f}",
            border_style="cyan"
        )
    
    def show_insert_animation(self, item: str, positions: List[int]):
        """Show animation when inserting an item (compact)"""
        console.print(f"Inserting: [bold cyan]{item}[/bold cyan]")
        
        with Live(self.draw_bit_array(), refresh_per_second=10) as live:
            for i in range(len(positions) + 1):
                if i > 0:
                    current_positions = positions[:i]
                    live.update(self.draw_bit_array(current_positions))
                time.sleep(0.3)
            
            # Final view
            time.sleep(0.3)
            
        console.print(f"[green]Inserted at positions: {positions}[/green]")
            
    def show_check_animation(self, item: str, result: dict):
        """Show animation when checking an item (compact)"""
        is_present = result['is_present']
        positions = result['positions']
        
        console.print(f"Checking: [bold cyan]{item}[/bold cyan]")
        
        with Live(self.draw_bit_array(), refresh_per_second=10) as live:
            for i in range(1, len(positions) + 1):
                current_positions = positions[:i]
                live.update(self.draw_bit_array(current_positions))
                time.sleep(0.3)
        
        # Final result as a single line
        if is_present:
            console.print(f"[bold green]May be in set![/bold green] (Positions: {positions})")
            console.print("[yellow]Note: This could be a false positive.[/yellow]")
        else:
            console.print(f"[bold red]Definitely not in set![/bold red] (Positions: {positions})")
            
    def show_history(self):
        """Show history of operations (compact)"""
        if not self.bloom_filter:
            console.print("[yellow]Bloom filter not initialized.[/yellow]")
            return
            
        # Create combined history table
        history_table = Table(title="Operation History")
        history_table.add_column("Operation", style="cyan", width=8)
        history_table.add_column("Item", style="green", width=15)
        history_table.add_column("Positions", style="yellow")
        history_table.add_column("Result", style="magenta", width=10)
        
        # Add inserts
        for entry in self.bloom_filter.insert_history:
            history_table.add_row(
                "INSERT",
                entry['item'],
                str(entry['positions']),
                ""
            )
            
        # Add checks
        for entry in self.bloom_filter.check_history:
            history_table.add_row(
                "CHECK",
                entry['item'],
                str(entry['positions']),
                "[green]Yes[/green]" if entry['result'] else "[red]No[/red]"
            )
            
        console.print(history_table)
        
    def show_statistics(self):
        """Show bloom filter statistics (compact)"""
        if not self.bloom_filter:
            console.print("[yellow]Bloom filter not initialized.[/yellow]")
            return
            
        bf = self.bloom_filter
        
        # Calculate filled cell percentage
        filled_cells = sum(bf.bit_array)
        fill_percentage = (filled_cells / bf.size) * 100
        
        # Create compact info table
        stats_table = Table(title="Bloom Filter Statistics", expand=False)
        stats_table.add_column("Property", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Bit Array Size", str(bf.size))
        stats_table.add_row("Hash Functions", str(len(bf.hash_functions)))
        stats_table.add_row("Items Inserted", str(bf.items_count))
        stats_table.add_row("Bits Set", f"{filled_cells}/{bf.size} ({fill_percentage:.1f}%)")
        stats_table.add_row("False Positive Prob", f"{bf.get_false_positive_probability():.6f}")
        
        # Add optimal configuration
        optimal_hashes = BloomFilter.get_optimal_hash_count(bf.size, bf.items_count)
        if optimal_hashes != len(bf.hash_functions):
            stats_table.add_row("Optimal Hash Count", f"{optimal_hashes} (current: {len(bf.hash_functions)})")
        
        console.print(stats_table)
        
    def show_explanation(self):
        """Show a compact explanation of how bloom filters work"""
        explanation = """
[bold cyan]What is a Bloom Filter?[/bold cyan]
A space-efficient probabilistic data structure for membership testing with possible false positives but no false negatives.

[bold cyan]Key Properties:[/bold cyan]
• [green]Space Efficient[/green] - Uses much less memory than storing actual elements
• [green]Fast Lookups[/green] - O(k) where k is the number of hash functions
• [green]No False Negatives[/green] - If it says an element is not in the set, it definitely isn't
• [yellow]Possible False Positives[/yellow] - May incorrectly report that an element is present
• [red]No Removal[/red] - Elements cannot be removed once added

[bold cyan]How It Works:[/bold cyan]
1. Start with a bit array of m bits (all set to 0)
2. Define k hash functions that map items to positions in the array
3. [bold]Insert:[/bold] Hash item with each function, set resulting positions to 1
4. [bold]Check:[/bold] Hash item with each function, check if all positions are 1
   - If any bit is 0: element is [bold red]definitely not[/bold red] in the set
   - If all bits are 1: element is [bold yellow]probably[/bold yellow] in the set

[bold cyan]Common Uses:[/bold cyan]
• Database query optimization
• Network routers for packet filtering
• Web browsers for safe browsing lists
• Spell checkers
• Cache optimization
        """
        
        console.print(Panel(explanation, title="Bloom Filter Explained", border_style="cyan", width=80))
        
    def run_simulation(self):
        """Run an automated simulation with random data (compact)"""
        # Ask for parameters
        sim_items = inquirer.prompt([
            inquirer.Text('count',
                        message="Number of items to insert:",
                        default="50",
                        validate=lambda _, x: x.isdigit() and 10 <= int(x) <= 1000)
        ])
        
        if not sim_items:
            return
            
        count = int(sim_items['count'])
        
        # Reset bloom filter
        self.bloom_filter.clear()
        
        # Generate random words for insertion
        words = []
        for i in range(count):
            # Create a random 4-letter word
            word = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
            words.append(word)
        
        # Perform insertions
        console.print(f"[cyan]Inserting {count} random items...[/cyan]")
        for word in words:
            self.bloom_filter.insert(word)
                
        console.print(f"[green]Inserted {count} random items[/green]")
        
        # Display bit array
        console.print(self.draw_bit_array())
        
        # Test with true positives and potential false positives
        console.print("\n[bold cyan]Testing accuracy:[/bold cyan]")
        
        # Test existing items (should all be found)
        true_positives = 0
        test_count = min(5, len(words))
        test_existing = random.sample(words, test_count)
        
        console.print("\n[bold]Testing items in the set:[/bold]")
        for word in test_existing:
            result = self.bloom_filter.check(word)
            if result['is_present']:
                true_positives += 1
            console.print(f"{word}: {'[green]✓[/green]' if result['is_present'] else '[red]✗[/red]'}")
        
        # Test non-existing items (some may report false positives)
        false_positives = 0
        non_existing = []
        for i in range(test_count):
            while True:
                word = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(4))
                if word not in words:
                    non_existing.append(word)
                    break
        
        console.print("\n[bold]Testing items NOT in the set:[/bold]")
        for word in non_existing:
            result = self.bloom_filter.check(word)
            if result['is_present']:
                false_positives += 1
            console.print(f"{word}: {'[yellow]✓ (false +)[/yellow]' if result['is_present'] else '[green]✗[/green]'}")
        
        # Show accuracy summary
        console.print(f"\n[bold]Results:[/bold]")
        console.print(f"True positives: {true_positives}/{test_count} (expected: 100%)")
        fp_percent = (false_positives/test_count) * 100
        console.print(f"False positives: {false_positives}/{test_count} ({fp_percent:.1f}%)")
        console.print(f"Theoretical FP probability: {self.bloom_filter.get_false_positive_probability():.4f}")
        
    def configure_filter(self):
        """Configure the bloom filter parameters"""
        questions = [
            inquirer.Text('size',
                        message="Bit array size:",
                        default=str(self.bit_array_size),
                        validate=lambda _, x: x.isdigit() and 10 <= int(x) <= 1000),
            inquirer.Text('hash_count',
                        message="Number of hash functions:",
                        default=str(self.hash_function_count),
                        validate=lambda _, x: x.isdigit() and 1 <= int(x) <= 10)
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return
            
        old_size = self.bit_array_size
        old_hash_count = self.hash_function_count
        
        self.bit_array_size = int(answers['size'])
        self.hash_function_count = int(answers['hash_count'])
        
        # Only recreate if parameters changed
        if old_size != self.bit_array_size or old_hash_count != self.hash_function_count:
            self.create_bloom_filter()
            console.print(f"[green]Reconfigured: size={self.bit_array_size}, hash_functions={self.hash_function_count}[/green]")
        
    def run_interactive_ui(self):
        """Run the interactive UI (compact version)"""
        # Display welcome banner
        console.print(Panel(
            "[bold cyan]Bloom Filter Demonstrator[/bold cyan] - Compact UI",
            border_style="cyan"
        ))
        
        while True:
            # Display the bit array visualization
            console.print(self.draw_bit_array())
            
            # Main menu options
            choices = [
                "Insert Item",
                "Check Item",
                "View History",
                "View Statistics",
                "Configure Filter",
                "Clear Filter",
                "Run Simulation",
                "How It Works",
                "Exit"
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
            
            if action == "Insert Item":
                item = inquirer.prompt([
                    inquirer.Text('item', message="Enter item to insert:")
                ])
                if item and item['item']:
                    positions = self.bloom_filter.insert(item['item'])
                    self.show_insert_animation(item['item'], positions)
                    
            elif action == "Check Item":
                item = inquirer.prompt([
                    inquirer.Text('item', message="Enter item to check:")
                ])
                if item and item['item']:
                    result = self.bloom_filter.check(item['item'])
                    self.show_check_animation(item['item'], result)
                    
            elif action == "View History":
                self.show_history()
                
            elif action == "View Statistics":
                self.show_statistics()
                
            elif action == "Configure Filter":
                self.configure_filter()
                
            elif action == "Clear Filter":
                if inquirer.confirm("Are you sure you want to clear the filter?", default=False):
                    self.bloom_filter.clear()
                    console.print("[green]Bloom filter cleared[/green]")
                    
            elif action == "Run Simulation":
                self.run_simulation()
                
            elif action == "How It Works":
                self.show_explanation()
                
            elif action == "Exit":
                break
                
            # Pause between actions
            console.print()
            input("Press Enter to continue...")
            console.clear()

def main():
    """Main entry point"""
    try:
        demo = BloomFilterDemo()
        demo.run_interactive_ui()
    except KeyboardInterrupt:
        console.print("\n[red]Demo closed[/red]")
    finally:
        console.print("[green]Thanks for exploring Bloom Filters![/green]")

if __name__ == "__main__":
    main()
