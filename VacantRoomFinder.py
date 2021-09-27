import discord, requests, json, html
from datetime import date, datetime
from discord.ext import commands


germain = [
    ["G001 - GERMAIN", "G002 - GERMAIN", "G003 - GERMAIN", "G007 - GERMAIN"],
    ["G101 - GERMAIN", "G103 - GERMAIN", "G104 - GERMAIN", "G105 - GERMAIN", "G107 - GERMAIN"],
    ["G201 - GERMAIN", "G203 - GERMAIN", "G204 - GERMAIN", "G205 - GERMAIN", "G206 - GERMAIN", "G207 - GERMAIN", "G209 - GERMAIN", "G210 - GERMAIN"]
]


def get_room_edt(room, day): 
    url = 'https://edt.uvsq.fr/Home/GetCalendarData'
    data = {'start':day,'end':day,'resType':'102','calView':'agendaDay','federationIds[]':room}
    response = requests.post(url,data=data)
    bytes_value = response.content.decode('utf8')
    data = json.loads(bytes_value)
    return data

def check_empty(room, moment):
    data = get_room_edt(room, moment.strftime("%Y-%m-%d"))
    until = None
    
    for module_data in data:
        debut = datetime.strptime(module_data["start"], "%Y-%m-%dT%H:%M:%S")
        fin = datetime.strptime(module_data["end"], "%Y-%m-%dT%H:%M:%S")
        
        description = html.unescape(module_data["description"])
        description = description.replace("\n", "")
        description = description.replace("\r", "")
        description = description.replace("<br />", "¨")

        sub_data = {
            "jour":f'{debut.day}/{debut.month}',
            "debut":debut,
            "fin":fin,
            "horaire":'{:0>2d}:{:0>2d}  —  {:0>2d}:{:0>2d}'.format(debut.hour, debut.minute, fin.hour, fin.minute),
            "salle":description.split("¨")[1],
            "module":description.split("¨")[2],
        }
        
        if moment > debut and moment < fin:
            return False, None

        elif moment < debut and (until is None or debut < until['debut']):
            until = sub_data
            
    return True, until


        


class FreeRoomFinder(commands.Cog):
    """
    Outil de recherche d'une salle disponible pour un moment donné
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


    @commands.command(name='squat')
    async def find_room(self, ctx, moment = None):
        if not moment:
            moment = datetime.now()
        else:
            moment = datetime.strptime(moment, "%d/%m/%Y %H:%M")

        print(f"Requesting for {moment}") 

        output = []
        nb_libres = 0
        for floor in germain:
            floor_output = []
            for room in floor: 
                empty, until = check_empty(room, moment)
                if empty:
                    floor_output.append([room, until])
                    nb_libres += 1
            
            output.append(floor_output.copy())


        if len(output) == 0:
            em = discord.Embed(title=f"<:week:755154675149439088> ViteMaSalle – {moment}", 
                        description=f"<:redTick:876779478410465291> Aucune salle libre n'est malheuresement disponible en ce moment.", 
                        color=0xb2e4d7, timestamp=datetime.utcnow())
        else: 
            em = discord.Embed(title=f"<:week:755154675149439088> ViteMaSalle – {moment}",
                description=f"**{nb_libres} salles** sont disponibles en ce moment dans le **bâtiment Germain**.", 
                color=0xb2e4d7, timestamp=datetime.utcnow())
            
            for floor, i in zip(output, range(0, len(output))):
                if len(floor):
                    em_name = f"Étage {i}" if i > 0 else "Rez-de-chaussée"
                    em_value = ""
                    for room in floor:
                        if room[1]:
                            room[1]['debut'] = "{:0>2d}:{:0>2d}".format(room[1]['debut'].hour, room[1]['debut'].minute)
                            em_value += f"<:greenTick:876779478733455360> Salle `{room[0][:4]}` — Jusqu'à **{room[1]['debut']}**\n"
                        else:
                            em_value += f"<:greenTick:876779478733455360> Salle `{room[0][:4]}` — **Toute la journée**\n"
                    em.add_field(name=em_name, value=em_value, inline=False)

        await ctx.send(embed=em)



def setup(bot):
    bot.add_cog(FreeRoomFinder(bot))
