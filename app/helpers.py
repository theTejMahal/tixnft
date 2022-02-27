from functools import wraps
from flask import redirect, render_template, request, session, url_for
from pytrie import SortedStringTrie as Trie
import sys
import os

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function
    
    
# initialize word list trie
trie = Trie()

# current_path = os.getcwd()
# if "/app" in current_path:
#     current_path = current_path.removesuffix("/app")
with open("words.txt") as word_file:
    for word in word_file:
        word = word.strip('\n')
        trie[word] = True