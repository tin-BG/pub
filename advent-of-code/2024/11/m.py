import sys
import re
from colorama import Fore, Style

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.abc import RichRenderable

console = Console()

def printc(s, color=Fore.CYAN) -> None:
	print(f"{color}{s}{Style.RESET_ALL}")

def combine_dict(a: dict, b: dict, n: int=1) -> dict:
	if b is None:
		return None
	r = a.copy()

	for k, v in b.items():
		if k not in r:
			r[k] = 0
		r[k] += v * n
	return r

#### <VIZ> ####
class VizData:
	def __init__(self, init_stones: list, iterations: int):
		self.stones = init_stones
		self.iterations = self.text_style(iterations, 'bold magenta')
		self.results = 0
		self.s_i = 0
		self.sm_l = 0
		self.rm_l = 0
		self.cur_search = ''
		self.last_insert = ''

	def set_stone(self, i: int=None) -> None:
		i = i or self.s_i
		self.stones[i] = self.text_style(self.stones[i], 'bold bright_green')

	def reset_stone(self, i: int=None) -> None:
		i = i or self.s_i
		self.stones[i] = self.text_reset(self.stones[i])

	def next_stone(self) -> None:
		self.reset_stone()
		self.s_i += 1

	def update_res(self, c: int) -> None:
		self.results += c
		# for i, s in enumerate(self.results):
		# 	self.results[i] = self.text_reset(s)
		# for s, n in stones.items():
		# 	self.results += [self.text_style(s, 'green3')] * n

	def create_table(self) -> Table:
		table = Table(title=self.text_style('Plutonian Pebbles'), box=None)
		table.add_column('Parameters')
		table.add_column('Values')
		table.add_row('Init.', f"[ {' '.join(self.stones)} ]")
		table.add_row('# Blinkings', self.iterations)
		table.add_row()
		table.add_row('Current Search', self.cur_search)
		table.add_row('Last Cached', self.last_insert)
		# table.add_row('Res.', f"[ {' '.join(self.results)} ]")
		table.add_row('# Stones in Results', f"[dark_slate_gray2]{self.results}[/dark_slate_gray2]")
		table.add_row()
		table.add_row('Cached Results', f"{self.sm_l}")
		table.add_row('Memoified Tree', f"{self.rm_l}")
		return table

	def update_last_insert(self, stone: str, results: dict, i: int) -> None:
		# self.last_insert = f"[royal_blue1]{stone}[/royal_blue1] [deep_pink4]#{i}[/deep_pink4] [ "
		# for s, n in results.items():
		# 	self.last_insert += f"{s}[{n}] "
		# self.last_insert += ']'
		c_stones = 0
		for n in results.values():
			c_stones += n
		self.last_insert = f"[deep_pink4]#{i:02}[/deep_pink4] [royal_blue1]{stone}[/royal_blue1] -> [dark_slate_gray2]{ c_stones }[/dark_slate_gray2] Stones "

	def update_cur_search(self, stone: str, i: int) -> None:
		self.cur_search = f"[deep_pink4]#{i:02}[/deep_pink4] [royal_blue1]{stone}[/royal_blue1]"

	@staticmethod
	def text_style(text: str, style:str=None) -> str:
		return f"[{style}]{text}[/{style}]" if style else text

	@staticmethod
	def text_reset(text: str) -> str:
		m = re.search(r'\](.+)\[', text)
		if m is not None:
			return m.group(1)
		return text

	def draw(self) -> RichRenderable:
		table = self.create_table()
		return table
#### </VIZ> ####

class Stones:
	def __init__(self, t: str, c: int):
		self.stones_array = t.split()
		self.stones = self.init_stones(self.stones_array)
		self.loop_max = c
		self.resmap = {}
		self.stonemap = {}
		self.stonemap_l = 0
		self.resmap_l = 0
		self.t_loop = None
		self.total = 0
		self.live = None
		self.vdata = VizData(self.stones_array, self.loop_max)

	#### <VIZ> ####
	def update_viz(self) -> None:
		panel = self.vdata.draw()
		self.live.update(panel)
		self.live.refresh()
	#### </VIZ> ####

	def init_stones(self, lstones: list) -> dict:
		stones = {}
		for s in lstones:
			if s not in stones:
				stones[s] = 0
			stones[s] += 1
		return stones

	def init_resmap(self, stone: str) -> None:
		self.resmap[stone] = [None] * (self.loop_max + 1)
		self.resmap[stone][0] = {stone: 1}
		#### <VIZ> ####
		self.resmap_l += 1
		self.vdata.rm_l = self.resmap_l
		self.update_viz()
		#### </VIZ> ####

	def get_stone_max_loop(self, stone: str, start: int) ->  (int, dict):
		for i in range(start, -1, -1):
			if self.resmap[stone][i] is not None:
				return i, self.resmap[stone][i]
		return 0, {stone: 1}

	@staticmethod
	def count_stones(stones: str) ->  int:
		t = 0
		for p in stones.values():
			t += p
		return t

	def count_resmap(self) ->  int:
		t = 0
		for a in self.resmap.values():
			t += len([e for e in a if e is not None])
		return t

	@staticmethod
	def lenven(stone: str) ->  dict:
		if len(stone) % 2:
			return None
		hlen = len(stone) // 2
		a = f"{int(stone[:hlen])}"
		b = f"{int(stone[hlen:])}"
		return {a: 1, b: 1} if a != b else {a: 2}

	def blink_stone(self, stone: str) ->  dict:
		if stone == '0':
			return {'1': 1}
		if (is_lenven := self.lenven(stone)) is not None:
			return is_lenven
		return {f"{int(stone) * 2024}": 1}

	def iterate_stone(self, stone: str) ->  dict:
		if stone in self.stonemap:
			return self.stonemap[stone]
		r = self.blink_stone(stone)
		self.stonemap[stone] = r
		#### <VIZ> ####
		self.stonemap_l += 1
		self.vdata.sm_l = self.stonemap_l
		self.update_viz() # VIZ
		#### </VIZ> ####
		return r

	def dfs_check_new_stone(self, stone: str) ->  dict:
		if stone in self.stonemap:
			return self.stonemap[stone]
		if stone in self.resmap and self.resmap[stone][1] is not None:
			return self.resmap[stone][1]
		return None

	def recheck_map(self, stone: str, res: dict, i: int) ->  None:
		c = {}
		for p, n in res.items():
			t = self.dfs_check_new_stone(p)
			c = combine_dict(c, t, n)
			if c is None:
				return
		if c is not None:
			if i >= len(self.resmap[stone]):
				self.resmap[stone].append(None)
			self.dfs_update(stone, c, i)

	def dfs_update(self, stone: str, res: dict, i: int) ->  bool:
		if stone not in self.resmap:
			self.init_resmap(stone)
		if self.resmap[stone][i] is None:
			#### <VIZ> ####
			self.resmap_l += 1
			self.vdata.rm_l = self.resmap_l
			self.vdata.update_last_insert(stone, res, i)
			self.update_viz()
			#### </VIZ> ####
			self.resmap[stone][i] = res
			return True
		return False

	def blink_update(self, stone: str, res: dict, i: int) ->  None:
		updated = self.dfs_update(stone, res, i)
		if updated:
			self.recheck_map(stone, res, i + 1)

	def dfs_blink(self, stone: str, pebbles: dict, i: int) ->  None:
		blinks = {}
		for pebble, n in pebbles.items():
			#### <VIZ> ####
			self.vdata.update_cur_search(pebble, i)
			self.update_viz()
			#### </VIZ> ####
			blinked = self.iterate_stone(pebble)
			self.blink_update(pebble, blinked, 1)
			blinks = combine_dict(blinks, blinked, n)
		self.blink_update(stone, blinks, i)
		if self.resmap[stone][self.loop_max] is None:
			self.dfs_blink(stone, blinks, i + 1)

	def dfs_stone(self, stone: str) ->  None:
		i, pebbles = self.get_stone_max_loop(stone, self.loop_max)
		self.dfs_blink(stone, pebbles, i + 1)

	def dfs_stone_init(self, stone: str) ->  None:
		if stone not in self.resmap:
			self.init_resmap(stone)
		self.dfs_stone(stone)

	def check_total(self):
		total = {}
		for s, n in self.stones.items():
			p = self.resmap[s][self.loop_max]
			total = combine_dict(total, p, n)
		return total

	def run(self):
		with Live(console=console, auto_refresh=False) as live:
			self.live = live
			for s in self.stones:
				self.vdata.set_stone() ### VIZ
				self.dfs_stone_init(s)
				#### <VIZ> ####
				self.vdata.update_res(self.count_stones(self.resmap[s][self.loop_max]))
				self.vdata.next_stone()
				self.update_viz()
				#### </VIZ> ####
			#### <VIZ> ####
			self.update_viz()
			#### </VIZ> ####
			# total = self.check_total()
			# printc(self.count_stones(total))

def load_input(default_file='input.txt'):
	fp = sys.argv[1] if len(sys.argv) > 1 else default_file
	loop = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isnumeric() else 1
	with open(fp, 'r', encoding='utf-8') as f:
		contents = f.read()
	return contents, loop

# def is_lenven(s):
# 	return not len(s) & 1

# def split_num(s):
# 	p = len(s) // 2
# 	a, b = s[:p], f"{int(s[p:])}"
# 	return a,b

def ex():
	t, c = load_input()
	stones = Stones(t, c)
	stones.run()
	### ↓ ↓ ↓ OLD CODE ↓ ↓ ↓ ####
	# s = t.split()
	# for n in range(c):
	# 	print(f"Loop #{n}:")
	# 	l = len(s)
	# 	i = 0
	# 	while i < l:
	# 		if s[i] == '0':
	# 			# print(f"{s[i]} -> 1")
	# 			s[i] = '1'
	# 		elif is_lenven(s[i]):
	# 			x, y = split_num(s[i])
	# 			# print(f"{s[i]} -> {x}, {y}")
	# 			s[i] = y
	# 			s.insert(i, x)
	# 			i += 1
	# 			l += 1
	# 		else:
	# 			# print(f"{s[i]} -> {int(s[i]) * 2024}")
	# 			s[i] = f"{int(s[i]) * 2024}"
	# 		i += 1
	# 	# print(s)
	# # print(s)
	# print(len(s))

if __name__ == '__main__':
	ex()
