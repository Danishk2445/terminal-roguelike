import os
import random
import time
from math import sqrt
from dataclasses import dataclass
from typing import List, Tuple
import sys
import threading

# Platform-specific keyboard input setup
if os.name == 'nt':  # for Windows
    import msvcrt
else:  # for Unix/Linux
    import tty
    import termios

@dataclass
class Entity:
    x: int
    y: int
    char: str
    dx: int = 0  # Direction for bullets
    dy: int = 0
    is_enemy: bool = False

class Game:
    def __init__(self, width: int = 40, height: int = 20):
        self.width = width
        self.height = height
        self.player = Entity(width // 2, height // 2, '@')
        self.bullets: List[Entity] = []
        self.enemies: List[Entity] = []
        self.score = 0
        self.game_over = False
        self.last_spawn_time = time.time()
        self.last_update_time = time.time()
        
    def spawn_enemy(self):
        current_time = time.time()
        if current_time - self.last_spawn_time >= 1:  # Spawn every second
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                x, y = random.randint(0, self.width-1), 0
            elif side == 'bottom':
                x, y = random.randint(0, self.width-1), self.height-1
            elif side == 'left':
                x, y = 0, random.randint(0, self.height-1)
            else:
                x, y = self.width-1, random.randint(0, self.height-1)
            self.enemies.append(Entity(x, y, 'E', is_enemy=True))
            self.last_spawn_time = current_time
    
    def move_enemies(self):
        for enemy in self.enemies:
            # Move towards player
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            dist = sqrt(dx*dx + dy*dy)
            if dist != 0:
                enemy.x += int(dx/dist + 0.5)
                enemy.y += int(dy/dist + 0.5)
            
            # Check collision with player
            if enemy.x == self.player.x and enemy.y == self.player.y:
                self.game_over = True
    
    def shoot(self, direction: Tuple[int, int]):
        dx, dy = direction
        # Create bullet with direction
        bullet = Entity(self.player.x + dx, self.player.y + dy, '→', dx, dy)
        # Set appropriate bullet character based on direction
        if dx == 1: bullet.char = '→'
        elif dx == -1: bullet.char = '←'
        elif dy == 1: bullet.char = '↓'
        elif dy == -1: bullet.char = '↑'
        self.bullets.append(bullet)
    
    def update_bullets(self):
        # Move bullets
        for bullet in self.bullets[:]:
            bullet.x += bullet.dx
            bullet.y += bullet.dy
            
            if bullet.x < 0 or bullet.x >= self.width or bullet.y < 0 or bullet.y >= self.height:
                self.bullets.remove(bullet)
                continue
                
            # Check collision with enemies
            for enemy in self.enemies[:]:
                if bullet.x == enemy.x and bullet.y == enemy.y:
                    self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    self.score += 10
                    break
    
    def draw(self):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Create empty grid
        grid = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
        # Draw entities
        for bullet in self.bullets:
            grid[bullet.y][bullet.x] = bullet.char
        for enemy in self.enemies:
            grid[enemy.y][enemy.x] = enemy.char
        grid[self.player.y][self.player.x] = self.player.char
        
        # Print grid and score
        print(f"Score: {self.score}")
        print('=' * (self.width + 2))
        for row in grid:
            print('|' + ''.join(row) + '|')
        print('=' * (self.width + 2))
        print("\nControls: WASD - Move, IJKL - Shoot, Q - Quit")

def get_key():
    if os.name == 'nt':  # Windows
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8').lower()
        return None
    else:  # Unix/Linux
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x03':  # Handle Ctrl+C
                raise KeyboardInterrupt
            return ch.lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def main():
    game = Game()
    frame_delay = 0.05  # 20 FPS

    # Set up non-blocking input for Unix systems
    if os.name != 'nt':
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            
            while not game.game_over:
                current_time = time.time()
                
                if current_time - game.last_update_time >= frame_delay:
                    # Check for input
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        char = sys.stdin.read(1)
                        
                        if char == 'q':
                            break
                            
                        # Movement
                        if char == 'w' and game.player.y > 0:
                            game.player.y -= 1
                        elif char == 's' and game.player.y < game.height - 1:
                            game.player.y += 1
                        elif char == 'a' and game.player.x > 0:
                            game.player.x -= 1
                        elif char == 'd' and game.player.x < game.width - 1:
                            game.player.x += 1
                            
                        # Shooting
                        elif char == 'i':  # up
                            game.shoot((0, -1))
                        elif char == 'k':  # down
                            game.shoot((0, 1))
                        elif char == 'j':  # left
                            game.shoot((-1, 0))
                        elif char == 'l':  # right
                            game.shoot((1, 0))
                    
                    # Update game state
                    game.spawn_enemy()
                    game.move_enemies()
                    game.update_bullets()
                    game.draw()
                    
                    game.last_update_time = current_time
                
                time.sleep(0.01)  # Small delay to prevent CPU overuse
                
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    else:  # Windows version
        while not game.game_over:
            current_time = time.time()
            
            if current_time - game.last_update_time >= frame_delay:
                # Check for input
                char = get_key()
                if char:
                    if char == 'q':
                        break
                        
                    # Movement
                    if char == 'w' and game.player.y > 0:
                        game.player.y -= 1
                    elif char == 's' and game.player.y < game.height - 1:
                        game.player.y += 1
                    elif char == 'a' and game.player.x > 0:
                        game.player.x -= 1
                    elif char == 'd' and game.player.x < game.width - 1:
                        game.player.x += 1
                        
                    # Shooting
                    elif char == 'i':  # up
                        game.shoot((0, -1))
                    elif char == 'k':  # down
                        game.shoot((0, 1))
                    elif char == 'j':  # left
                        game.shoot((-1, 0))
                    elif char == 'l':  # right
                        game.shoot((1, 0))
                
                # Update game state
                game.spawn_enemy()
                game.move_enemies()
                game.update_bullets()
                game.draw()
                
                game.last_update_time = current_time
            
            time.sleep(0.01)  # Small delay to prevent CPU overuse
    
    print("\nGame Over! Final score:", game.score)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGame terminated by user")