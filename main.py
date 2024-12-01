import curses
import random
import time
import math

# constants
MAP_WIDTH = 40
MAP_HEIGHT = 20
NUM_ENEMIES = 10
WALL_DENSITY = 30 # higher = fewer walls

# character representations
PLAYER_CHAR = '@'
ENEMY_CHAR = 'E'
WALL_CHAR = '#'
FLOOR_CHAR = '.'
ARROW_CHAR = '*'
ENEMY_ARROW_CHAR = '+'

# color pair constants
COLOR_PLAYER = 1
COLOR_ENEMY = 2
COLOR_WALL = 3
COLOR_FLOOR = 4
COLOR_PROJECTILE = 5
COLOR_ENEMY_PROJECTILE = 6
COLOR_STATUS = 7
COLOR_WIN_MESSAGE = 8

class Entity:
    """base class for game entities (player, enemies, projectiles)
        stores position and character of entity"""
    def __init__(self, x, y, char):
        self.x = x
        self.y = y
        self.char = char

class Player(Entity):
    """player class with health, speed, and ammo tracking
        inherits position and character from entity"""
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_CHAR)
        self.health = 100
        self.speed = 1
        self.ammo = 10

class Enemy(Entity):
    """enemy class with health, speed, and shooting behaviour
        tracks last shot time and randomizes shooting intervals
        inherits position and character from entity"""
    def __init__(self, x, y):
        super().__init__(x, y, ENEMY_CHAR)
        self.health = 50
        self.speed = 0.5
        self.last_shot_time = time.time()
        self.shoot_delay = random.uniform(1, 3)

class Projectile(Entity):
    """projectile class representing shots fired by player or enemy
        tracks movement direction, speed, and origin
        inherits position and character from entity"""
    def __init__(self, x, y, dx, dy, is_enemy=False):
        char = ENEMY_ARROW_CHAR if is_enemy else ARROW_CHAR
        super().__init__(x, y, char)
        self.dx = dx # x-direction movement vector
        self.dy = dy # y-direction movement vector
        self.speed = 2
        self.is_enemy = is_enemy # origin of projectile (player or enemy)

class Game:
    """game class managing game state, rendering, and game loop
        handles entity interactions, map generation, and input processing"""
    def __init__(self, stdscr):
        self.stdscr = stdscr # main game screen
        self.setup_colors()
        curses.curs_set(0) # hide cursor
        stdscr.nodelay(True)
        stdscr.keypad(True)
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        # initialize game state
        self.map = self.generate_map() # generate random map
        self.player = self.spawn_entity(Player) # spawn player
        self.enemies = [self.spawn_entity(Enemy) for _ in range(NUM_ENEMIES)] # spawn enemies
        self.projectiles = []
        # game timing and state tracking
        self.last_update = time.time()
        self.game_over = False
        
    def setup_colors(self):
        """Initialize color pairs"""
        curses.start_color()
        curses.use_default_colors()
        # define color pairs (foreground, background)
        curses.init_pair(COLOR_PLAYER, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_ENEMY, curses.COLOR_RED, -1)
        curses.init_pair(COLOR_WALL, curses.COLOR_CYAN, -1)
        curses.init_pair(COLOR_FLOOR, curses.COLOR_BLACK, -1)
        curses.init_pair(COLOR_PROJECTILE, curses.COLOR_YELLOW, -1)
        curses.init_pair(COLOR_ENEMY_PROJECTILE, curses.COLOR_MAGENTA, -1)
        curses.init_pair(COLOR_STATUS, curses.COLOR_GREEN, -1)
        curses.init_pair(COLOR_WIN_MESSAGE, curses.COLOR_GREEN, -1)
    
    def generate_map(self):
        """generate a map with walls and floor"""
        map_grid = [[FLOOR_CHAR for _ in range(self.width)] for _ in range(self.height)]
        
        # create border walls
        for x in range(self.width):
            map_grid[0][x] = WALL_CHAR # top row wall
            map_grid[self.height-1][x] = WALL_CHAR # bottom row wall
        
        for y in range(self.height):
            map_grid[y][0] = WALL_CHAR # left wall
            map_grid[y][self.width-1] = WALL_CHAR # right wall
        
        # random walls in arena
        for _ in range(self.width * self.height // WALL_DENSITY):
            # width or height - 1 are walls so -2 is the max available
            x, y = random.randint(1, self.width-2), random.randint(1, self.height-2)
            map_grid[y][x] = WALL_CHAR
        
        return map_grid
    
    def spawn_entity(self, entity_class):
        """spawn an entity in a random floor tile"""
        while True:
            x, y = random.randint(1, self.width - 2), random.randint(1, self.height - 2)
            if self.map[y][x] == FLOOR_CHAR:
                return entity_class(x, y)
    
    def move_entity(self, entity, dx, dy):
        """move an entity if the destination is a floor tile"""
        new_x, new_y = entity.x + dx, entity.y + dy
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            if self.map[new_y][new_x] == FLOOR_CHAR:
                entity.x, entity.y = new_x, new_y
        
    def handle_input(self):
        """handle player input"""
        key = self.stdscr.getch()
        # movement with arrow keys
        if key == curses.KEY_UP:
            self.move_entity(self.player, 0, -1)
        elif key == curses.KEY_DOWN:
            self.move_entity(self.player, 0, 1)
        elif key == curses.KEY_LEFT:
            self.move_entity(self.player, -1, 0)
        elif key == curses.KEY_RIGHT:
            self.move_entity(self.player, 1, 0)
        
        # 8 direction shooting keys (WASD + QEZC)
        elif key == ord('w'):
            self.shoot(self.player.x, self.player.y, 0, -1)
        elif key == ord('s'):
            self.shoot(self.player.x, self.player.y, 0, 1)
        elif key == ord('a'):
            self.shoot(self.player.x, self.player.y, -1, 0)
        elif key == ord('d'):
            self.shoot(self.player.x, self.player.y, 1, 0)
        elif key == ord('q'):
            self.shoot(self.player.x, self.player.y, -1, -1)
        elif key == ord('e'):
            self.shoot(self.player.x, self.player.y, 1, -1)
        elif key == ord('z'):
            self.shoot(self.player.x, self.player.y, -1, 1)
        elif key == ord('c'):
            self.shoot(self.player.x, self.player.y, 1, 1)
        # quit
        elif key == ord('x'):
            self.game_over = True
    
    def shoot(self, x, y, dx, dy, is_enemy=False):
        """create a projectile from a given position"""
        if not is_enemy:
            if self.player.ammo <= 0:
                return
            self.player.ammo -= 1
        projectile = Projectile(x, y, dx, dy, is_enemy)
        self.projectiles.append(projectile)
    
    def update_enemies(self, delta_time):
        """update enemy movement and shooting"""
        current_time = time.time()
        for enemy in self.enemies:
            dx = self.player.x - enemy.x
            dy = self.player.y - enemy.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                dx = dx / distance
                dy = dy / distance
            dx += random.uniform(-0.2, 0.2)
            dy += random.uniform(-0.2, 0.2)
            new_x = enemy.x + dx * enemy.speed * delta_time
            new_y = enemy.y + dy * enemy.speed * delta_time
            if (0 <= int(new_x) < self.width and
                0 <= int(new_y) < self.height and
                self.map[int(new_y)][int(new_x)] == FLOOR_CHAR):
                enemy.x = new_x
                enemy.y = new_y
            if current_time - enemy.last_shot_time >= enemy.shoot_delay:
                shot_dx = self.player.x - enemy.x
                shot_dy = self.player.y - enemy.y
                shot_distance = math.sqrt(shot_dx**2 + shot_dy**2)
                if shot_distance > 0:
                    shot_dx /= shot_distance
                    shot_dy /= shot_distance
                self.shoot(enemy.x, enemy.y, shot_dx, shot_dy, is_enemy=True)
                enemy.last_shot_time = current_time
                enemy.shoot_delay = random.uniform(1, 3)
    
    def update_projectiles(self, delta_time):
        """update projectile positions and check for collisions"""
        for projectile in self.projectiles[:]:
            projectile.x += projectile.dx * projectile.speed * delta_time
            projectile.y += projectile.dy * projectile.speed * delta_time
            if (projectile.x < 0 or projectile.x >= self.width or
                projectile.y < 0 or projectile.y >= self.height):
                self.projectiles.remove(projectile)
                continue
            if self.map[int(projectile.y)][int(projectile.x)] == WALL_CHAR:
                self.projectiles.remove(projectile)
                continue
            if projectile.is_enemy: # if project from enemy
                # if enemy projectile hits player
                if (math.floor(self.player.x) == math.floor(projectile.x) and
                    math.floor(self.player.y) == math.floor(projectile.y)):
                    self.player.health -= 10
                    self.projectiles.remove(projectile)
                    if self.player.health <= 0:
                        self.game_over = True
                    continue
            else:
                for enemy in self.enemies[:]:
                    # if you hit enemy
                    if (math.floor(enemy.x) == math.floor(projectile.x) and
                        math.floor(enemy.y) == math.floor(projectile.y)):
                        self.projectiles.remove(projectile)
                        self.enemies.remove(enemy)
                        self.player.ammo += 2
                        break
    def render(self):
        """render the game state"""
        self.stdscr.clear()
        # render map
        for y in range(self.height):
            for x in range(self.width):
                char = self.map[y][x]
                if char == WALL_CHAR:
                    self.stdscr.addch(y, x, char, curses.color_pair(COLOR_WALL))
                else:
                    self.stdscr.addch(y, x, char, curses.color_pair(COLOR_FLOOR))
        # render player
        self.stdscr.addch(self.player.y, self.player.x, self.player.char,
                          curses.color_pair(COLOR_PLAYER))
        # render enemies
        for enemy in self.enemies:
            self.stdscr.addch(int(enemy.y), int(enemy.x), enemy.char, 
                              curses.color_pair(COLOR_ENEMY))
        # render projectiles
        for projectile in self.projectiles:
            color = COLOR_ENEMY_PROJECTILE if projectile.is_enemy else COLOR_PROJECTILE
            self.stdscr.addch(int(projectile.y), int(projectile.x), projectile.char,
                              curses.color_pair(color))
        # render status
        status = f"Enemies Left: {len(self.enemies)} | Player Health: {self.player.health} | Ammo: {self.player.ammo}"
        self.stdscr.addstr(self.height, 0, status, curses.color_pair(COLOR_STATUS))
        
        self.stdscr.refresh()
    
    def run(self):
        """main game loop""" 
        while not self.game_over:
            current_time = time.time()
            delta_time = current_time - self.last_update
            self.last_update = current_time
            self.handle_input()
            self.update_projectiles(delta_time)
            self.update_enemies(delta_time)
            self.render()
            if not self.enemies:
                self.stdscr.clear()
                max_y, max_x = self.stdscr.getmaxyx()
                win_message = "You Win!"
                play_again_message = "Press 'y' to play again or 'q' to quit"
                win_y = max_y // 2 - 1
                play_again_y = max_y // 2 + 1
                win_x = (max_x - len(win_message)) // 2
                play_again_x = (max_x - len(play_again_message)) // 2
                self.stdscr.addstr(win_y, win_x, win_message,
                                   curses.color_pair(COLOR_WIN_MESSAGE) | curses.A_BOLD)
                self.stdscr.addstr(play_again_y, play_again_x, play_again_message,
                                   curses.color_pair(COLOR_STATUS))
                self.stdscr.refresh()
                while True:
                    key = self.stdscr.getch()
                    if key == ord('y'):
                        self.__init__(self.stdscr)
                        break
                    elif key == ord('q'):
                        self.game_over = True
                        break
            time.sleep(0.05)

def main(stdscr):
    game = Game(stdscr)
    game.run()

if __name__ == "__main__":
    curses.wrapper(main)
        