import requests, json, html
from datetime import datetime
import re

greenTick = '<:greenTick:876779478733455360>'
redTick = ''

germain = [
    ["G001 - GERMAIN", "G002 - GERMAIN", "G003 - GERMAIN", "G007 - GERMAIN"],
    ["G101 - GERMAIN", "G103 - GERMAIN", "G104 - GERMAIN", "G105 - GERMAIN", "G107 - GERMAIN"],
    ["G201 - GERMAIN", "G203 - GERMAIN", "G204 - GERMAIN", "G205 - GERMAIN", "G206 - GERMAIN", "G207 - GERMAIN", "G209 - GERMAIN", "G210 - GERMAIN"]
]

# TODO: Ajouter les salles Fermat + Descartes (Jungle, Alsace, etc.) + possibilité de lancer la recherche sur un seul batiment

def get_room_edt(room, day): 
    """ Requête POST sur CELCAT pour obtenir l'emploi du temps JSON d'une salle pour une jour donné """

    url = 'https://edt.uvsq.fr/Home/GetCalendarData'
    data = {'start':day,'end':day,'resType':'102','calView':'agendaDay','federationIds[]':room}
    response = requests.post(url,data=data)
    bytes_value = response.content.decode('utf8')
    data = json.loads(bytes_value)
    return data

def check_if_empty(room, moment):
    """ Renvoie False si la @room est occupé au @moment donné, 
        et True avec la data du prochain créneau si elle est vacante """

    # data = get_room_edt(room, moment.strftime("%Y-%m-%d"))
    data = get_room_edt(room, f"{moment.year}-{moment.month}-{moment.day}")
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
            "module":description.split("¨")[2]
        }
        
        # Salle occupée: on renvoie Faux et on quitte la fonction
        if moment > debut and moment < fin:
            return False, None

        # Sinon: on ajoute la data du dernier module à Until
        elif moment < debut and (until is None or debut < until['debut']):
            until = sub_data
    
    # Salle vacante. Until = None si vacante toute la journée (aucun créneau après) 
    return True, until

def find_all_rooms(moment):
    """ Renvoie l'ensemble des salles vacantes pour un @moment donné """

    print(f"Requesting for {moment}") 
    output = []
    nb_libres = 0
    for floor in germain:
        floor_output = []
        for room in floor: 
            empty, until = check_if_empty(room, moment) # until = data du créneau qui occupe la salle 
            if empty:
                floor_output.append([room, until])
                nb_libres += 1
        
        output.append(floor_output.copy())

    return nb_libres, output

def match_datetime(moment):
    """ Renvoie la date formatée, si celle-ci matche. """
    try:
        match = re.compile(r'\d{1,2}-\d{1,2} \d{1,2}:\d{2}').search(moment) # Search is used otherwise, match can't find it if garbage chars surrounding date.
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m-%d %H:%M'))

        match = re.compile(r'\d{1,2}-\d{1,2} \d{1,2}h\d{2}').search(moment)
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m-%d %Hh%M'))

        match = re.compile(r'\d{1,2}\/\d{1,2} \d{1,2}:\d{2}').search(moment)
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m/%d %H:%M'))

        match = re.compile(r'\d{1,2}\/\d{1,2} \d{1,2}h\d{2}').search(moment)
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m/%d %Hh%M'))

        match = re.compile(r'\d{4}-\d{1,2}-\d{1,2}').search(moment)
        if match: return(datetime.strptime(moment[match.start():match.end()], '%Y-%m-%d'))

        match = re.compile(r'\d{2}-\d{1,2}-\d{1,2}').search(moment)
        if match: return(datetime.strptime(moment[match.start():match.end()], '%Y-%m-%d'))

        match = re.compile(r'\d{4}\/\d{1,2}\/\d{1,2}').search(moment)
        if match: return(datetime.strptime(moment[match.start():match.end()], '%Y/%m/%d'))

        match = re.compile(r'\d{2}\/\d{1,2}\/\d{1,2}').search(moment)
        if match: return(datetime.strptime(moment[match.start():match.end()], '%Y/%m/%d'))

        match = re.compile(r'\d{1,2}-\d{1,2}').search(moment)
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m-%d'))

        match = re.compile(r'\d{1,2}\/\d{1,2}').search(moment)
        if match: return(datetime.strptime(f"{datetime.now().year}_{moment[match.start():match.end()]}", '%Y_%m/%d'))
    except Exception as error:
        print(f'\033[91mError: <match_datetime({moment})> {error}\033[0m')
        return False
    
    return False


# Discord Bot Part 
import discord
from discord.ext import commands

class FreeRoomFinder(commands.Cog):
    """
    Outil de recherche d'une salle disponible pour un moment donné
    """
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


    @commands.command(name='findroom')
    async def find_room(self, ctx, moment = None):
        
        # TODO: ajouter slash_commands avec choix pour les batiments ? solution pour le @moment ?

        if not moment:
            moment = datetime.now()
        else:
            # TODO: accepter tous les formats d'horaires (HHhMM, HhMM, HH:MM, DD/MM/YY HH:MM, etc.) - Regex ou lib existante ?
            # moment = datetime.datetime.strptime(moment, '%Y-%m-%d')
            # moment = datetime.strptime(moment, "%d/%m/%Y %H:%M")
            res = match_datetime(moment)
            if not res:
                await ctx.send(f"Désolé, mais la date {moment} n'a pas été reconnue.\nExemples de formats disponibles : Mois/Jour, Année/Mois/Jour, Année/Mois/Jour, Heure:Minutes")
            else:
                moment = res


        nb_libres, output = find_all_rooms(moment)

        # TODO : Arranger l'output Embed 

        if len(output) == 0: # Aucune salle libre en Germain
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
                            em_value += f"{greenTick} Salle `{room[0][:4]}` — Jusqu'à **{room[1]['debut']}**\n"
                        else:
                            em_value += f"{greenTick} Salle `{room[0][:4]}` — **Toute la journée**\n"
                    em.add_field(name=em_name, value=em_value, inline=False)

        await ctx.send(embed=em)



    @find_room.error
    async def test_on_error(self, ctx, error):
        """ Sends the suitable error message to user """
        print(f'\033[91mError: <{ctx.command}> {error}\033[0m')
        await ctx.send("ERR - `{}`".format(error))

def setup(bot):
    bot.add_cog(FreeRoomFinder(bot))
