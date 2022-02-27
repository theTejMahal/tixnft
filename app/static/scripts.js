/** 
* Returns a parameter from the user's current url
* Usage: getParameterByName('match_id') returns the 4 if the url has /?match_id=4
* Source: http://stackoverflow.com/questions/901115/how-can-i-get-query-string-values-in-javascript
*/
function getParameterByName(name, url) {
    if (!url) {
      url = window.location.href;
    }
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

/**
 * Gets the table of games available to be joined
 * Updates the innerHTMl in the "joinroomid" div in joinroom.html to display the table
 * Usage: call getJoinGames()
*/
function getJoinGames() {

    var table="<table class='table table-striped'><thead><tr><th>Game Name</th><th>Number of Players</th><th>Join Room</th></tr></thead><tbody>";
    $.getJSON(Flask.url_for("getGames"))
    .done(function(data, textStatus, jqXHR) {
        games = data["games"];
        for (var i = 0; i < games.length; i++)
        {
            var url = "<a href=" + Flask.url_for("waitingRoom", {match_id:games[i]['id']}) + ">Join Game</a>";
            
            table += "<tr><td>" + games[i]['name'] + "</td><td>" + games[i]['num_players'] + "<td>" + url + "</td>";
        }
        table += "</tbody><tfoot><tr><td colspan='3'></td></tr></tfoot></table>";
        
        document.getElementById("joinroomid").innerHTML = table;

    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
}

/**
* Calls the getJoinGames function every second
* Facilitates dynamic updating of the joinroom html page so the table of available games is always up-to-date
*/
function callJoinGames() {
    
    getJoinGames();
    var myVar = setInterval(getJoinGames, 1000);

}

/**
 * Gets the table of users in the current match and their status
 * Updates the innerHTMl in the "waitingroomid" div in waitingroom.html to display the table
 * If all users in the match have status Ready (checked using ShouldIGo python function), calls play function in python
 * Usage: call getWaitingRoom()
*/
function getWaitingRoom() {

    var table="<table class='table table-striped'><thead><tr><th>Username</th><th>User Status</th></tr></thead><tbody>";
    var match_id = getParameterByName('match_id');
    
    $.getJSON(Flask.url_for("getWaiting", {match_id: match_id}))
    .done(function(data, textStatus, jqXHR) {
        players = data["players"];
        for (var i = 0; i < players.length; i++)
        {
            table += "<tr><td>" + players[i]['username'] + "</td><td>" + players[i]['status'] + "</td></tr>";
        }
        table += "</tbody><tfoot><tr><td colspan='2'></td></tr></tfoot></table>";
        document.getElementById("waitingroomid").innerHTML = table;

    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
    
    
    $.getJSON(Flask.url_for("shouldIGo", {match_id: match_id}))
    .done(function(data, textStatus, jqXHR) {
        
        if(data['status'] == true){
            allowedToLeave = true;
            window.location = Flask.url_for("play", {match_id: match_id});
        }

    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });
    
 
}


/**
* Calls the getWaitingRooms function every second
* Facilitates dynamic updating of the waitingroom html page so the table of users in match is always up-to-date
*/
function callWaitingRoom() {
    getWaitingRoom();
    var myVar = setInterval(getWaitingRoom, 1000);

}

/**
 * Calls the startGamePressed function in python
 * Usage: This function is only called when users press the "Start Game" button from waitingroom.html
*/
function startGamePressed(){
    var match_id = getParameterByName('match_id');
    $.getJSON(Flask.url_for("startGamePressed", {match_id:match_id}))
    .done(function(data, textStatus, jqXHR) {
    });
}


/**
 * Updates play.html by calling getGameUpdates python function and accessing match and user data
 * Displays users and scores, highlighting user whose turn it is, displays current word, displays timer
 * Displays form to submit next letter if it's your turn
 * Usage: call inPlay()
*/
function inPlay(){
    var match_id = getParameterByName('match_id');
    
    $.getJSON(Flask.url_for("getGameUpdates", {match_id: match_id}))
    .done(function(data, textStatus, jqXHR) {
        match = data["match"];
        users = data["users"];
        timerVal = match[0]['timer'];
        myStatus = data["myStatus"];
        
        if (match[0]['game_ended'] == true){
            overhead = "Game Over! &times; <br>";
            var lostUser = "Loser: ";
            var wonUsers = "Winners:";
            // loop through all the users
            for (var i = 0; i < users.length; i++)
            {
                // highlight the user whose turn it is by making a primary button
                if (users[i]['user'] == match[0]['current_turn']){
                    lostUser += users[i]['username'];
                }
                // if not your turn, make a default button
                else {
                    wonUsers += " "
                    wonUsers += users[i]['username'];
                }
            }
            wonUsers += "."
            if (match[0]['num_players'] == 1){
                wonUsers = "Winners: none :("
            }
            overhead += lostUser + ". " + "\n" + wonUsers;
            document.getElementById("myNav").style.width = "100%";
            document.getElementById("myNav").innerHTML = "<div class='overlay-content'><a href='" + Flask.url_for('index') + "'>" + overhead + "</a></div>";
        }
        else{
            var usershead = "<div class='btn-toolbar' role='toolbar' aria-label='...'>";
            // loop through all the users
            for (var i = 0; i < users.length; i++)
            {
                // highlight the user whose turn it is by making a primary button
                if (users[i]['user'] == match[0]['current_turn']){
                    usershead += "<button class='btn btn-primary' type='button'>";
                }
                // if not your turn, make a default button
                else {
                    usershead += "<button class='btn btn-default' type='button'>"; 
                }
                usershead += users[i]['username'];
                usershead += "&nbsp<span class='badge'>";
                usershead += users[i]['score'];
                usershead += " </span></button>";
            }
            usershead += "</div>";
    
            
            // if user's turn, display the form to submit another letter
            if(myStatus === true && document.getElementById("playSubmitDisplay").innerHTML === ""){
                
                var submitDisplay = "<form action='" + Flask.url_for('play',{match_id:match_id}) + "' method='post' name='getLetter'><fieldset>";
                submitDisplay += "<div class='form-group'><input autocomplete='off' autofocus class='form-control' name='letter' id='letter' placeholder='Letter' maxlength='1' type='text' value=''/></div>";
                submitDisplay += "<div class='form-group'><input class='btn btn-default' type='submit'></input></div></fieldset></form>";
                document.getElementById("playSubmitDisplay").innerHTML = submitDisplay;

            }
            else if (myStatus === false && document.getElementById("playSubmitDisplay").innerHTML !== ""){
                var submitDisplay = "";
                document.getElementById("playSubmitDisplay").innerHTML = submitDisplay;
            }
            
            document.getElementById("playUsersDisplay").innerHTML = usershead;

        }
        
        document.getElementById("playCurrentWordDisplay").innerHTML = "<h1>Current Word: " + match[0]['current_word'] + "</h1>";
        
        document.getElementById("playTimerDisplay").innerHTML = "<p>" + timerVal + " seconds remaining</p>";
        
        // display submission form
        

        
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());
    });


}


/**
* Calls the inPlay function 1x per second
* Facilitates dynamic updating of the play html page so the timer, user turn, and current word are always up-to-date
*/        
function callInPlay() {
    inPlay();
    var myVar = setInterval(inPlay, 1000);

}