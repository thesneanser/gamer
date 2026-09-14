import pygame
import numpy as np
import math
import os

WIDTH = 800
HEIGHT = 600
WINDOW_TITLE = ""
FRAME_RATE = 100

STARTING_CREDITS = 14
STARTING_DEADLINE_COST = 75
STARTING_SPINS = 5
STARTING_ROUNDS = 3
SPIN_COST = 0
HIGHLIGHT_DURATION = 0.35
JACKPOT_HIGHLIGHT_SPEED = 0.50

GRID_COLS = 5
GRID_ROWS = 3
GRID_SPACING_X = 70
GRID_SPACING_Y = 60
GRID_CENTER_X = 370
GRID_CENTER_Y = 300
GRID_X = GRID_CENTER_X - ((GRID_COLS - 1) * GRID_SPACING_X / 2) + np.arange(GRID_COLS) * GRID_SPACING_X
GRID_Y = GRID_CENTER_Y - ((GRID_ROWS - 1) * GRID_SPACING_Y / 2) + np.arange(GRID_ROWS) * GRID_SPACING_Y

pygame.init()
display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)

clock = pygame.time.Clock()
running = True


cheats_enabled = True


handle = pygame.Rect(100, 100, 50, 50)
dragging = False
drag_offset = (0, 0)
current_screen = 1
Aspin = False
wait_spin = 0
current_credits = STARTING_CREDITS
input_debt_amount = 1
debt_credits = 0
current_deadline_cost = STARTING_DEADLINE_COST
debug_overlay = False
spin_active = False
spin_progress = 0.1
spin_frame = 0
highlighted_positions = set()
highlight_timer = 0.0
highlight_sequence = []
highlight_pattern_names = []
highlight_index = 0
current_highlight_duration = HIGHLIGHT_DURATION
jackpot_highlight_speed = JACKPOT_HIGHLIGHT_SPEED
remain_spins = STARTING_SPINS
spin_cost = SPIN_COST
remain_round = STARTING_ROUNDS
symbol_matrix = [[], [], []]

asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


# symbols
JB = "JB"
TM = "TM"
LH = "LH"
ZS = "ZS"
AS = "AS"
ID = "ID"
RT = "RT"

# weights
JBW = 194
TMW = 194
LHW = 149
ZSW = 149
ASW = 119
IDW = 119
RTW = 75

symbols = [JB, TM, LH, ZS, AS, ID, RT]
weights = [JBW, TMW, LHW, ZSW, ASW, IDW, RTW]
symbol_values = {
	JB: 2,
	TM: 2,
	LH: 3,
	ZS: 3,
	AS: 5,
	ID: 5,
	RT: 7,
}
pattern_multipliers = {
	"HOR": 1,
	"VERT": 1,
	"DIAG": 1,
	"HOR-L": 2,
	"HOR-XL": 3,
	"ZIG": 4,
	"ZAG": 4,
	"ABOVE": 7,
	"BELOW": 7,
	"EYE": 8,
	"JACKPOT": 10,
}
score_multiplier = 1
pattern_score_multiplier = 1
symbol_colours = {
	JB: (50, 50, 50),
	TM: (150, 50, 50),
	LH: (100, 150, 50),
	ZS: (150, 150, 150),
	AS: (50, 150, 150),
	ID: (50, 50, 150),
	RT: (50, 50, 20),
}

cheat_fields = [
	("score", None),
	("pattern_score", None),
	*(("chance", symbol) for symbol in symbols),
	*(("symbol_value", symbol) for symbol in symbols),
	*(("pattern", pattern_name) for pattern_name in pattern_multipliers),
]
cheat_selected_field = 0
cheat_input_active = False
cheat_input_text = ""


def get_cheat_value(field):
	field_type, key = field
	if field_type == "score":
		return score_multiplier
	if field_type == "pattern_score":
		return pattern_score_multiplier
	if field_type == "chance":
		return weights[symbols.index(key)]
	if field_type == "symbol_value":
		return symbol_values[key]
	return pattern_multipliers[key]


def set_cheat_value(field, value):
	global score_multiplier, pattern_score_multiplier
	field_type, key = field
	value = max(0, int(value))
	if field_type == "score":
		score_multiplier = value
	elif field_type == "pattern_score":
		pattern_score_multiplier = value
	elif field_type == "chance":
		weights[symbols.index(key)] = value
	elif field_type == "symbol_value":
		symbol_values[key] = value
	else:
		pattern_multipliers[key] = value


def load_symbol_image(symbol):
	candidate_names = [
		f"{symbol.lower()}.png",
		f"{symbol}.png",
		f"{symbol.lower()}.jpg",
		f"{symbol}.jpg",
	]
	for file_name in candidate_names:
		path = os.path.join(asset_dir, file_name)
		if os.path.exists(path):
			image = pygame.image.load(path).convert_alpha()
			return image

	fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
	pygame.draw.circle(fallback, symbol_colours[symbol], (25, 25), 22)
	pygame.draw.circle(fallback, (255, 255, 255, 120), (25, 25), 22, 2)
	return fallback


symbol_images = {symbol: load_symbol_image(symbol) for symbol in symbols}

patterns = {
	"JACKPOT": [[(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]],
	"EYE": [[(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 3), (1, 4), (2, 1), (2, 2), (2, 3)]],
	"ABOVE": [[(0, 2), (1, 1), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)]],
	"BELOW": [[(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 3), (2, 2)]],
	"ZIG": [[(0, 2), (1, 1), (1, 3), (2, 0), (2, 4)]],
	"ZAG": [[(0, 0), (0, 4), (1, 1), (1, 3), (2, 2)]],
	"HOR-XL": [[(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)], [(1, 0), (1, 1), (1, 2), (1, 3), (1, 4)], [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]],
	"HOR-L": [[(0, 0), (0, 1), (0, 2), (0, 3)],[(1, 0), (1, 1), (1, 2), (1, 3)],[(2, 0), (2, 1), (2, 2), (2, 3)],[(2, 1), (2, 2), (2, 3), (2, 4)],[(1, 1), (1, 2), (1, 3), (1, 4)],[(0, 1), (0, 2), (0, 3), (0, 4)]],
	"DIAG": [[(0, 0), (1, 1), (2, 2)],[(0, 1), (1, 2), (2, 3)],[(0, 2), (1, 3), (2, 4)],[(0, 4), (1, 3), (2, 2)],[(0, 3), (1, 2), (2, 1)],[(0, 2), (1, 1), (2, 0)]],
	"VERT": [[(0, 0), (1, 0), (2, 0)],[(0, 1), (1, 1), (2, 1)],[(0, 2), (1, 2), (2, 2)],[(0, 3), (1, 3), (2, 3)],[(0, 4), (1, 4), (2, 4)]],
	"HOR": [[(0, 0), (0, 1), (0, 2)],[(2, 0), (2, 1), (2, 2)],[(1, 1), (1, 2), (1, 3)],[(1, 0), (1, 1), (1, 2)],[(0, 1), (0, 2), (0, 3)],[(2, 1), (2, 2), (2, 3)],[(0, 2), (0, 3), (0, 4)],[(1, 2), (1, 3), (1, 4)],[(2, 2), (2, 3), (2, 4)]]
}



class Button:
	def __init__(self, x, y, width, height, text):
		self.rect = pygame.Rect(x, y, width, height)
		self.text = text
		self.font = pygame.font.Font(None, 32)
		self.click_highlight_frames = 0

	def draw(self, screen, mouse_position):
		if self.click_highlight_frames > 0:
			colour = (255, 220, 80)
			self.click_highlight_frames -= 1
		elif self.rect.collidepoint(mouse_position):
			colour = (150, 150, 150)
		else:
			colour = (100, 100, 100)

		pygame.draw.rect(screen, colour, self.rect)

		text = self.font.render(self.text, True, (255, 255, 255))
		text_rect = text.get_rect(center=self.rect.center)

		screen.blit(text, text_rect)

	def clicked(self, position):
		if self.rect.collidepoint(position):
			self.click_highlight_frames = 8
			return True
		return False


def draw_debug_overlay(surface, symbol_matrix):
	font = pygame.font.Font(None, 22)
	lines = [
		f"screen: {current_screen}",
		f"credits: {current_credits}  debt: {debt_credits}",
		f"spins: {remain_spins}  rounds: {remain_round}",
		f"spin: {spin_active}  progress: {spin_progress:.2f}",
		f"handle: ({handle.x}, {handle.y})",
		f"wait: {wait_spin:.1f}  Aspin: {Aspin}",
		f"matrix: {' '.join(''.join(row) for row in symbol_matrix)}",
		f"symbol values x{score_multiplier}",
		f"pattern values x{pattern_score_multiplier}",
		f"chances: {' '.join(f'{symbol}:{weights[index]}' for index, symbol in enumerate(symbols))}",
		f"symbol values: {' '.join(f'{symbol}:{symbol_values[symbol]}' for symbol in symbols)}",
		f"patterns: {' '.join(f'{name}:{value}' for name, value in pattern_multipliers.items())}",
	]
	padding = 8
	line_height = font.get_linesize()
	width = max(font.size(line)[0] for line in lines) + padding * 2
	height = line_height * len(lines) + padding * 2
	panel = pygame.Surface((width, height), pygame.SRCALPHA)
	panel.fill((0, 0, 0, 205))
	for index, line in enumerate(lines):
		text = font.render(line, True, (230, 240, 255))
		panel.blit(text, (padding, padding + index * line_height))
	surface.blit(panel, (WIDTH - width - 12, 12))


print_debt_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60, "Print Debt")
high_ticket = Button(220, 275, 150, 50, "3 Spins")
low_ticket = Button(430, 275, 150, 50, "7 Spins")

def find_matching_patterns(symbol_matrix):
	matches = []

	for pattern_name, pattern_variants in patterns.items():
		for positions in pattern_variants:
			pattern_symbols = [symbol_matrix[row][column] for row, column in positions]
			if len(set(pattern_symbols)) == 1:
				symbol = pattern_symbols[0]
				if pattern_name in ("JACKPOT") or symbol:
					match = (pattern_name, symbol, set(positions))
					matches.append(match)

	if any(pattern_name == "JACKPOT" for pattern_name, _, _ in matches):
		return [
			match for match in matches if match[0] != "JACKPOT"
		] + [
			match for match in matches if match[0] == "JACKPOT"
		]

	return [
		match for match in matches
		if not any(
			len(other_match[2]) > len(match[2])
			and match[2].issubset(other_match[2])
			and not (
				{
					match[0], other_match[0]
				}
				in (
					{"HOR-XL", "ABOVE"},
					{"HOR-XL", "BELOW"},
					{"DIAG", "HOR-XL"},
					{"DIAG", "ABOVE"},
					{"DIAG", "BELOW"},
				)
			)
			for other_match in matches
		)
	]


def calculate_score(matches):
	adjusted_symbol_values = {
		symbol: value * score_multiplier
		for symbol, value in symbol_values.items()
	}
	adjusted_pattern_multipliers = {
		pattern_name: value * pattern_score_multiplier
		for pattern_name, value in pattern_multipliers.items()
	}
	return sum(
		adjusted_symbol_values[symbol] * adjusted_pattern_multipliers[pattern_name]
		for pattern_name, symbol, _ in matches
	)

def draw_slot_symbol(surface, symbol, x, y, highlight_strength=0.0, size=0.50):
	image = symbol_images[symbol]

	pulse_strength = max(0.0, min(1.0, highlight_strength))
	symbol_size = max(12, int(100 * size * (1.0 + 0.12 * pulse_strength)))

	scaled_image = pygame.transform.smoothscale(
		image,
		(symbol_size, symbol_size)
	)

	rect = scaled_image.get_rect(center=(x, y))

	surface.blit(scaled_image, rect)

	if highlight_strength > 0:
		lightened = scaled_image.copy()
		lightened.fill(
			(
				int(110 * highlight_strength),
				int(110 * highlight_strength),
				int(110 * highlight_strength),
				0
			),
			special_flags=pygame.BLEND_RGBA_ADD
		)
		surface.blit(lightened, rect)


def main():
	global running, dragging, handle, current_screen, Aspin, wait_spin, symbol_matrix, spin_active, spin_progress, spin_frame, highlighted_positions, highlight_timer, highlight_sequence, highlight_pattern_names, highlight_index, current_highlight_duration, jackpot_highlight_speed, current_credits, input_debt_amount, debt_credits, current_deadline_cost, remain_spins, spin_cost, remain_round, debug_overlay, cheat_selected_field, cheat_input_active, cheat_input_text

	while running:
		mx, my = pygame.mouse.get_pos()
		if wait_spin > 0:
			wait_spin -= 0.1
		if wait_spin < 0:
			wait_spin = 0
		if highlight_timer > 0:
			highlight_timer -= 0.01
			if highlight_timer <= 0:
				highlight_index += 1
				if highlight_index < len(highlight_sequence):
					highlighted_positions = highlight_sequence[highlight_index]
					if highlight_pattern_names[highlight_index] == "JACKPOT":
						current_highlight_duration = HIGHLIGHT_DURATION / jackpot_highlight_speed
					else:
						current_highlight_duration = max(0.12, current_highlight_duration * 0.9)
					highlight_timer = current_highlight_duration
				else:
					highlighted_positions = set()
					highlight_sequence = []
					highlight_pattern_names = []

		if spin_active:
			spin_frame += 1
			if spin_frame % 2 == 0:
				symbol_weights = np.array(weights, dtype=float)
				symbol_matrix = [
					list(np.random.choice(symbols, size=5, p=symbol_weights / symbol_weights.sum()))
					for _ in range(3)
				]
			spin_progress += 0.02
			if spin_progress >= 1.0:
				spin_progress = 1.0
				spin_active = False
				Aspin = False
				wait_spin = 10
				matches = find_matching_patterns(symbol_matrix)
				highlight_sequence = [positions for _, _, positions in matches]
				highlight_pattern_names = [pattern_name for pattern_name, _, _ in matches]
				highlight_index = 0
				highlighted_positions = highlight_sequence[0] if highlight_sequence else set()
				current_highlight_duration = HIGHLIGHT_DURATION / jackpot_highlight_speed if matches and matches[0][0] == "JACKPOT" else HIGHLIGHT_DURATION
				highlight_timer = current_highlight_duration if matches else 0.0
				if matches:
					score = calculate_score(matches)
					current_credits += score
					print("Matches:", ", ".join(f"{pattern_name} ({symbol})" for pattern_name, symbol, _ in matches))
					print(f"Score: {score} credits. Total credits: {current_credits}")
				else:
					print("Matches: none")
		else:
			spin_progress = 0.0

		

	#--------------------slot screen--------------------
		if current_screen == 1:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
					debug_overlay = not debug_overlay
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] > 700:
						current_screen = 2
						dragging = False

					if remain_spins == 0 and Aspin and not spin_active:
						if high_ticket.clicked(event.pos):
							remain_spins = 3
							current_credits -= spin_cost
							remain_round -= 1
						if low_ticket.clicked(event.pos):
							remain_spins = 7
							current_credits -= spin_cost
							remain_round -= 1

					if handle.collidepoint(event.pos):
						dragging = True
						drag_offset = (handle.x - event.pos[0], handle.y - event.pos[1])
				elif event.type == pygame.MOUSEBUTTONUP:
					dragging = False
				elif event.type == pygame.MOUSEMOTION and dragging and remain_spins > 0:
					handle.x = event.pos[0] + drag_offset[0]
					handle.y = event.pos[1] + drag_offset[1]


			handle.x = WIDTH // 1.25

			if handle.y > 400:
				handle.y = 400

			elif handle.y < 150:
				handle.y = 150

			elif handle.y > 150 and not dragging:
				handle.y -= 3

			elif handle.y < 200:
				if wait_spin == 0:
					Aspin = True

			elif handle.y > 375 and Aspin and not spin_active:
				symbol_weights = np.array(weights, dtype=float)
				symbol_matrix = [
					list(np.random.choice(symbols, size=5, p=symbol_weights / symbol_weights.sum()))
					for _ in range(3)
				]
				spin_active = True
				spin_progress = 0.0
				spin_frame = 0
				highlighted_positions = set()
				highlight_timer = 0.0
				highlight_sequence = []
				highlight_index = 0
				current_highlight_duration = HIGHLIGHT_DURATION
				Aspin = False
				remain_spins -= 1

			display.fill((30, 30, 30))

			pygame.draw.circle(display, (70, 160, 255), (handle.x + handle.width // 2, handle.y + handle.height // 2), handle.width // 2)

			for row, column_symbols in enumerate(symbol_matrix):
				for column, symbol in enumerate(column_symbols):
					base_x = GRID_X[column]
					base_y = GRID_Y[row]
					highlight_progress = (current_highlight_duration - highlight_timer) / current_highlight_duration
					if (row, column) in highlighted_positions:
						if highlight_progress < 0.25:
							highlight_strength = highlight_progress / 0.25
						elif highlight_progress < 0.75:
							highlight_strength = 1.0
						else:
							highlight_strength = (1.0 - highlight_progress) / 0.25
					else:
						highlight_strength = 0.0
					if spin_active:
						draw_slot_symbol(display, symbol, base_x, base_y, 0)
					else:
						draw_slot_symbol(display, symbol, base_x, base_y, highlight_strength=highlight_strength)

			if remain_spins == 0 and Aspin and not spin_active:
				matrix_panel = pygame.Rect(180, 190, 440, 220)
				pygame.draw.rect(display, (0, 0, 0), matrix_panel)
				pygame.draw.rect(display, (120, 120, 120), matrix_panel, 2)
				high_ticket.draw(display, (mx, my))
				low_ticket.draw(display, (mx, my))

			if debug_overlay:
				draw_debug_overlay(display, symbol_matrix)

			pygame.display.flip()
			clock.tick(FRAME_RATE)


		def draw_cheat_page(surface, mouse_position):
			surface.fill((24, 28, 38))
			title_font = pygame.font.Font(None, 38)
			label_font = pygame.font.Font(None, 26)
			small_font = pygame.font.Font(None, 22)
			selected_colour = (255, 210, 80)
			text_colour = (235, 240, 250)

			title = title_font.render("CHEAT PAGE", True, text_colour)
			surface.blit(title, (40, 20))
			instructions = small_font.render("Click a value, type a number, then press Enter. Esc cancels.", True, (170, 180, 195))
			surface.blit(instructions, (40, 52))

			selected_field = cheat_fields[cheat_selected_field]
			if cheat_input_active:
				selected_text = cheat_input_text or "_"
			else:
				selected_text = str(get_cheat_value(selected_field))
			multiplier_text = label_font.render(f"Symbol value multiplier: {selected_text if selected_field[0] == 'score' else score_multiplier}", True, selected_colour if selected_field[0] == "score" else text_colour)
			surface.blit(multiplier_text, (40, 92))
			pattern_multiplier_text = label_font.render(f"Pattern value multiplier: {selected_text if selected_field[0] == 'pattern_score' else pattern_score_multiplier}", True, selected_colour if selected_field[0] == "pattern_score" else text_colour)
			surface.blit(pattern_multiplier_text, (40, 116))

			left_x = 40
			right_x = 430
			row_y = 140
			row_height = 34
			header = label_font.render("SYMBOLS", True, (120, 200, 255))
			surface.blit(header, (left_x, row_y))
			header = label_font.render("PATTERN MULTIPLIERS", True, (120, 200, 255))
			surface.blit(header, (right_x, row_y))

			for row, symbol in enumerate(symbols):
				y = row_y + 34 + row * row_height
				for field_type, label, value, x, width in (
					("chance", f"{symbol} chance", weights[row], left_x, 175),
					("symbol_value", f"{symbol} value", symbol_values[symbol], left_x + 190, 150),
				):
					field_index = cheat_fields.index((field_type, symbol))
					rect = pygame.Rect(x, y, width, 32)
					colour = (70, 75, 90) if field_index != cheat_selected_field else selected_colour
					pygame.draw.rect(surface, colour, rect)
					value_colour = (20, 24, 32) if field_index == cheat_selected_field else text_colour
					field_text = f"{label}: {value}"
					if field_index == cheat_selected_field and cheat_input_active:
						field_text = f"{label}: {cheat_input_text or '_'}"
					surface.blit(small_font.render(field_text, True, value_colour), (x + 8, y + 6))

			for row, pattern_name in enumerate(pattern_multipliers):
				y = row_y + 34 + row * row_height
				field_index = cheat_fields.index(("pattern", pattern_name))
				rect = pygame.Rect(right_x, y, 310, 32)
				colour = (70, 75, 90) if field_index != cheat_selected_field else selected_colour
				value_colour = (20, 24, 32) if field_index == cheat_selected_field else text_colour
				field_text = f"{pattern_name}: {pattern_multipliers[pattern_name]}"
				if field_index == cheat_selected_field and cheat_input_active:
					field_text = f"{pattern_name}: {cheat_input_text or '_'}"
				pygame.draw.rect(surface, colour, rect)
				surface.blit(small_font.render(field_text, True, value_colour), (right_x + 8, y + 6))

			back_text = label_font.render("< Back", True, text_colour)
			surface.blit(back_text, (700, 20))

	#--------------------debt screen--------------------
		if current_screen == 2:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
					debug_overlay = not debug_overlay
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] > 700:
						current_screen = 3
						dragging = False
					if event.pos[0] < 300:
						current_screen = 1
						dragging = False
					if print_debt_button.clicked(event.pos):
						if current_credits >= input_debt_amount:
							current_credits -= input_debt_amount
							debt_credits += input_debt_amount
							print(f"Debt printed. Remaining credits: {current_credits} Debt credits: {debt_credits}")
						else:
							print("Not enough credits to print debt.")

					if debt_credits == current_deadline_cost:
						remain_round = 3
						print(f"Deadline reached! You have {remain_round} spins remaining to pay off your debt.")
						current_deadline_cost *= 1.25
					if remain_spins == 0 and remain_round == 0 and debt_credits + current_credits < current_deadline_cost:
						print("Game Over! You failed to pay off your debt in time.")
						running = False



			display.fill((30, 90, 30))
			print_debt_button.draw(display, (mx, my))
			if debug_overlay and cheats_enabled:
				draw_debug_overlay(display, symbol_matrix)

			pygame.display.flip()
			clock.tick(FRAME_RATE)

	#-------------------charm buy screen--------------------
		if current_screen == 3:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
					debug_overlay = not debug_overlay
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] > 700:
						current_screen = 4
						dragging = False
					if event.pos[0] < 300:
						current_screen = 2
						dragging = False

			display.fill((90, 30, 30))
			if debug_overlay and cheats_enabled:
				draw_debug_overlay(display, symbol_matrix)

			pygame.display.flip()
			clock.tick(FRAME_RATE)

	#--------------------cheats--------------------
		if current_screen == 4 and cheats_enabled:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN and event.key == pygame.K_f:
					debug_overlay = not debug_overlay
				elif event.type == pygame.TEXTINPUT and cheat_input_active:
					cheat_input_text += "".join(character for character in event.text if character.isdigit())
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						cheat_input_active = False
						cheat_input_text = ""
					elif event.key == pygame.K_BACKSPACE and cheat_input_active:
						cheat_input_text = cheat_input_text[:-1]
					elif event.key == pygame.K_RETURN and cheat_input_active:
						if cheat_input_text:
							set_cheat_value(cheat_fields[cheat_selected_field], cheat_input_text)
						cheat_input_active = False
						cheat_input_text = ""
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] > 690 and event.pos[1] < 80:
						current_screen = 3
						dragging = False
						cheat_input_active = False
					elif pygame.Rect(40, 88, 360, 25).collidepoint(event.pos):
						cheat_selected_field = 0
						cheat_input_active = True
						cheat_input_text = ""
					elif pygame.Rect(40, 112, 360, 25).collidepoint(event.pos):
						cheat_selected_field = 1
						cheat_input_active = True
						cheat_input_text = ""
					else:
						for row, symbol in enumerate(symbols):
							y = 174 + row * 34
							for field_type, x, width in (("chance", 40, 175), ("symbol_value", 230, 150)):
								if pygame.Rect(x, y, width, 32).collidepoint(event.pos):
									cheat_selected_field = cheat_fields.index((field_type, symbol))
									cheat_input_active = True
									cheat_input_text = ""
						for row, pattern_name in enumerate(pattern_multipliers):
							y = 174 + row * 34
							if pygame.Rect(430, y, 310, 32).collidepoint(event.pos):
								cheat_selected_field = cheat_fields.index(("pattern", pattern_name))
								cheat_input_active = True
								cheat_input_text = ""

			draw_cheat_page(display, (mx, my))
			if debug_overlay and cheats_enabled:
				draw_debug_overlay(display, symbol_matrix)

			pygame.display.flip()
			clock.tick(FRAME_RATE)

	pygame.quit()


if __name__ == "__main__":
	main()