#!/usr/bin/env python3
"""
Clock Simulator - Interactive demonstration of Lamport and Vector clocks
"""

import inquirer
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
import sys
import os

class LamportClock:
    def __init__(self):
        self.time = 0
    
    def increment(self):
        """Increment clock for internal event"""
        self.time += 1
    
    def send(self):
        """Get timestamp for sending message"""
        self.increment()
        return self.time
    
    def receive(self, received_time):
        """Update clock when receiving message"""
        self.time = max(self.time, received_time) + 1
    
    def __str__(self):
        return str(self.time)

class VectorClock:
    def __init__(self, num_processes, process_id):
        self.clock = [0] * num_processes
        self.process_id = process_id
    
    def increment(self):
        """Increment clock for internal event"""
        self.clock[self.process_id] += 1
    
    def send(self):
        """Get timestamp for sending message"""
        self.increment()
        return self.clock.copy()
    
    def receive(self, received_clock):
        """Update clock when receiving message"""
        for i in range(len(self.clock)):
            self.clock[i] = max(self.clock[i], received_clock[i])
        self.clock[self.process_id] += 1
    
    def __str__(self):
        return str(self.clock)

class Process:
    def __init__(self, process_id, clock_type, num_processes):
        self.id = process_id
        self.name = f"P{process_id}"
        if clock_type == "Lamport":
            self.clock = LamportClock()
        else:
            self.clock = VectorClock(num_processes, process_id)
        self.events = []
        
    def local_event(self):
        """Process a local event"""
        self.clock.increment()
        self.events.append(("local", str(self.clock)))
    
    def send_message(self, target_process):
        """Send a message to another process"""
        timestamp = self.clock.send()
        self.events.append(("send", str(self.clock), target_process.id))
        return timestamp
    
    def receive_message(self, timestamp, sender_id):
        """Receive a message from another process"""
        self.clock.receive(timestamp)
        self.events.append(("receive", str(self.clock), sender_id))

class ClockSimulator:
    def __init__(self):
        self.processes = []
        self.messages = []  # (sender_id, receiver_id, send_event_idx, receive_event_idx)
        self.round = 0
        self.save_plots = False
        
    def setup(self):
        """Initialize the simulation with user preferences"""
        questions = [
            inquirer.List('clock_type',
                         message="Select clock type",
                         choices=['Lamport', 'Vector']),
            inquirer.List('num_processes',
                         message="Number of processes",
                         choices=[2, 3, 4, 5]),
            inquirer.Confirm('save_plots',
                           message="Save plots to files?",
                           default=True)
        ]
        answers = inquirer.prompt(questions)
        
        self.clock_type = answers['clock_type']
        self.num_processes = answers['num_processes']
        self.save_plots = answers['save_plots']
        
        # Create processes
        for i in range(self.num_processes):
            self.processes.append(Process(i, self.clock_type, self.num_processes))
    
    def draw_state(self):
        """Draw the current state of all processes"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Draw timeline for each process
        y_positions = np.linspace(0.8, 0.2, self.num_processes)
        
        for i, process in enumerate(self.processes):
            y = y_positions[i]
            
            # Process label
            ax.text(-0.1, y, process.name, fontsize=12, ha='right', va='center')
            
            # Timeline
            ax.plot([0, 1], [y, y], 'k-', linewidth=1)
            
            # Events
            if process.events:
                x_positions = np.linspace(0.1, 0.9, len(process.events))
                for j, event in enumerate(process.events):
                    x = x_positions[j]
                    
                    # Draw event marker
                    marker = 'o' if event[0] == 'local' else ('>' if event[0] == 'send' else '<')
                    color = 'blue' if event[0] == 'local' else ('green' if event[0] == 'send' else 'red')
                    ax.plot(x, y, marker, color=color, markersize=10)
                    
                    # Draw clock value
                    ax.text(x, y - 0.05, event[1], fontsize=8, ha='center')
        
        # Draw messages
        for msg in self.messages:
            sender_id, receiver_id, send_idx, receive_idx = msg
            sender_y = y_positions[sender_id]
            receiver_y = y_positions[receiver_id]
            
            send_x = np.linspace(0.1, 0.9, len(self.processes[sender_id].events))[send_idx]
            receive_x = np.linspace(0.1, 0.9, len(self.processes[receiver_id].events))[receive_idx]
            
            # Draw arrow for message
            ax.annotate('', xy=(receive_x, receiver_y), xytext=(send_x, sender_y),
                       arrowprops=dict(arrowstyle='->', color='purple', lw=1.5))
        
        # Legend
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markersize=10, label='Local event'),
            Line2D([0], [0], marker='>', color='w', markerfacecolor='green', markersize=10, label='Send message'),
            Line2D([0], [0], marker='<', color='w', markerfacecolor='red', markersize=10, label='Receive message'),
            Line2D([0], [0], color='purple', linewidth=2, label='Message')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        ax.set_xlim(-0.2, 1.1)
        ax.set_ylim(0, 1)
        ax.set_title(f'{self.clock_type} Clock Simulation - Round {self.round}', fontsize=16)
        ax.axis('off')
        
        if self.save_plots:
            filename = f'clock_simulation_{self.clock_type.lower()}_round_{self.round}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"Saved plot to {filename}")
        
        plt.show(block=False)
        plt.pause(2)  # Show for 2 seconds
        plt.close()
    
    def run_round(self):
        """Run one round of the simulation"""
        self.round += 1
        
        # Choose action
        action_question = [
            inquirer.List('action',
                         message="Choose action",
                         choices=['Send message', 'Local event', 'Exit'])
        ]
        action = inquirer.prompt(action_question)['action']
        
        if action == 'Exit':
            return False
        
        if action == 'Local event':
            # Choose process for local event
            process_choices = [f"{p.name} (clock: {p.clock})" for p in self.processes]
            local_question = [
                inquirer.List('process',
                             message="Select process for local event",
                             choices=process_choices)
            ]
            selected = inquirer.prompt(local_question)['process']
            process_idx = int(selected.split()[0][1])  # Extract process number
            
            self.processes[process_idx].local_event()
            print(f"\n{self.processes[process_idx].name} performed local event")
            print(f"New clock value: {self.processes[process_idx].clock}\n")
            
        else:  # Send message
            # Choose sender
            sender_choices = [f"{p.name} (clock: {p.clock})" for p in self.processes]
            sender_question = [
                inquirer.List('sender',
                             message="Select sender process",
                             choices=sender_choices)
            ]
            sender_selected = inquirer.prompt(sender_question)['sender']
            sender_idx = int(sender_selected.split()[0][1])
            
            # Choose receiver
            receiver_choices = [f"{p.name} (clock: {p.clock})" 
                              for i, p in enumerate(self.processes) if i != sender_idx]
            receiver_question = [
                inquirer.List('receiver',
                             message="Select receiver process",
                             choices=receiver_choices)
            ]
            receiver_selected = inquirer.prompt(receiver_question)['receiver']
            receiver_idx = int(receiver_selected.split()[0][1])
            
            # Send message
            sender = self.processes[sender_idx]
            receiver = self.processes[receiver_idx]
            
            timestamp = sender.send_message(receiver)
            send_event_idx = len(sender.events) - 1
            
            receiver.receive_message(timestamp, sender_idx)
            receive_event_idx = len(receiver.events) - 1
            
            self.messages.append((sender_idx, receiver_idx, send_event_idx, receive_event_idx))
            
            print(f"\n{sender.name} sent message to {receiver.name}")
            print(f"Sender clock after send: {sender.clock}")
            print(f"Receiver clock after receive: {receiver.clock}\n")
        
        return True
    
    def run(self):
        """Main simulation loop"""
        print("\n=== Clock Simulator ===")
        print("This tool demonstrates Lamport and Vector clocks")
        print("Each round, you can either:")
        print("  - Trigger a local event on a process")
        print("  - Send a message between processes")
        print("The visualization will show the clock values and message flow\n")
        
        self.setup()
        print(f"\nStarting {self.clock_type} clock simulation with {self.num_processes} processes")
        
        # Initial state
        self.draw_state()
        
        while True:
            if not self.run_round():
                break
            self.draw_state()
        
        print("\nSimulation complete!")
        if self.save_plots:
            print(f"All plots saved as clock_simulation_{self.clock_type.lower()}_round_*.png")

if __name__ == "__main__":
    simulator = ClockSimulator()
    simulator.run()
