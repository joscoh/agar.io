import random
import numpy
from gameobject import *
from player import Player

FOOD_COUNT = 2000
OTHER_PLAYERS = 20
INITIAL_RADIUS = 10


def random_food_position(x, y):
    '''Function that provides a randomized location for placing food'''
    randx = random.gauss(x, 20)
    randx = max(randx, 0)
    randx = min(randx, 2400)
    randy = random.gauss(y, 20)
    randy = max(randy, 0)
    randy = min(randy, 2400)
    return (randx, randy)


def food_generator():
    '''Generates food pellets semi-randomly so they are disbursed somewhat
    evenly throughout the board. Note that the number of food pellets is
    constant, so the generator is called whenever a piece of food is eaten'''
    x = 0
    y = 0
    while(True):
        while x < 44:
            while y < 44:
                x_location = 54.5 * x
                y_location = 54.5 * y
                p1, p2 = random_food_position(x_location, y_location)
                color = wx.Colour(int(random.uniform(0, 255)),
                                  int(random.uniform(0, 255)),
                                  int(random.uniform(0, 255)))
                yield GameObject(p1, p2, 5, color, True)
                y += 1
            y = 0
            x += 1
        x = 0


def create_player(radius, id_number):
    '''Creates a player in a random position such that more players are near
    the middle of the frame'''
    x = random.gauss(GAME_WIDTH / 2, FRAME_WIDTH)
    x = max(x, 0)
    x = min(x, GAME_WIDTH)
    y = random.gauss(GAME_HEIGHT / 2, FRAME_HEIGHT)
    y = max(y, 0)
    y = min(y, GAME_HEIGHT)
    color = wx.Colour(int(random.uniform(0, 256)), int(random.uniform(0, 256)),
                      int(random.uniform(0, 256)))
    return Player(x, y, radius, color, id_number)


class Game_Frame(wx.Frame):

    def __init__(self, *args, **kw):
        super(Game_Frame, self).__init__(*args, **kw,
                                         size=(FRAME_WIDTH, FRAME_HEIGHT))
        # decay timer
        self.decay_timer = wx.Timer(self)
        self.decay_timer.Start(10000)
        self.Bind(wx.EVT_TIMER, self.on_decay_timer, self.decay_timer)
        # movement setup
        self.move_timer = wx.Timer(self)
        self.move_timer.Start(50)
        self.direction = (0, 0)

        self.Bind(wx.EVT_TIMER, self.on_move_timer, self.move_timer)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.Bind(wx.EVT_MOTION, self.on_mouse)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        # food setup
        self.food_gen = food_generator()
        xGrids = GAME_WIDTH / FRAME_WIDTH
        yGrids = GAME_HEIGHT / FRAME_HEIGHT
        self.food_pieces = [[] for _ in range(int(xGrids * yGrids))]
        for _ in range(FOOD_COUNT):
            food = next(self.food_gen)
            i = food.get_grid_location()[0]
            self.food_pieces[i].append(food)

        # other player setup
        self.other_players = []
        self.playerIds = {}
        for i in range(OTHER_PLAYERS):
            cpu_player = create_player(
                int(random.uniform(INITIAL_RADIUS, 10 * INITIAL_RADIUS)), i)
            self.other_players.append(cpu_player)
            self.playerIds[i] = cpu_player

        self.Centre()
        self.Show()
        self.SetDoubleBuffered(True)
        self.user = create_player(INITIAL_RADIUS, OTHER_PLAYERS + 1)
        self.playerIds[OTHER_PLAYERS + 1] = self.user

    def get_relative_position(self, go):
        '''Gets the relative position of a game object, relative to the user.
        This allows us to only draw objects that are within a 600 x 600 square
        around the user'''
        abs_x, abs_y = go.get_absolute_position()
        ux, uy = self.user.get_absolute_position()
        return (abs_x - ux + 300, abs_y - uy + 300)

    def on_key(self, event):
        '''If the spacebar is pressed, shoot a blob in the current direction'''
        if event.GetKeyCode() == wx.WXK_SPACE:
            self.user.shoot(self.direction)

    def on_mouse(self, event):
        '''If the mouse is moved, change the current direction of movement'''
        self.direction = GameObject.normalize(numpy.subtract(
            event.GetPosition(), self.get_relative_position(self.user)))

    def on_decay_timer(self, event):
        '''Every 10 seconds, decay all the players'''
        self.user.decay()
        self.Refresh()

    def on_move_timer(self, event):
        '''Every 50 miliseconds, move and redraw all of the players, handling
        collisions with food and other players as necessary'''
        x, y = Game_Frame.trim_position(self.direction,
                                        self.user.get_absolute_position())
        self.user.move(((x, y)))
        for b in self.user.blobs:
            self.handle_player_collisions(self.user, b)
            self.handle_food_collisions(b)
        for p in self.other_players:
            for b in p.blobs:
                self.handle_food_collisions(b)
                self.handle_player_collisions(p, b)
            self.move_CPU(p)
        self.Refresh()

    def handle_food_collisions(self, blob):
        '''Handles food collisions between a blob and a piece of food, changing
        the blob's size appropriately and removing the food. Note that a new
        piece of food is also generated, usually elsewhere on the board'''
        grid = blob.get_grid_location()
        for g in grid:
            food_to_remove = None
            for f in self.food_pieces[g]:
                (x, y) = self.get_relative_position(f)
                if 0 < x < 600 and 0 < y < 600 and f.isFood:
                    if GameObject.has_collided(blob, f):
                        blob.eatObj(f)
                        food_to_remove = f
            if food_to_remove is not None:
                self.food_pieces[g].remove(food_to_remove)
                # add another food
                food = next(self.food_gen)
                i = food.get_grid_location()[0]
                self.food_pieces[i].append(food)

    def handle_player_collisions(self, player, blob):
        '''Handles player collisions and allows one blob to eat another. Deals
        with all cases, including when the last blob of a player is eaten and
        the player loses. In this case, a new player is generated, or, in the
        user's case, they start again in a random location'''
        blob_to_remove = None
        all_players = [p for p in self.other_players]
        all_players.append(self.user)
        all_players.remove(player)
        all_blobs = []
        [all_blobs.extend(p.blobs) for p in all_players]
        for b in all_blobs:
            if blob > b and GameObject.hasEaten(blob, b):
                blob.eatObj(b)
                blob_to_remove = b
                player_to_remove = self.playerIds[blob_to_remove.id_number]
            if blob_to_remove is not None:
                player_to_remove.remove_blob(blob_to_remove)
                if(player_to_remove is not None and
                   player_to_remove in self.other_players and
                   len(player_to_remove.blobs) == 0):
                    self.other_players.remove(player_to_remove)
                    # add another player
                    new_player = create_player(int(random.uniform(
                                               INITIAL_RADIUS,
                                               10 * INITIAL_RADIUS)),
                                               player_to_remove.id_number)
                    self.other_players.append(new_player)
                    self.playerIds[player_to_remove.id_number] = new_player
                    return
                elif (player_to_remove is not None and
                      len(player_to_remove.blobs) == 0):
                    # restart the game if the player lost
                    new_user = create_player(INITIAL_RADIUS,
                                             self.user.id_number)
                    self.user = new_user
                    self.playerIds[self.user.id_number] = self.user
                return

    @staticmethod
    def trim_position(p, ap):
        '''Trims a given velocity and absolute position so the velocity will
        fit within the game boundaries'''
        x, y = p
        ax, ay = ap
        if ax <= 0 and x <= 0:
            x = 0
        if ax >= GAME_WIDTH and x >= 0:
            x = 0
        if ay <= 0 and y <= 0:
            y = 0
        if ay >= GAME_HEIGHT and y >= 0:
            y = 0
        return (x, y)

    def on_exit(self, event):
        '''Closes the game on exit'''
        self.Close(True)

    def on_paint(self, e):
        '''Draws all the players and food objects'''
        dc = wx.PaintDC(self)
        dc.SetBackgroundMode(wx.SOLID)
        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()

        # find the grids that are in the range of the user's sight
        grids = Game_Frame.get_grids_in_sight(300, self.user)
        for i in grids:
            for f in self.food_pieces[i]:
                x, y = self.get_relative_position(f)
                f.draw(dc, (x, y))
        for p in self.other_players:
            x, y = self.get_relative_position(p)
            p.draw(dc, (x, y))
        for b in self.user.blobs:
            b.draw(dc, self.get_relative_position(b))

    def danger_reward(self, player):
        '''Finds the most dangerous and most rewarding player. This is
        calculated as a function of the size difference and the proximity, and
        is used to determine where a CPU player will move. It returns a tuple
        of tuples, where the first tuple is the most dangerous player and the
        danger, and the second tuple is the most rewardin target and the
        reward'''
        danger = 0
        danger_blob = None
        reward = 0
        reward_blob = None
        x, y = player.get_absolute_position()
        total_players = [p for p in self.other_players]
        total_players.append(self.user)
        for p in total_players:
            if Game_Frame.is_player_in_range(player, p, 300):
                for other_b in p.blobs:
                    for my_b in player.blobs:
                        if other_b > my_b:
                            px, py = other_b.get_absolute_position()
                            d = max(2, my_b.r * math.pow(
                                (other_b.r - my_b.r), 2) /
                                max(0.1, math.hypot(px - x, py - y)))
                            if(d > danger):
                                danger = d
                                danger_blob = other_b
                        elif other_b < my_b:
                            px, py = other_b.get_absolute_position()
                            r = max(2, my_b.r * math.pow((
                                other_b.r - my_b.r), 2) /
                                max(0.1, math.hypot(px - x, py - y)))
                            if(r > reward):
                                reward = r
                                reward_blob = other_b
        return (danger_blob, danger), (reward_blob, reward)

    def move_CPU(self, player):
        '''Moves the CPU player based on the danger and reward of the other
        players in its sight, as well as the nearest food.'''
        # find other players in the player's "sight"
        movement_vector = None
        (d, d_value), (r, r_value) = self.danger_reward(player)
        (f, f_value) = self.best_food(player, 300)
        if d is None and f is None and r is None:
            movement_vector = (2 * random() - 1, 2 * random() - 1)
        # If danger is greater than reward
        if d_value == max(d_value, r_value, f_value):
            movement_vector = numpy.subtract(player.get_absolute_position(),
                                             d.get_absolute_position())
            # if nearing edge, dont go into edge
            x, y = player.get_absolute_position()
            if x <= 2 * player.r:
                movement_vector = numpy.add(
                    GameObject.normalize(movement_vector), (1, 0))
            elif x >= GAME_WIDTH - 2 * player.r:
                movement_vector = numpy.add(
                    GameObject.normalize(movement_vector), (-1, 0))
            if y <= 2 * player.r:
                movement_vector = numpy.add(
                    GameObject.normalize(movement_vector), (0, 1))
            elif y >= GAME_HEIGHT - 2 * player.r:
                movement_vector = numpy.add(
                    GameObject.normalize(movement_vector), (0, -1))
        # if reward is greater than danger
        elif r_value == max(d_value, r_value, f_value):
            movement_vector = numpy.subtract(r.get_absolute_position(),
                                             player.get_absolute_position())
        # otherwise, find nearest food
        elif f_value == max(d_value, r_value, f_value):
            movement_vector = numpy.subtract(f.get_absolute_position(),
                                             player.get_absolute_position())
        # add some randomness to movement
        vx, vy = movement_vector
        vx = random.gauss(vx, vx / 10)
        vy = random.gauss(vy, vy / 10)
        pos = player.get_absolute_position()
        movement_vector = Game_Frame.trim_position((vx, vy), pos)
        player.move(movement_vector)

    def best_food(self, player, sight_factor):
        '''Computes the closest piece of food to a player, used in CPU
        movement'''
        grids = Game_Frame.get_grids_in_sight(sight_factor, player)
        px, py = player.get_absolute_position()
        min_dist = sight_factor * math.sqrt(2)
        min_food = None
        for i in grids:
            for f in self.food_pieces[i]:
                if Game_Frame.is_player_in_range(player, f, 300):
                    fx, fy = f.get_absolute_position()
                    distance = math.hypot(fx - px, fy - py)
                    if(distance < min_dist):
                        min_dist = distance
                        min_food = f
        if min_food is None:
            return (None, 0)
        return (min_food, 1 / max(min_dist, 1))

    @staticmethod
    def is_player_in_range(player1, player2, sight_factor):
        '''Determines if player 2 is within the sight range of player 1'''
        p1x, p1y = player1.get_absolute_position()
        p2x, p2y = player2.get_absolute_position()
        return ((p1x - sight_factor <= p2x - player2.r or
                p1x + sight_factor >= p2x + player2.r) and
                (p1y - sight_factor <= p2y - player2.r or
                p2y + sight_factor >= p2y + player2.r))

    @staticmethod
    def get_grids_in_sight(sight_factor, player):
        '''Gets the grids within sight of a player - will always be of size
        1-4'''
        x, y = player.get_absolute_position()
        to_return = set()
        topLeft = find_grid(x - sight_factor, y - sight_factor)
        topRight = find_grid(x + sight_factor, y - sight_factor)
        bottomLeft = find_grid(x - sight_factor, y + sight_factor)
        ctr = 0
        while(topLeft + ctr <= bottomLeft):
            for i in range(topLeft + ctr, topRight + 1 + ctr):
                to_return.add(i)
            ctr += 4
        return list(to_return)


if __name__ == '__main__':
    app = wx.App()
    frm = Game_Frame(None, title='Agario')
    app.MainLoop()
