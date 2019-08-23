#-*- coding:utf-8 -*-


import curses
from random import randrange, choice
from collections import defaultdict
import numpy as np


actions = ['Up', 'Left', 'Down', 'Right', 'Restart', 'Exit']
letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
actions_dict = dict(zip(letter_codes, actions * 2))


def get_user_action(keyboard):
    char = "N"
    while char not in actions_dict:
        char = keyboard.getch()
    return actions_dict[char]


#对于行列相等的二维list做zip想当于转置了原list
def transpose(field):
    return [list(row) for row in zip(*field)]


#每一行逆序，相当于整个棋盘做一个左右镜像变换
def invert(field):
    return [row[::-1] for row in field]


class GameField(object):
    def __init__(self, height=4, width=4, win=2048):
        self.height = height
        self.width = width
        self.win_value = 2048
        self.score = 0
        self.highscore = 0
        self.reset()

    def reset(self):
        if self.score > self.highscore:
            self.highscore = self.score
        self.score = 0
        # self.field = [[0 for i in range(self.width)] for j in range(self.height)]
        # self.field = [[0] * self.width] * self.height
        self.field = np.zeros((self.height, self.width), dtype=np.int)
        self.spawn()
        self.spawn()

    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2       #4跟2按照1:9的概率比出现，2以九成概率被初始化
        i, j = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    def move(self, direction):
        def move_row_left(row):
            def tighten(row):
                new_row = [i for i in row if i]
                new_row += [0] * (len(row) - len(new_row))
                return new_row

            def merge(row):
                pair = False
                new_row = []
                for i in range(len(row)):
                    if pair:
                        new_row.append(2 * row[i])
                        self.score += 2 * row[i]
                        pair = False
                    else:
                        if i + 1 < len(row) and row[i] == row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(row[i])
                assert len(new_row) == len(row)
                return new_row
            return tighten(merge(tighten(row)))

        moves = {}
        moves['Left'] = lambda field: [move_row_left(row) for row in field]
        moves['Right'] = lambda field: invert(moves['Left'](invert(field)))
        moves['Up'] = lambda field: transpose(moves['Left'](transpose(field)))
        moves['Down'] = lambda field: transpose(moves['Right'](transpose(field)))

        if direction in moves:
            if self.move_is_possible(direction):
                self.field = moves[direction](self.field)
                self.spawn()
                return True
            else:
                return False

    def is_win(self):
        return any(any(i >= self.win_value for i in row) for row in self.field)

    def is_gameover(self):
        return not any(self.move_is_possible(move) for move in actions)

    def move_is_possible(self, direction):
        #判断一行能否移动，以左移为基础，其他转置或者逆矩阵可以得到
        def row_is_left_movable(row):
            def change(i):
                if row[i] == 0 and row[i + 1] != 0:        #情况一：该位置为初始值0，右边的相邻位置不为0
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:        #情况二：某位置跟右边相邻位置值相等（最右边两个都是0的情况需要排除）
                    return True
                return False

            return any(change(i) for i in range(len(row) - 1))

        check = {}
        check['Left'] = lambda field: any(row_is_left_movable(row) for row in field)
        check['Right'] = lambda field: check['Left'](invert(field))
        check['Up'] = lambda field: check['Left'](transpose(field))
        check['Down'] = lambda field: check['Right'](transpose(field))
        if direction in check:
            return check[direction](self.field)
        else:
            return False

    def draw(self, screen):
        help_string1 = '(W)Up (S)Down (A)Left (D)Right'
        help_string2 = '     (R)Restart (Q)Exit'
        gameover_string = '           GAME OVER'
        win_string = '           YOU WIN'

        def cast(string):
            screen.addstr(string + '\n')

        # 绘制水平分割线
        def draw_horizon_separation():
            line = '+' + ('+------' * self.width + '+')[1:]
            separator = defaultdict(lambda: line)
            if not hasattr(draw_horizon_separation, "counter"):
                draw_horizon_separation.counter = 0
            cast(separator[draw_horizon_separation.counter])
            draw_horizon_separation.counter += 1

        def draw_row(row):
            cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')

        screen.clear()
        cast('SCORE: ' + str(self.score))
        if 0 != self.highscore:
            cast('HIGHSCORE: ' + str(self.highscore))

        for row in self.field:
            draw_horizon_separation()
            draw_row(row)

        draw_horizon_separation()
        if self.is_win():
            cast(win_string)
        else:
            if self.is_gameover():
                cast(gameover_string)
            else:
                cast(help_string1)
        cast(help_string2)


def main(stdscr):
    def init():
        #重置游戏棋盘
        game_field.reset()
        return 'Game'
    
    def not_game(state):
        #画出GameOver或者Win的界面
        game_field.draw(stdscr)
        #读取用户输入得到action，判断是重启游戏还是结束游戏
        action = get_user_action(stdscr)
        responses = defaultdict(lambda: state)
        responses['Restart'], responses['Exit'] = 'Init', 'Exit'
        return responses[action]
    
    def game():
        #画出当前棋盘状态
        game_field.draw(stdscr)
        #从用户输入得到action
        action = get_user_action(stdscr)

        if action == 'Restart':
            return 'Init'
        if action == 'Exit':
            return 'Exit'
        if game_field.move(action):
            if game_field.is_win():
                return 'Win'
            if game_field.is_gameover():
                return 'Gameover'
        return 'Game'

    state_action = {
            'Init': init,
            'Win': lambda: not_game('Win'),
            'Gameover': lambda: not_game('Gameover'),
            'Game': game
    }

    curses.use_default_colors()
    game_field = GameField(win=2048)

    state = 'Init'
    #状态机开始循环
    while state != 'Exit':
        state = state_action[state]()


curses.wrapper(main)




            


     
