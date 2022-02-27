# database management

from peewee import *
from . import keys

db = MySQLDatabase(keys.model, host=keys.host, user=keys.user, passwd=keys.passwd)

class BaseModell(Model):
    DoesNotExist = None

    class Meta:
        database = db

# table of users registered with Ghost50, which stores username, password, and score
class User(BaseModell):
    #peewee auto adds an "id" column, auto-incrementing
    id = PrimaryKeyField()
    username = CharField(unique=True)
    password = CharField()
    score = IntegerField()
    ai_word = CharField()

# table of matches, where each match is a row with an id, name, current_game, current_word,timer, current_turn, has_started, num_players, and game_ended    
class Match(BaseModell):
    # only added id manually to suppress warning, usually adds automatically
    id = PrimaryKeyField()
    name = CharField(unique=True)
    current_game = IntegerField()
    current_word = CharField(default="")
    timer = IntegerField()
    current_turn = ForeignKeyField(User, to_field='id', null = True)
    has_started = BooleanField(default=False)
    num_players = IntegerField(default=0)
    game_ended = BooleanField(default=False)

# table of user-matches, connecting users and match ids with their status (Waiting versus Ready)    
class User_Match(BaseModell):
    #peewee auto adds an "id" column, auto-incrementing
    user = ForeignKeyField(User, to_field='id', unique=True)
    match = ForeignKeyField(Match, to_field='id')
    status = CharField(default="Waiting")


# initializes the database    
def initialize_db():
	db.connect()
	db.create_tables([User, Match, User_Match], safe=True)

