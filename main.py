import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import random
import os
from collections import Counter

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
ALLOWED_USER_IDS = [1076458831430832238]
games = {}

class Game:
    def __init__(self, host):
        self.host = host
        self.participants = set()
        self.imposter_count = 1
        self.started = False
        self.imposters = []
        self.message = None

class GameView(View):
    def __init__(self, ctx, game: Game):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.game = game

    def generate_embed(self):
        player_list = '\n'.join(f"- {p.display_name}" for p in self.game.participants) or "*None yet*"
        embed = discord.Embed(
            title="⚽ Football Imposter Game",
            description=f"**Host:** {self.game.host.display_name}\n\n**Players Joined:**\n{player_list}\n\n**Imposters:** {self.game.imposter_count}",
            color=discord.Color.blurple()
        )
        return embed

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.primary)
    async def join(self, interaction: discord.Interaction, button: Button):
        if self.game.started:
            await interaction.response.send_message("Game already started.", ephemeral=True)
            return

        self.game.participants.add(interaction.user)
        embed = self.generate_embed()
        await self.game.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"You joined the game!", ephemeral=True)

    @discord.ui.select(
        placeholder="Select number of imposters",
        options=[discord.SelectOption(label=str(i), value=str(i)) for i in range(1, 4)]
    )
    async def set_imposters(self, interaction: discord.Interaction, select: Select):
        if interaction.user != self.game.host:
            await interaction.response.send_message("Only the host can set imposters.", ephemeral=True)
            return
        self.game.imposter_count = int(select.values[0])
        embed = self.generate_embed()
        await self.game.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"Imposters set to {select.values[0]}", ephemeral=True)

    @discord.ui.button(label="Start Match", style=discord.ButtonStyle.success)
    async def start_game(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.game.host:
            await interaction.response.send_message("Only the host can start the game.", ephemeral=True)
            return

        if len(self.game.participants) < 3:
            await interaction.response.send_message("At least 3 players are required to start the game.", ephemeral=True)
            return

        if self.game.imposter_count >= len(self.game.participants):
            await interaction.response.send_message("Too many imposters for the number of players.", ephemeral=True)
            return

        self.game.started = True
        players = list(self.game.participants)
        imposters = random.sample(players, self.game.imposter_count)
        self.game.imposters = imposters

        footballers = [
            # Superstars + legends + underrated
            "Lionel Messi", "Cristiano Ronaldo", "Kylian Mbappé", "Erling Haaland", "Neymar Jr", "Kevin De Bruyne",
            "Robert Lewandowski", "Karim Benzema", "Mohamed Salah", "Harry Kane", "Vinícius Júnior", "Jude Bellingham",
            "Phil Foden", "Pedri", "Gavi", "João Félix", "Bruno Fernandes", "Bernardo Silva", "Bukayo Saka",
            "Declan Rice", "Lautaro Martínez", "Khvicha Kvaratskhelia", "Victor Osimhen", "Frenkie de Jong",
            "Luis Díaz", "Trent Alexander-Arnold", "Andrew Robertson", "Achraf Hakimi", "João Cancelo",
            "Thibaut Courtois", "Marc-André ter Stegen", "Alisson Becker", "Ederson", "Manuel Neuer",
            "Zinedine Zidane", "Ronaldinho", "Pelé", "Diego Maradona", "Johan Cruyff", "David Beckham",
            "Kaka", "Rivaldo", "Xavi", "Andrés Iniesta", "Paolo Maldini", "Roberto Carlos", "Iker Casillas",
            "Thierry Henry", "Wayne Rooney", "Pirlo", "Fernando Torres", "Raúl", "Luis Figo",
            "Valderrama", "George Weah", "Alan Shearer", "Francesco Totti", "Bergkamp",
            "Mitoma", "Trossard", "Ødegaard", "Florian Wirtz", "Doku", "Kudus", "Eze", "Estupiñán", "Ferguson",
            "Lucas Paquetá", "Musah", "Malacia", "Brobbey", "Loïs Openda", "Timber", "Nico Williams", "Garnacho",
            "Gvardiol", "Solomon", "Šeško", "Take Kubo", "Rodrygo", "Ansu Fati", "Aleix García", "Sandro Tonali",
            "Højlund", "Amadou Onana", "Badiashile", "Gnonto", "Jorginho", "Reyna", "Pepi", "McKennie"
        ]

        chosen_player = random.choice(footballers)

        for player in players:
            try:
                if player in imposters:
                    await player.send("You are the imposter 🤫")
                else:
                    await player.send(f"Your footballer: **{chosen_player}**")
            except:
                await self.ctx.send(f"⚠️ Couldn't DM {player.mention}")

        await self.ctx.send("✅ **Game started! Check your DMs.**")

    @discord.ui.button(label="Start Voting", style=discord.ButtonStyle.danger)
    async def start_voting(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.game.host:
            await interaction.response.send_message("Only the host can start voting.", ephemeral=True)
            return

        if not self.game.started:
            await interaction.response.send_message("You must start the match before voting.", ephemeral=True)
            return

        options = [discord.SelectOption(label=player.display_name, value=str(player.id)) for player in self.game.participants]

        class VoteSelect(discord.ui.View):
            def __init__(self, participants, imposters):
                super().__init__(timeout=60)
                self.votes = {}
                self.participants = participants
                self.imposters = imposters

                self.select = discord.ui.Select(
                    placeholder="Vote for the imposter",
                    options=options
                )
                self.select.callback = self.vote
                self.add_item(self.select)

            async def vote(self, interaction: discord.Interaction):
                voter = interaction.user
                if voter not in self.participants:
                    await interaction.response.send_message("You're not a player.", ephemeral=True)
                    return

                if voter.id in self.votes:
                    await interaction.response.send_message("You already voted.", ephemeral=True)
                    return

                chosen_id = int(self.select.values[0])
                self.votes[voter.id] = chosen_id
                await interaction.response.send_message(f"You voted for <@{chosen_id}>", ephemeral=True)

                if len(self.votes) == len(self.participants):
                    self.stop()

        vote_view = VoteSelect(self.game.participants, self.game.imposters)
        await interaction.response.send_message("🗳️ Voting started!", view=vote_view)
        await vote_view.wait()

        votes = list(vote_view.votes.values())
        if not votes:
            await self.ctx.send("❌ No one voted. Game ends.")
            return

        count = Counter(votes)
        top = count.most_common(1)
        top_votes = [v for v, c in count.items() if c == top[0][1]]

        if len(top_votes) > 1:
            await self.ctx.send("🌀 **Ah Sh!it ! Here we go again** — It's a tie.")
        else:
            voted_out_id = top_votes[0]
            voted_out = discord.utils.get(self.ctx.guild.members, id=int(voted_out_id))
            if voted_out in self.game.imposters:
                await self.ctx.send(f"🎯 **{voted_out.display_name} was the imposter!**\nCaught in 4k N!gga")
            else:
                await self.ctx.send(f"🙈 **{voted_out.display_name} was innocent!**\nNice try Diddy")

        del games[self.ctx.channel.id]
        self.stop()

@bot.command()
async def startgame(ctx):
    if ctx.channel.id in games:
        await ctx.send("⚠️ A game is already running.")
        return

    game = Game(ctx.author)
    games[ctx.channel.id] = game
    view = GameView(ctx, game)
    embed = view.generate_embed()
    game.message = await ctx.send(embed=embed, view=view)

@bot.event
async def on_ready():
    print(f"🤖 Logged in as {bot.user}")

bot.run(os.environ['DISCORD_BOT_TOKEN'])

