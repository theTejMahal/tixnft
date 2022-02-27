from flask import Flask, jsonify, render_template, request, url_for, session, flash, redirect
from flask_jsglue import JSGlue
from .models import *
from threading import Event, Thread
from .trie import *
from passlib.apps import custom_app_context as pwd_context
from flask_session import Session
from .helpers import *
from tempfile import gettempdir
from .ai import *


import sys

# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response
        
# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def before_request():
	# create db if needed and connect
	initialize_db()

@app.teardown_request
def _db_close(exc):
    if not db.is_closed():
        db.close()

@app.route("/")
@login_required
def index():
    # render home page

    users = User.select(User.username, User.score).order_by(User.score.desc())

    return render_template('index.html', users=users)
    
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()
    error = None


    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            error = 'Must provide username'

        # ensure password was submitted
        elif not request.form.get("password"):
            error = 'Must provide password'

        try:
            # check username
            user = User.get(username=request.form['username'])
        except User.DoesNotExist:
            error = 'Invalid username or password'
        else:
            # check password
            if pwd_context.verify(request.form['password'], user.password):
                #valid, sign them in
                
                # remember which user has logged in
                session["user_id"] = user.id
            
                flash('You were successfully logged in')

                # redirect user to home page
                return redirect(url_for("index"))
            else:
                error = 'Invalid usename or password'

    # else if user reached route via GET (as by clicking a link or via redirect) or there was an error
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    
    # forget any user_id
    session.clear()
    error = None

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            error = 'Must provide username'

        # ensure password was submitted
        elif not request.form.get("password"):
            error = 'Must provide password'
            
        # ensure passwords are equal
        
        elif not request.form.get("password") == request.form.get("confirm_password"):
            error = 'Passwords must match'

        # insert user
        else:
            try:
                with db.transaction():
                    # Attempt to create the user. If the username is taken, due to the
                    # unique constraint, the database will raise an IntegrityError.
                    user = User.create(
                        username=request.form.get('username'),
                        password=pwd_context.encrypt(request.form.get("password")))

                flash('You were registered successfully')

                # redirect user to home page
                return redirect(url_for("index"))
            
            except IntegrityError:
                error='That username is already taken'

    # else if user reached route via GET (as by clicking a link or via redirect) or there was an error
    return render_template("register.html", error=error)
    
@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    # if the user was directed via POST
    if request.method == "POST":

        # ensure password was submitted
        if request.form.get("password"):
            error = 'Must provide password'
            
        # ensure passwords are equal
        elif not request.form.get("password") == request.form.get("confirm_password"):
            error = 'Passwords must match'

       #change password here
        newpassword=pwd_context.encrypt(request.form.get("password"))
        
        # updates the new password into the sql table 
        q = User.update(password= newpassword).where(User.id == session["user_id"])
        q.execute() 
        
        # notifies the user that their password was changed
        flash('Password changed successfully!')

        # redirect user to home page
        return redirect(url_for("index"))
            
    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepassword.html")
        
@app.route("/createroom", methods=["GET", "POST"])
def createRoom():
    """Creates a new match room"""
    
    error = None

     # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
    
        
        # if the user was part of an old game, remove them and lower count of players
        removeUser()
    
        # ensure game name was entered
        if not request.form.get("name"):
            error = 'Must provide a game name'
            
        # insert game, make sure unique
        else:
            try:
                with db.transaction():
                    # Attempt to create the game. If the name is taken, due to the
                    # unique constraint, the database will raise an IntegrityError.
                    match = Match.create(name=request.form.get('name'))
                
                flash('Your game has been created!')

                # redirect user to home page
                return redirect(url_for("waitingRoom",match_id=match.id) )
            
            except IntegrityError as err:
                error = "That name is already taken"


    # else if user reached route via GET (as by clicking a link or via redirect) or there was an error
    return render_template("createroom.html", error=error)
    

@app.route("/joinroom", methods=["GET", "POST"])
def joinRoom():
    """Renders the join room page"""    
    return render_template("joinroom.html")
    
@app.route("/_games", methods=["GET", "POST"])
def getGames(): 
    """Returns a list of all games user can join"""
    
    # looks at all the matches that haven't started
    matches = Match.select().where(Match.has_started == False)
    # gets the information from those games and returns it
    json = matches.dicts()
    return jsonify({'games':list(json)})
    
@app.route("/waitingroom", methods=["GET", "POST"])
def waitingRoom():
    """Renders the waiting room page for the specific match"""    
    
    # this gets the current id for the match
    match_id = request.args["match_id"]
    
    # if the user was part of an old game, remove them and lower count of players
    removeUser() 
    
    # adds user_match if user hasn't already joined game
    try:
        with db.transaction():
            user = User_Match.create(user=session["user_id"], match = match_id)
            
            match = Match.get(Match.id == match_id)
            match.num_players = match.num_players + 1
            match.save()
            
    except IntegrityError:
        # just don't read
        pass
    
    # if not all players have started, just show waiting room
    return render_template("waitingroom.html")

@app.route("/_waiting", methods=["GET", "POST"])
def getWaiting():
    """Returns a list of players in waiting room"""    

    # this gets the current id for the match
    match_id = request.args["match_id"]
    
    # looks at all the users with the same usermatch
    rows = User_Match.select(User_Match, User).join(User).where(User_Match.match_id == match_id)
    
    # goes through all the rows to put into the table 
    for row in rows: 
        # checks whether they have joined the game or not 
        if row.status == 2:
            row.userstatus = "Joined"
        else:
            row.userstatus = "Waiting"

        row.username = row.user.username 

    json = rows.dicts()
    return jsonify({'players':list(json)})
    
# removes the user from a match after they have left 
def removeUser():
    """Removes user from User_Match"""    
    try:
        # gets the users id
        user = User_Match.get(User_Match.user_id == session["user_id"])
        match = Match.get(Match.id == user.match_id)
        # takes them out of the match they are no longer in 
        match.num_players -= 1
        match.save()
        user.delete_instance()
    except User_Match.DoesNotExist:
        pass
    except Match.DoesNotExist:
        pass

    
@app.route("/_startGamePressed", methods=["GET", "POST"])
def startGamePressed():
    """Updates the status of the user after they press the start game button"""
    
    # when the user presses the button their status gets updated 
    q = User_Match.update(status="Ready").where(User_Match.user_id == session["user_id"])
    q.execute()
    
    match_id = request.args["match_id"]

    # check if all users have pressed ready - if they have, and game hasn't started, then start game
    users = User_Match.select().where(User_Match.match_id == match_id)
    
    # checks that everyone has loaded the game 
    isAllLoaded = True
    for user in users:
        if user.status != "Ready":
            isAllLoaded = False
            
    # If everyone has pressed start, then update the status of the game
    if isAllLoaded:
        q = Match.update(has_started=True).where(Match.id == match_id)
        q.execute()
        
        startGame(match_id)

@app.route("/_shouldIGo", methods=["GET", "POST"])
def shouldIGo():
    """Called constantly by javascript to check if all of the users are ready to begin the game"""
    
    match_id = request.args["match_id"]
    
    # if game has started, direct them
    return jsonify({"status" : Match.get(id=match_id).has_started })


#THE GAME PAGE - HERE'S WHERE THE ACTION STARTS

TURN_TIME = 25

def startGame(match_id):
    """Starts game and timer"""
    
    # updates the timer to the universal value for turn times 
    q = Match.update(timer=TURN_TIME).where(Match.id == match_id)
    q.execute()
    
    
    # get users in descending order by number of wins
    orderedUsers = User.select(User,User_Match).join(User_Match).where(User_Match.match_id == match_id).order_by(User.score.desc())

    # updates the turn order 
    q = Match.update(current_turn = orderedUsers[0].id).where(Match.id == match_id)
    q.execute()

    #initializes timer to keep track of user's time
    global timer
    timer = call_repeatedly(1, updateTime, match_id)
    
    
def call_repeatedly(interval, func, *args):
    """Allows us to call updateTime every second"""

    stopped = Event()
    def loop():
        while not stopped.wait(interval): # the first call is in `interval` secs
            func(*args)
    Thread(target=loop).start()    
    return stopped.set
    
def updateTime(match_id):
    """Every 1 second, updates "timer" value for mysql match row to decrease by 1"""

    # decrement time variable in mysql
    match = Match.get(Match.id == match_id)
    match.timer = match.timer - 1
    match.save()
        
    # if time has run out, game's over
    if match.timer <= 0:
        gameOver(match_id)
    
def gameOver(match_id):
    """Called when game ends; updates user scores"""
    
    # calling our global variable stops the timer
    timer()
    
    # updates the status of game_ended 
    q = Match.update(game_ended = True).where(Match.id == match_id)
    q.execute()
    
    # gets the id of the losing user 
    losingUser = Match.get(Match.id == match_id).current_turn_id
    
    # gets a list of users who participated in the game 
    listofusers = User_Match.select().where(User_Match.match_id == match_id)
    
    # gives everyone who participated in the game +1 onto their score
    for player in listofusers:
        q = User.update(score = (User.score + 1)).where(User.id == player.user_id)
        q.execute()
    
    # takes away 2 from the player who lost so their net change in score is -1
    q = User.update(score = (User.score - 2)).where(User.id == losingUser)
    q.execute()
      
@app.route("/play", methods=["GET", "POST"])
def play():
    """Renders play template if user is in match"""
    # if user submitted letter
    match_id = request.args.get("match_id")

    if request.method == "POST":
        
        # if you inputted nothing, you lose        
        if not request.form.get("letter"):
            gameOver(match_id)
            return render_template('play.html')
        
        # gets the match info and letter submitted 
        letter = request.form.get("letter").lower()

        match = Match.get(Match.id == match_id)
    
        # error checking - make sure person who submitted word is current user
        current_turn_id = match.current_turn_id
        if not session["user_id"] == current_turn_id:
            gameOver(match_id)
            return render_template('play.html')
    
        # make sure letter is a letter and it's a single character
        if not letter.isalpha() and len(letter) == 1:
            gameOver(match_id)
            return render_template('play.html')

        # update letter in match row
        new_word = match.current_word + letter
        q = Match.update(current_word = new_word).where(Match.id == match_id)
        q.execute()
        
        # determine if user loses or game continues
        checked_word = checkWord(new_word)
        
        # check if letter completes word (and word is 4 or more chars)
        if checked_word == 1:
            gameOver(match_id)
            return render_template('play.html')
        
        # or if there are no words that could be made with those letters
        elif checked_word == 2:
            gameOver(match_id)
            return render_template('play.html')
        
        # else, checked_word == 0, turn is ok and next person's turn
        else:
            # find next player whose turn it is by getting users, finding position of current one, and getting next one
            users = User.select(User,User_Match).join(User_Match).where(User_Match.match_id == match_id).order_by(User.score.desc(), User.username)
            numTurn = 0
            
            for i, j in enumerate(users):
                if j.id == current_turn_id:
                    numTurn = i
            
            # find next user, accounting for wrap around (i.e. if previous user was last, go to first one)
            next_turn = (numTurn + 1) % len(users)
            next_user = users[next_turn]
            
            # update values in mySQL to move to the next user and restart the timer 
            
            q = Match.update(current_turn=next_user).where(Match.id == match_id)
            q.execute()
            q = Match.update(timer=TURN_TIME).where(Match.id == match_id)
            q.execute()

    # gets all of the users currently involved in the match 
    users = User_Match.select().where(User_Match.match_id == match_id)
    
       
    # error checking - make sure user trying to see page is part of game
    allowed = False
    for user in users:
        if user.user_id == session["user_id"]:
            allowed = True
        
    if not allowed:
        return render_template('getoutahere.html')
    
    return render_template('play.html')
        
@app.route("/_gameUpdates", methods=["GET", "POST"])
def getGameUpdates():
    
    """Returns current game data, requires passing in match_id"""
    # gets the match id 
    match_id = request.args.get("match_id")
    # gets the information from the match 
    match = Match.select().where(Match.id == match_id).dicts()
    # gets the user information and orders the user by their score 
    users = User.select(User,User_Match).join(User_Match).where(User_Match.match_id == match_id).order_by(User.score.desc(), User.username).dicts()
    #gets whether it's users turn 
    myTurn = (Match.get(Match.id == match_id).current_turn_id == session["user_id"])
    
    # returns the information
    return jsonify({'match':list(match), 'users':list(users), 'myStatus': myTurn})

    
@app.route("/playAI", methods=["GET", "POST"])
def playAI():
    """Play against the AI"""
        
    data = {}
    error = None
    
     # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("letter"):
            error = 'Must provide a letter'
            
        if not len(request.form.get("letter")) == 1 and request.form.get("letter").isalpha():
            error = 'Must provide only a single letter'
           
        else:  
            data["first_time"] = False
            
            ai = AI()
            
            current_word = User.get(User.id == session["user_id"]).ai_word
            current_word += request.form.get("letter")
            current_word = current_word.lower()
            
            q = User.update(ai_word=current_word).where(User.id == session["user_id"])
            q.execute()
            
            data["current_word"] = current_word
            
            check = checkWord(current_word)
            if check == 0:
                
                # word is ok, computer should pick word
                
                data["game_over"] = False
            
                selectedWord = ai.getWord(current_word)
                q = User.update(ai_word=selectedWord).where(User.id == session["user_id"])
                q.execute()
                data["current_word"] = selectedWord
                
                # now check computer's word
                check = checkWord(selectedWord)
                if check == 0:
                    data["game_over"] = False
                    data["message"] = "M(AI)lan picked: " + selectedWord[-1] + ". Pick a new letter." 

                elif check == 1:
                    data["game_over"] = True
                    data["message"] = "You win! m(AI)lan completed a word."
                
                else:
                    data["game_over"] = True
                    data["message"] = "You win! m(AI)lan's word is invalid."
    
                
            
            elif check == 1:
                
                data["game_over"] = True
                data["message"] = "You lose! You made a word!"
                
            else:
                
                data["game_over"] = True
                data["message"] = "You lose! There's no word that can be made from your letters!"
                
            return render_template('ai.html', data=data, error=error)
        
        

    # else if user reached route via GET (as by clicking a link or via redirect) - means its a new game
    else:
        q = User.update(ai_word="").where(User.id == session["user_id"])
        q.execute()
        data["current_word"] = ""
        data["first_time"] = True
        
       # return render_template(word="a")
        return render_template('ai.html',data=data, error=error)

# returns 0 on success, 1 on word completion, 2 on word failure 
def checkWord(word):
    
    # check if letter completes word (and word is 4 or more chars)
    if len(word) >= 4 and trie.has_key(word):
        return 1
        
    # or if its not a word
    elif len(trie.keys(prefix=word)) == 0:
        return 2
    
    #otherwise it's fine 
    return 0
    

if __name__ == '__main__':
    app.run(debug=True)


