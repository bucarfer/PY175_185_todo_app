from werkzeug.exceptions import NotFound
from uuid import uuid4
from functools import wraps
import os

from flask import (
    flash,
    Flask, 
    redirect, 
    render_template,
    request, 
    session,
    url_for,
) 

from todos.utils import (
    delete_todo_by_id,
    delete_list_by_id,
    error_for_list_title, 
    error_for_todo_title,
    find_list_by_id, 
    find_todo_by_id,
    is_list_completed,
    is_todo_completed,
    mark_all_completed,
    sort_items,
    todos_remaining,
)

app = Flask(__name__)
app.secret_key='secret1' #Set up a secret key

def require_list(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        list_id = kwargs.get('list_id')
        lst = find_list_by_id(list_id, session['lists'])
        if not lst:
            raise NotFound(description='List not found')
        return f(lst=lst, *args, **kwargs)

    return decorated_function

def require_todo(f):
    @wraps(f)
    @require_list
    def decorated_function(lst, *args, **kwargs):
        todo_id = kwargs.get('todo_id')
        todo = find_todo_by_id(todo_id, lst['todos'])
        if not todo:
            raise NotFound(description='Todo not found')
        return f(lst=lst, todo=todo, *args, **kwargs)
    
    return decorated_function

@app.context_processor
def list_utilities_processor():
    return dict(
        is_list_completed=is_list_completed
    )

@app.before_request
def initialize_session():
    if 'lists' not in session:
        session['lists'] = []

# redirect start page
@app.route("/")
def index():
    return redirect(url_for('get_lists'))

@app.route("/lists")
def get_lists():
    lists = sort_items(session['lists'], is_list_completed)
    return render_template('lists.html',
                            lists=lists, 
                            todos_remaining=todos_remaining)

# create a new todo list
@app.route("/lists", methods=["POST"])
def create_list():
    title = request.form["list_title"].strip() 
    error = error_for_list_title(title, session['lists'])
    if error:
        flash(error, "error")
        return render_template("new_list.html", title=title)
    
    session['lists'].append({ #saves lists in session
        'id': str(uuid4()),
        'title': title, 
        'todos': [],
    })

    flash("The list has been created.", "success")
    session.modified = True
    return redirect(url_for('get_lists'))

@app.route("/lists/new") 
def add_todo_list():
    return render_template('new_list.html')

@app.route("/lists/<list_id>")
@require_list
def show_list(lst, list_id):
    lst['todos'] = sort_items(lst['todos'], is_todo_completed)
    return render_template('list.html', lst=lst)

# create a new todo object
@app.route("/lists/<list_id>/todos", methods=["POST"])
@require_list
def create_todo(lst, list_id):
    todo_title = request.form["todo"].strip() ### this line gets the value of todo, "todo": "Buy milk", <input name="todo">, line 47 list.html

    error = error_for_todo_title(todo_title)
    if error:
        flash(error, "error")
        return render_template("list.html", lst=lst)

    lst["todos"].append({ ## session["lists"] = [
                          #     {
                          #         "id": "...",
                          #         "title": "...",
                          #         "todos": []
                          #     }
                          # ]. what is session? a dictionary where we store different objects?
        'id': str(uuid4()),
        'title': todo_title,
        'completed': False, 
    })

    flash("The todo object was added.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id)) #from show_list(list_id)

#Toggle completion status of a todo
@app.route("/lists/<list_id>/todos/<todo_id>/toggle", methods=["POST"])
@require_todo
def update_todo_status(lst, todo, list_id, todo_id):

    todo['completed'] = (request.form['completed'] == 'True') #'True' becuase submitted HTML form is all strings

    flash("the todo has been updated.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))

#Delete a todo item
@app.route("/lists/<list_id>/todos/<todo_id>/delete", methods=["POST"])
@require_todo
def delete_todo(lst, todo, list_id, todo_id):  
    delete_todo_by_id(todo_id, lst)

    flash("The todo has been deleted", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))

#Complete all
@app.route("/lists/<list_id>/complete_all", methods=['POST'])
@require_list
def mark_all_todos_completed(lst, list_id):
    mark_all_completed(lst)

    flash("All todos have been completed.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))

#edit a list 
@app.route("/lists/<list_id>/edit")
@require_list
def edit_list(lst, list_id):
    return render_template('edit_list.html', lst=lst)

#delete list 
@app.route("/lists/<list_id>/delete", methods=["POST"])
@require_list
def delete_list(lst, list_id):
    delete_list_by_id(list_id, session['lists'])

    flash("The list has been deleted.", "success")
    session.modified = True
    return redirect(url_for('get_lists'))

#enter new title
@app.route("/lists/<list_id>", methods=['POST']) 
@require_list
def update_list(lst, list_id):
    title = request.form["list_title"].strip()
    
    error = error_for_list_title(title, session['lists'])
    if error:
        flash(error, "error")
        return render_template('edit_list.html', lst=lst, title=title)
    
    lst['title'] = title
    flash("The list title has been modified.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))

if __name__ == "__main__":
    if os.environ.get('FLASK_ENV') == 'production' :
        app.run(debug=False)
    else:
        app.run(debug=True, port=5003)