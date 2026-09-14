import pygame
import random
import math
import os

pygame.init()

WIDTH = 800
HEIGHT = 600
display = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("")

clock = pygame.time.Clock()
running = True

handle = pygame.Rect(100, 100, 50, 50)
dragging = False
drag_offset = (0, 0)
current_screen = 1
Aspin = False
wait_spin = 0
current_credits = 7
input_debt_amount = 1
debt_credits = 0
current_deadline_cost = 75


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
symbol_colours = {
	JB: (50, 50, 50),
	TM: (150, 50, 50),
	LH: (100, 150, 50),
	ZS: (150, 150, 150),
	AS: (50, 150, 150),
	ID: (50, 50, 150),
	RT: (50, 50, 20),
}

asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


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
symbol_matrix = [[], [], []]

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


print_debt_button = Button(WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60, "Print Debt")
high_ticket = Button(20, 20, 120, 50, "")
low_ticket = Button(20, 80, 120, 50, "")

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
	return sum(
		symbol_values[symbol] * pattern_multipliers[pattern_name]
		for pattern_name, symbol, _ in matches
	)

grid_x = [230, 300, 370, 440, 510]
grid_y = [240, 300, 360]
spin_active = False
spin_progress = 0.0
spin_frame = 0
highlighted_positions = set()
highlight_timer = 0.0
highlight_sequence = []
highlight_pattern_names = []
highlight_index = 0
highlight_duration = 0.35
jackpot_highlight_speed = 0.50
current_highlight_duration = highlight_duration
remain_spins = 5
spin_cost = 7
remain_round = 3


def draw_slot_symbol(surface, symbol, x, y, spin_amount, highlight_strength=0.0, size=0.35):
    image = symbol_images[symbol]

    pulse = 1.0 + 0.15 * math.sin(spin_amount * 16.0 + x * 0.08) + 0.1 * highlight_strength
    spin_rotation = spin_amount * 1080.0

    base_size = image.get_size()

    scaled_width = max(12, int(base_size[0] * pulse * size))
    scaled_height = max(12, int(base_size[1] * pulse * size))

    scaled_image = pygame.transform.smoothscale(
        image,
        (scaled_width, scaled_height)
    )

    rotated = pygame.transform.rotate(scaled_image, spin_rotation)

    rect = rotated.get_rect(
        center=(x, y + math.sin(spin_amount * 12.0 + x * 0.1) * 4)
    )

    surface.blit(rotated, rect)

    if highlight_strength > 0:
        lightened = rotated.copy()
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
	global running, dragging, handle, current_screen, Aspin, wait_spin, symbol_matrix, spin_active, spin_progress, spin_frame, highlighted_positions, highlight_timer, highlight_sequence, highlight_pattern_names, highlight_index, current_highlight_duration, jackpot_highlight_speed, current_credits, input_debt_amount, debt_credits, current_deadline_cost, remain_spins, spin_cost, remain_round

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
						current_highlight_duration = highlight_duration / jackpot_highlight_speed
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
				symbol_matrix = [
					random.choices(symbols, weights=weights, k=5)
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
				current_highlight_duration = highlight_duration / jackpot_highlight_speed if matches and matches[0][0] == "JACKPOT" else highlight_duration
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
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] > 700:
						current_screen = 2
						dragging = False

					if remain_spins == 0:
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
				symbol_matrix = [
					random.choices(symbols, weights=weights, k=5)
					for _ in range(3)
				]
				spin_active = True
				spin_progress = 0.0
				spin_frame = 0
				highlighted_positions = set()
				highlight_timer = 0.0
				highlight_sequence = []
				highlight_index = 0
				current_highlight_duration = highlight_duration
				Aspin = False
				remain_spins -= 1

			display.fill((30, 30, 30))

			pygame.draw.circle(display, (70, 160, 255), (handle.x + handle.width // 2, handle.y + handle.height // 2), handle.width // 2)

			for row, column_symbols in enumerate(symbol_matrix):
				for column, symbol in enumerate(column_symbols):
					base_x = grid_x[column]
					base_y = grid_y[row]
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
						draw_slot_symbol(display, symbol, base_x, base_y, 0.0, highlight_strength)

			if remain_spins == 0:
				pygame.draw.rect(display, (0, 0, 0), display.get_rect())
				high_ticket.draw(display, (mx, my))
				low_ticket.draw(display, (mx, my))


			pygame.display.flip()
			clock.tick(100)

	#--------------------debt screen--------------------
		if current_screen == 2:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
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

			pygame.display.flip()
			clock.tick(100)

	#--------------------charm buy screen--------------------
		if current_screen == 3:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					if event.pos[0] < 300:
						current_screen = 2
						dragging = False

			display.fill((30, 30, 30))

			pygame.display.flip()
			clock.tick(100)

	pygame.quit()


if __name__ == "__main__":
	main()