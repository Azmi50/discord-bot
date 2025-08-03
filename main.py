import discord
from discord import app_commands
from discord.ui import Button, View, Select
import random
import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from dotenv import load_dotenv
load_dotenv()
import os


# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Data storage
tournaments = {}
participants = {}
active_matches = {}
match_results = {}
all_rounds = {}  # Tracks every round's matches
tournament_types = {}  # Stores tournament type for each tournament

def load_custom_font(size):
    font_options = [
        "consolab.ttf",
        "courbd.ttf",
        "lucon.ttf",
        None
    ]
    for font_path in font_options:
        try:
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    return ImageFont.load_default()

def generate_pixel_perfect_bracket(tournament_name):
    if tournament_name not in all_rounds:
        return None

    round_count = len(all_rounds[tournament_name])
    img_width = 250 + (round_count * 300)  # Reduced spacing between rounds
    img_height = max(800, 100 + len(all_rounds[tournament_name][0]) * 120)
    img = Image.new('RGB', (img_width, img_height), (10, 10, 20))
    draw = ImageDraw.Draw(img)

    font_reg = load_custom_font(18)
    colors = {
        'text': (200, 200, 200),
        'win': (0, 200, 100),
        'lose': (220, 50, 50),
        'line': (100, 100, 150),
        'box': (30, 30, 40),
        'box_border': (80, 80, 100),
        'winner': (250, 200, 50)
    }

    # First pass: calculate all match positions
    match_positions = {}
    for round_num, round_matches in enumerate(all_rounds[tournament_name]):
        x_pos = 50 + (round_num * 300)
        match_spacing = 120
        total_matches = len(round_matches)
        start_y = (img_height - (total_matches * match_spacing)) // 2

        for match_idx, (p1, p2) in enumerate(round_matches):
            y_pos = start_y + (match_idx * match_spacing)
            match_positions[(round_num, match_idx)] = (x_pos, y_pos)

    # Second pass: draw everything
    for round_num, round_matches in enumerate(all_rounds[tournament_name]):
        for match_idx, (p1, p2) in enumerate(round_matches):
            x_pos, y_pos = match_positions[(round_num, match_idx)]
            res = match_results.get(tournament_name, {}).get((p1, p2), {})

            # Draw player boxes
            box_width = 160
            draw.rectangle((x_pos, y_pos, x_pos + box_width, y_pos + 30), 
                          fill=colors['box'], outline=colors['box_border'])
            draw.rectangle((x_pos, y_pos + 40, x_pos + box_width, y_pos + 70), 
                          fill=colors['box'], outline=colors['box_border'])

            # Player names (truncate if too long)
            p1_display = (p1[:12] + '..') if len(p1) > 12 else p1
            p2_display = (p2[:12] + '..') if len(p2) > 12 else p2
            draw.text((x_pos + 5, y_pos + 5), p1_display, font=font_reg, fill=colors['text'])
            draw.text((x_pos + 5, y_pos + 45), p2_display, font=font_reg, fill=colors['text'])

            # Win/Lose markers
            if res.get("p1_vote") == "win":
                draw.rectangle((x_pos + box_width, y_pos, x_pos + box_width + 20, y_pos + 30), 
                             fill=colors['win'])
                draw.text((x_pos + box_width + 2, y_pos + 5), "W", font=font_reg, fill=(0, 0, 0))
            elif res.get("p1_vote") == "lose":
                draw.rectangle((x_pos + box_width, y_pos, x_pos + box_width + 20, y_pos + 30), 
                             fill=colors['lose'])
                draw.text((x_pos + box_width + 2, y_pos + 5), "L", font=font_reg, fill=(0, 0, 0))

            if res.get("p2_vote") == "win":
                draw.rectangle((x_pos + box_width, y_pos + 40, x_pos + box_width + 20, y_pos + 70), 
                             fill=colors['win'])
                draw.text((x_pos + box_width + 2, y_pos + 45), "W", font=font_reg, fill=(0, 0, 0))
            elif res.get("p2_vote") == "lose":
                draw.rectangle((x_pos + box_width, y_pos + 40, x_pos + box_width + 20, y_pos + 70), 
                             fill=colors['lose'])
                draw.text((x_pos + box_width + 2, y_pos + 45), "L", font=font_reg, fill=(0, 0, 0))

            # Draw connecting lines to next round
            if round_num < len(all_rounds[tournament_name]) - 1:
                next_match_idx = match_idx // 2
                if (round_num + 1, next_match_idx) in match_positions:
                    next_x, next_y = match_positions[(round_num + 1, next_match_idx)]

                    # Calculate connection points
                    current_top = y_pos + 15  # Center of top player box
                    current_bottom = y_pos + 55  # Center of bottom player box
                    next_center = next_y + 35  # Center of next match

                    # Draw diagonal lines
                    line_start_x = x_pos + box_width + 20
                    line_mid_x = line_start_x + (next_x - line_start_x) // 2

                    # Top player to next match
                    draw.line([
                        (line_start_x, current_top),
                        (line_mid_x, current_top),
                        (line_mid_x, next_center),
                        (next_x - 10, next_center)
                    ], fill=colors['line'], width=2)

                    # Bottom player to next match
                    draw.line([
                        (line_start_x, current_bottom),
                        (line_mid_x, current_bottom),
                        (line_mid_x, next_center),
                        (next_x - 10, next_center)
                    ], fill=colors['line'], width=2)

    # Draw winner if tournament complete
    final_round = all_rounds[tournament_name][-1]
    if len(final_round) == 1:
        p1, p2 = final_round[0]
        res = match_results.get(tournament_name, {}).get((p1, p2), {})
        if res.get("p1_vote") and res.get("p2_vote"):
            winner = p1 if res.get("p1_vote") == "win" else p2
            x_pos, y_pos = match_positions[(len(all_rounds[tournament_name]) - 1, 0)]
            draw.rectangle((x_pos + 200, y_pos + 30, x_pos + 360, y_pos + 70), 
                         fill=colors['winner'], outline=colors['box_border'])
            draw.text((x_pos + 210, y_pos + 40), f"Winner: {winner}", 
                     font=font_reg, fill=(0, 0, 0))

    img = ImageEnhance.Contrast(img).enhance(1.1)
    img = ImageEnhance.Brightness(img).enhance(1.1)

    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

class TournamentTypeSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Quick Tournament",
                value="quick",
                description="Single elimination bracket - fast-paced competition"
            ),
            discord.SelectOption(
                label="League Tournament",
                value="league",
                description="Round robin format - everyone plays everyone"
            )
        ]
        super().__init__(
            placeholder="Choose tournament type...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.tournament_type = self.values[0]
        await interaction.response.edit_message(
            content=f"Selected: {self.values[0]} tournament",
            view=None
        )
        await self.view.finalize_tournament_creation(interaction)

class TournamentCreationView(View):
    def __init__(self, name, size):
        super().__init__()
        self.name = name
        self.size = size
        self.tournament_type = "quick"  # Default
        self.add_item(TournamentTypeSelect())

    async def finalize_tournament_creation(self, interaction: discord.Interaction):
        if self.name in tournaments:
            await interaction.followup.send("❌ Tournament exists! Choose another name.", ephemeral=True)
            return

        tournaments[self.name] = {
            "size": self.size,
            "creator": interaction.user.name,
            "type": self.tournament_type
        }
        participants[self.name] = []
        tournament_types[self.name] = self.tournament_type

        view = TournamentView(self.name, self.size, self.tournament_type)
        await interaction.followup.send(
            embed=view.update_embed(),
            view=view
        )

class TournamentView(View):
    def __init__(self, tournament_name, max_players, tournament_type="quick"):
        super().__init__(timeout=None)
        self.tournament_name = tournament_name
        self.max_players = max_players
        self.tournament_type = tournament_type

    @discord.ui.button(label="Join Tournament", style=discord.ButtonStyle.green)
    async def join_tournament(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(participants.get(self.tournament_name, [])) >= self.max_players:
            await interaction.response.send_message("❌ Tournament is full!", ephemeral=True)
            return

        if interaction.user.name not in participants.setdefault(self.tournament_name, []):
            participants[self.tournament_name].append(interaction.user.name)
            await interaction.response.send_message(
                f"✅ {interaction.user.mention} joined **{self.tournament_name}**!",
                ephemeral=True
            )
            await interaction.message.edit(embed=self.update_embed())

            if len(participants[self.tournament_name]) == self.max_players:
                await self.start_tournament(interaction)
        else:
            await interaction.response.send_message("❌ You already joined!", ephemeral=True)

    def update_embed(self):
        embed = discord.Embed(
            title=f"🏆 {self.tournament_name}",
            description=f"Players: {len(participants.get(self.tournament_name, []))}/{self.max_players}",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Participants",
            value="\n".join(participants.get(self.tournament_name, ["None"])) or "None",
            inline=False
        )
        return embed

    async def start_tournament(self, interaction):
        players = participants[self.tournament_name]
        random.shuffle(players)

        if self.tournament_type == "quick":
            first_round = [(players[i], players[i+1]) for i in range(0, len(players), 2)]
            all_rounds[self.tournament_name] = [first_round]
            active_matches[self.tournament_name] = first_round.copy()
            match_results[self.tournament_name] = {}

            bracket_img = generate_pixel_perfect_bracket(self.tournament_name)
            await interaction.channel.send(
                content="🎮 **Quick Tournament Started!** (Single Elimination)",
                file=discord.File(bracket_img, filename="bracket.png")
            )

            for p1, p2 in first_round:
                match_results[self.tournament_name][(p1, p2)] = {"p1_vote": None, "p2_vote": None}
                await interaction.channel.send(
                    f"⚔️ **Match**: {p1} vs {p2}\n"
                    "Use `/result` to submit your outcome (20min limit)"
                )

        elif self.tournament_type == "league":
            matches = []
            for i in range(len(players)):
                for j in range(i+1, len(players)):
                    matches.append((players[i], players[j]))

            all_rounds[self.tournament_name] = [matches]
            active_matches[self.tournament_name] = matches.copy()
            match_results[self.tournament_name] = {}

            tournaments[self.tournament_name]["standings"] = {
                player: {"wins": 0, "losses": 0} for player in players
            }

            await interaction.channel.send(
                content="🏆 **League Tournament Started!** (Round Robin)\n"
                        "Each player will face every other player once.\n"
                        f"Total matches: {len(matches)}"
            )

            for i, (p1, p2) in enumerate(matches[:5]):
                match_results[self.tournament_name][(p1, p2)] = {"p1_vote": None, "p2_vote": None}
                await interaction.channel.send(
                    f"⚔️ **Match {i+1}**: {p1} vs {p2}\n"
                    "Use `/result` to submit your outcome"
                )

class ResultView(View):
    def __init__(self, p1, p2, tournament_name, username):
        super().__init__(timeout=1200)
        self.p1 = p1
        self.p2 = p2
        self.tournament_name = tournament_name
        self.username = username

    @discord.ui.button(label="I Won", style=discord.ButtonStyle.green)
    async def declare_win(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_result(interaction, "win")

    @discord.ui.button(label="I Lost", style=discord.ButtonStyle.red)
    async def declare_loss(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.submit_result(interaction, "lose")

    async def submit_result(self, interaction, result):
        if self.username not in [self.p1, self.p2]:
            await interaction.response.send_message("❌ You're not part of this match!", ephemeral=True)
            return

        match_key = (self.p1, self.p2)
        if self.username == self.p1:
            match_results[self.tournament_name][match_key]["p1_vote"] = result
        else:
            match_results[self.tournament_name][match_key]["p2_vote"] = result

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

        res = match_results[self.tournament_name][match_key]
        if res["p1_vote"] is not None and res["p2_vote"] is not None:
            await self.process_completed_match(interaction)
        else:
            await interaction.followup.send("✅ Vote recorded. Waiting for opponent...", ephemeral=True)

    async def process_completed_match(self, interaction):
        res = match_results[self.tournament_name][(self.p1, self.p2)]

        if (res["p1_vote"], res["p2_vote"]) not in [("win", "lose"), ("lose", "win")]:
            await interaction.followup.send("❌ Results conflict! Please coordinate.", ephemeral=True)
            return

        winner = self.p1 if res["p1_vote"] == "win" else self.p2
        loser = self.p2 if winner == self.p1 else self.p1

        active_matches[self.tournament_name].remove((self.p1, self.p2))

        if tournament_types.get(self.tournament_name) == "quick":
            await self.handle_quick_tournament(interaction, winner)
        else:
            await self.handle_league_tournament(interaction, winner, loser)

    async def handle_quick_tournament(self, interaction, winner):
        current_round = all_rounds[self.tournament_name][-1]

        if not any(match in active_matches[self.tournament_name] for match in current_round):
            winners = [
                m[0] if match_results[self.tournament_name][m]["p1_vote"] == "win" else m[1]
                for m in current_round
            ]

            if len(winners) > 1:
                next_round = [(winners[i], winners[i+1]) for i in range(0, len(winners), 2)]
                all_rounds[self.tournament_name].append(next_round)
                active_matches[self.tournament_name] = next_round.copy()

                await interaction.channel.send("🔥 **Next Round Matches:**")
                for p1, p2 in next_round:
                    match_results[self.tournament_name][(p1, p2)] = {"p1_vote": None, "p2_vote": None}
                    await interaction.channel.send(f"⚔️ **{p1}** vs **{p2}**\nSubmit results with `/result`")
            else:
                await interaction.channel.send(f"🏆 **Tournament Champion**: {winners[0]}")

        updated_bracket = generate_pixel_perfect_bracket(self.tournament_name)
        await interaction.followup.send(
            content=f"🎯 **Match Result**: {winner} advances!",
            file=discord.File(updated_bracket, filename="bracket.png")
        )

    async def handle_league_tournament(self, interaction, winner, loser):
        tournaments[self.tournament_name]["standings"][winner]["wins"] += 1
        tournaments[self.tournament_name]["standings"][loser]["losses"] += 1

        if not active_matches[self.tournament_name]:
            standings = tournaments[self.tournament_name]["standings"]
            sorted_players = sorted(standings.items(),
                                  key=lambda x: (x[1]["wins"], -x[1]["losses"]),
                                  reverse=True)

            embed = discord.Embed(
                title=f"🏆 {self.tournament_name} - Final Standings",
                color=discord.Color.gold()
            )

            for i, (player, stats) in enumerate(sorted_players):
                embed.add_field(
                    name=f"{i+1}. {player}",
                    value=f"Wins: {stats['wins']} | Losses: {stats['losses']}",
                    inline=False
                )

            await interaction.channel.send(
                content=f"🎉 **League Tournament Complete!**\n"
                       f"🏆 Champion: {sorted_players[0][0]}",
                embed=embed
            )
        else:
            await interaction.followup.send(
                content=f"✅ **Match Result**: {winner} defeated {loser}\n"
                       f"Remaining matches: {len(active_matches[self.tournament_name])}"
            )

@tree.command(name="newtournament", description="Create a new tournament")
async def create_tournament(interaction: discord.Interaction, 
                          name: str, 
                          size: app_commands.Range[int, 2, 32] = 8):
    view = TournamentCreationView(name, size)
    await interaction.response.send_message(
        content="**Select Tournament Type**",
        view=view,
        ephemeral=True
    )

@tree.command(name="result", description="Submit your match result")
async def submit_result(interaction: discord.Interaction):
    user = interaction.user.name
    for tourney, matches in active_matches.items():
        for p1, p2 in matches:
            if user in (p1, p2):
                view = ResultView(p1, p2, tourney, user)
                await interaction.response.send_message(
                    f"Submit result for: **{p1}** vs **{p2}**",
                    view=view,
                    ephemeral=True
                )
                return
    await interaction.response.send_message("❌ No active matches found for you!", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f'✅ Tournament Bot ready as {bot.user}')

# Run the bot with your token
bot.run(os.getenv("DISCORD_TOKEN"))
