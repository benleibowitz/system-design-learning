#!/usr/bin/env python3
"""
Tic Tac Toe - Single Player Game Against Computer
Arrow Key Navigation Version
"""

import random
import os
import time
import sys
import tty
import termios
import select

# ANSI color codes for beautiful terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Game colors
    PLAYER_X = '\033[94m'  # Blue
    PLAYER_O = '\033[91m'  # Red
    BOARD = '\033[93m'     # Yellow
    WIN = '\033[92m'       # Green
    HEADER = '\033[95m'    # Magenta
    CURSOR = '\033[46m'    # Cyan background
    ERROR = '\033[91m'     # Red
    SELECTED = '\033[43m'  # Yellow background

# Symbols
class Symbols:
    EMPTY = ' '
    X = 'X'
    O = 'O'
    
    # Box drawing
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'
    HORIZONTAL = '─'
    VERTICAL = '│'
    CROSS = '┼'
    T_DOWN = '┬'
    T_UP = '┴'
    T_RIGHT = '├'
    T_LEFT = '┤'

class KeyInput:
    """Handle keyboard input for arrow keys and enter"""
    
    @staticmethod
    def get_key():
        """Get a single keypress"""
        if sys.platform == 'win32':
            import msvcrt
            key = msvcrt.getch()
            if key in [b'\xe0', b'\x00']:
                key = msvcrt.getch()
                if key == b'H': return 'UP'
                elif key == b'P': return 'DOWN'
                elif key == b'K': return 'LEFT'
                elif key == b'M': return 'RIGHT'
            elif key == b'\r': return 'ENTER'
            elif key == b'\x1b': return 'ESC'
            return None
        else:
            # Unix/Linux/Mac
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                key = sys.stdin.read(1)
                
                if key == '\x1b':  # ESC sequence
                    if sys.stdin.read(1) == '[':
                        arrow = sys.stdin.read(1)
                        if arrow == 'A': return 'UP'
                        elif arrow == 'B': return 'DOWN'
                        elif arrow == 'C': return 'RIGHT'
                        elif arrow == 'D': return 'LEFT'
                    return 'ESC'
                elif key == '\r' or key == '\n':
                    return 'ENTER'
                elif key == ' ':
                    return 'SPACE'
                return None
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

class TicTacToe:
    def __init__(self):
        self.board = [[Symbols.EMPTY for _ in range(3)] for _ in range(3)]
        self.cursor_row = 1
        self.cursor_col = 1
        self.current_player = Symbols.X  # Human always starts as X
        self.human_symbol = Symbols.X
        self.computer_symbol = Symbols.O
        self.difficulty = 'medium'
        self.game_over = False
        self.winner = None
        self.moves_count = 0
        
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def draw_header(self):
        """Draw game header"""
        self.clear_screen()
        print(f"\n{Colors.HEADER}{Colors.BOLD}╔═══════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.HEADER}{Colors.BOLD}║       TIC TAC TOE GAME        ║{Colors.RESET}")
        print(f"{Colors.HEADER}{Colors.BOLD}╚═══════════════════════════════╝{Colors.RESET}")
        print(f"{Colors.DIM}    You are {Colors.PLAYER_X}X{Colors.DIM} • Computer is {Colors.PLAYER_O}O{Colors.RESET}")
        print(f"{Colors.DIM}    Use arrow keys to move, Enter to place{Colors.RESET}\n")
    
    def draw_board(self):
        """Draw the game board with current state and cursor"""
        print(f"{Colors.BOARD}   {Symbols.TOP_LEFT}───{Symbols.T_DOWN}───{Symbols.T_DOWN}───{Symbols.TOP_RIGHT}{Colors.RESET}")
        
        for i in range(3):
            print(f"{Colors.BOARD}   {Symbols.VERTICAL}{Colors.RESET}", end='')
            for j in range(3):
                # Check if this is the cursor position
                is_cursor = (i == self.cursor_row and j == self.cursor_col)
                
                if is_cursor and self.board[i][j] == Symbols.EMPTY:
                    print(f"{Colors.CURSOR} {Colors.BOLD}·{Colors.RESET} ", end='')
                else:
                    symbol = self.board[i][j]
                    if symbol == Symbols.X:
                        if is_cursor:
                            print(f"{Colors.CURSOR}{Colors.PLAYER_X} {symbol} {Colors.RESET}", end='')
                        else:
                            print(f" {Colors.PLAYER_X}{symbol}{Colors.RESET} ", end='')
                    elif symbol == Symbols.O:
                        if is_cursor:
                            print(f"{Colors.CURSOR}{Colors.PLAYER_O} {symbol} {Colors.RESET}", end='')
                        else:
                            print(f" {Colors.PLAYER_O}{symbol}{Colors.RESET} ", end='')
                    else:
                        print(f" {symbol} ", end='')
                
                if j < 2:
                    print(f"{Colors.BOARD}{Symbols.VERTICAL}{Colors.RESET}", end='')
                else:
                    print(f"{Colors.BOARD}{Symbols.VERTICAL}{Colors.RESET}")
            
            if i < 2:
                print(f"{Colors.BOARD}   {Symbols.T_RIGHT}───{Symbols.CROSS}───{Symbols.CROSS}───{Symbols.T_LEFT}{Colors.RESET}")
        
        print(f"{Colors.BOARD}   {Symbols.BOTTOM_LEFT}───{Symbols.T_UP}───{Symbols.T_UP}───{Symbols.BOTTOM_RIGHT}{Colors.RESET}\n")
    
    def is_valid_move(self, row, col):
        """Check if a move is valid"""
        return 0 <= row < 3 and 0 <= col < 3 and self.board[row][col] == Symbols.EMPTY
    
    def make_move(self, row, col, symbol):
        """Make a move on the board"""
        if self.is_valid_move(row, col):
            self.board[row][col] = symbol
            self.moves_count += 1
            return True
        return False
    
    def check_winner(self):
        """Check if there's a winner"""
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != Symbols.EMPTY:
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != Symbols.EMPTY:
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != Symbols.EMPTY:
            return self.board[0][0]
        
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != Symbols.EMPTY:
            return self.board[0][2]
        
        return None
    
    def is_board_full(self):
        """Check if the board is full"""
        return self.moves_count == 9
    
    def get_empty_cells(self):
        """Get all empty cells on the board"""
        empty_cells = []
        for i in range(3):
            for j in range(3):
                if self.board[i][j] == Symbols.EMPTY:
                    empty_cells.append((i, j))
        return empty_cells
    
    def minimax(self, depth, is_maximizing, alpha=-float('inf'), beta=float('inf')):
        """Minimax algorithm with alpha-beta pruning for AI"""
        winner = self.check_winner()
        
        if winner == self.computer_symbol:
            return 10 - depth
        elif winner == self.human_symbol:
            return depth - 10
        elif self.is_board_full():
            return 0
        
        if is_maximizing:
            max_eval = -float('inf')
            for row, col in self.get_empty_cells():
                self.board[row][col] = self.computer_symbol
                self.moves_count += 1
                eval_score = self.minimax(depth + 1, False, alpha, beta)
                self.board[row][col] = Symbols.EMPTY
                self.moves_count -= 1
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for row, col in self.get_empty_cells():
                self.board[row][col] = self.human_symbol
                self.moves_count += 1
                eval_score = self.minimax(depth + 1, True, alpha, beta)
                self.board[row][col] = Symbols.EMPTY
                self.moves_count -= 1
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def get_computer_move(self):
        """Get computer's move based on difficulty"""
        empty_cells = self.get_empty_cells()
        
        if self.difficulty == 'easy':
            # Random move
            return random.choice(empty_cells)
        
        elif self.difficulty == 'medium':
            # Mix of random and smart moves
            if random.random() < 0.7:  # 70% chance of smart move
                return self.get_best_move()
            else:
                return random.choice(empty_cells)
        
        else:  # hard
            # Always make the best move
            return self.get_best_move()
    
    def get_best_move(self):
        """Get the best move using minimax"""
        best_score = -float('inf')
        best_move = None
        
        for row, col in self.get_empty_cells():
            self.board[row][col] = self.computer_symbol
            self.moves_count += 1
            score = self.minimax(0, False)
            self.board[row][col] = Symbols.EMPTY
            self.moves_count -= 1
            
            if score > best_score:
                best_score = score
                best_move = (row, col)
        
        return best_move
    
    def handle_arrow_input(self):
        """Handle arrow key input for board navigation"""
        while True:
            key = KeyInput.get_key()
            
            if key == 'UP' and self.cursor_row > 0:
                self.cursor_row -= 1
                return 'move'
            elif key == 'DOWN' and self.cursor_row < 2:
                self.cursor_row += 1
                return 'move'
            elif key == 'LEFT' and self.cursor_col > 0:
                self.cursor_col -= 1
                return 'move'
            elif key == 'RIGHT' and self.cursor_col < 2:
                self.cursor_col += 1
                return 'move'
            elif key == 'ENTER' or key == 'SPACE':
                if self.is_valid_move(self.cursor_row, self.cursor_col):
                    return 'place'
                else:
                    return 'invalid'
            elif key == 'ESC':
                return 'quit'
    
    def select_from_menu(self, options, title):
        """Generic menu selection using arrow keys"""
        selected = 0
        
        while True:
            self.clear_screen()
            print(f"\n{Colors.HEADER}{Colors.BOLD}{title}{Colors.RESET}")
            print(f"{Colors.DIM}{'─' * len(title)}{Colors.RESET}")
            print(f"{Colors.DIM}Use arrow keys to select, Enter to confirm{Colors.RESET}\n")
            
            for i, option in enumerate(options):
                if i == selected:
                    print(f"{Colors.SELECTED}{Colors.BOLD}▶ {option} {Colors.RESET}")
                else:
                    print(f"  {option}")
            
            key = KeyInput.get_key()
            
            if key == 'UP' and selected > 0:
                selected -= 1
            elif key == 'DOWN' and selected < len(options) - 1:
                selected += 1
            elif key == 'ENTER' or key == 'SPACE':
                return selected
            elif key == 'ESC':
                return None
    
    def show_win_message(self):
        """Display win/draw message with animation"""
        self.draw_header()
        self.draw_board()
        
        if self.winner == self.human_symbol:
            print(f"\n{Colors.WIN}{Colors.BOLD}🎉 CONGRATULATIONS! YOU WIN! 🎉{Colors.RESET}")
        elif self.winner == self.computer_symbol:
            print(f"\n{Colors.ERROR}{Colors.BOLD}💻 COMPUTER WINS! BETTER LUCK NEXT TIME! 💻{Colors.RESET}")
        else:
            print(f"\n{Colors.BOARD}{Colors.BOLD}🤝 IT'S A DRAW! WELL PLAYED! 🤝{Colors.RESET}")
        
        print(f"\n{Colors.DIM}Game finished in {self.moves_count} moves{Colors.RESET}")
        print(f"{Colors.DIM}Press any key to continue...{Colors.RESET}")
        KeyInput.get_key()
    
    def play_again_menu(self):
        """Ask if player wants to play again using arrow keys"""
        options = ["Yes, play again!", "No, exit game"]
        choice = self.select_from_menu(options, "PLAY AGAIN?")
        return choice == 0 if choice is not None else False
    
    def choose_difficulty(self):
        """Let player choose difficulty using arrow keys"""
        options = [
            "Easy   - Computer makes random moves",
            "Medium - Computer mixes smart and random moves",
            "Hard   - Computer plays optimally (very difficult!)"
        ]
        
        choice = self.select_from_menu(options, "SELECT DIFFICULTY")
        
        if choice is not None:
            self.difficulty = ['easy', 'medium', 'hard'][choice]
        else:
            self.difficulty = 'medium'  # Default
    
    def choose_symbol(self):
        """Let player choose their symbol using arrow keys"""
        options = ["Play as X (go first)", "Play as O (go second)"]
        choice = self.select_from_menu(options, "CHOOSE YOUR SYMBOL")
        
        if choice == 0:
            self.human_symbol = 'X'
            self.computer_symbol = 'O'
        else:
            self.human_symbol = 'O'
            self.computer_symbol = 'X'
        
        self.current_player = 'X'  # X always goes first
    
    def reset_game(self):
        """Reset the game state"""
        self.board = [[Symbols.EMPTY for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'
        self.cursor_row = 1
        self.cursor_col = 1
        self.game_over = False
        self.winner = None
        self.moves_count = 0
    
    def run(self):
        """Main game loop"""
        self.clear_screen()
        print(f"{Colors.HEADER}{Colors.BOLD}Welcome to Tic Tac Toe!{Colors.RESET}")
        print(f"{Colors.DIM}Arrow Key Navigation Edition{Colors.RESET}")
        time.sleep(1.5)
        
        while True:
            self.reset_game()
            self.choose_difficulty()
            self.choose_symbol()
            
            # If computer is X, it goes first
            if self.computer_symbol == 'X':
                self.draw_header()
                self.draw_board()
                print(f"{Colors.DIM}Computer is thinking...{Colors.RESET}")
                time.sleep(1)
                row, col = self.get_computer_move()
                self.make_move(row, col, self.computer_symbol)
                self.current_player = 'O'
            
            while not self.game_over:
                self.draw_header()
                self.draw_board()
                
                if self.current_player == self.human_symbol:
                    # Human's turn with arrow keys
                    action = self.handle_arrow_input()
                    
                    if action == 'move':
                        continue  # Redraw with new cursor position
                    elif action == 'place':
                        self.make_move(self.cursor_row, self.cursor_col, self.human_symbol)
                    elif action == 'invalid':
                        # Flash error briefly
                        self.draw_header()
                        self.draw_board()
                        print(f"{Colors.ERROR}That position is already taken!{Colors.RESET}")
                        time.sleep(0.8)
                        continue
                    elif action == 'quit':
                        print(f"\n{Colors.HEADER}Thanks for playing!{Colors.RESET}\n")
                        return
                else:
                    # Computer's turn
                    print(f"{Colors.DIM}Computer is thinking...{Colors.RESET}")
                    time.sleep(0.8)
                    row, col = self.get_computer_move()
                    self.make_move(row, col, self.computer_symbol)
                    # Move cursor to computer's move
                    self.cursor_row = row
                    self.cursor_col = col
                    time.sleep(0.5)
                
                # Check for winner
                self.winner = self.check_winner()
                if self.winner or self.is_board_full():
                    self.game_over = True
                else:
                    # Switch player
                    self.current_player = self.computer_symbol if self.current_player == self.human_symbol else self.human_symbol
            
            self.show_win_message()
            
            if not self.play_again_menu():
                break
        
        self.clear_screen()
        print(f"\n{Colors.HEADER}Thanks for playing Tic Tac Toe!{Colors.RESET}")
        print(f"{Colors.DIM}Arrow Key Navigation Edition{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        game = TicTacToe()
        game.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.HEADER}Game interrupted. Thanks for playing!{Colors.RESET}\n")
