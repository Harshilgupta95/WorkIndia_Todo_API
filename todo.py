import os
from flask import Flask,request,jsonify,make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import jwt
import datetime
from functools import wraps

app=Flask(__name__)
app.config['SECRET_KEY']='mysecretkey'

basedir=os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'dbTodo.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    agent_id=db.Column(db.String(50),unique=True)
    password=db.Column(db.String(80))

class Todo(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(100))
    description=db.Column(db.String(200))
    category=db.Column(db.String(100))
    due_date=db.Column(db.String(10))  #DateTime showing error so used String dataType
    user_id=db.Column(db.Integer)

def token_required(f):
    @wraps(f)
    def myfun(*args,**kwargs):
        token=None
        if 'x-access-token' in request.headers:
            token=request.headers['x-access-token']
        if not token:
            return jsonify({'message':'Token is missing'}),401
        try:
            data=jwt.decode(token,app.config['SECRET_KEY'])
            curr_user=User.query.filter_by(agent_id=data['agent_id']).first()
        except:
            return jsonify({'message':'Invalid Token'}),401
        return f(curr_user,*args,**kwargs)
    return myfun



@app.route('/app/agent',methods=['POST'])
def create_user():
    data=request.get_json()

    hashed_password=generate_password_hash(data['password'],method='sha256')
    new_user=User(agent_id=data['agent_id'],password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'Status':'account created','status_code':200})

@app.route('/app/agent/auth')
def login():
    auth=request.authorization
    if not auth or not auth.username or not auth.password:
        return jsonify({'status':'failure','status_code':401})
    user=User.query.filter_by(agent_id=auth.username).first()
    if not user:
        return jsonify({'status':'failure','status_code':401})
    if check_password_hash(user.password,auth.password):
        token=jwt.encode({'agent_id':user.agent_id,'exp':datetime.datetime.utcnow()+datetime.timedelta(minutes=30)},app.config['SECRET_KEY'])

        return jsonify({'status':'success','agent_id':token.decode('UTF-8'),'status_code':200})
    return jsonify({'status': 'failure', 'status_code': 401})


@app.route('/app/sites/list',methods=['POST'])
# @token_required
def add_todo():
    data=request.get_json()
    new_todo=Todo(title=data['title'],description=data['description'],category=data['category'],due_date=data['due_date'],user_id=data['user_id'])
    # new_todo=Todo( "Read a Book","Reading","Personal",datetime(2020, 6, 5, 8, 10, 10, 10),1)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'Status':'Todo created','status_code':200})

@app.route('/app/sites/list/<user_id>', methods=['GET'])
# @token_required
def get_todo(user_id):
    todo=Todo.query.filter_by(id=user_id).first()
    if not todo:
        return jsonify({'message':'No Todo found'})
    todo_data={}
    todo_data['id']=todo.id
    todo_data['title']=todo.title
    todo_data['description']=todo.description
    todo_data['category']=todo.category
    todo_data['user_id']=todo.user_id
    return jsonify(todo_data)


@app.route('/app/sites/list/', methods=['GET'])
# @token_required
def get_all_todo():
    todos=Todo.query.all()
    op=[]
    for todo in todos:
        todo_data={}
        todo_data['id']=todo.id
        todo_data['title']=todo.title
        todo_data['description']=todo.description
        todo_data['category']=todo.category
        todo_data['user_id']=todo.user_id
        op.append(todo_data)
    return jsonify({'todos':op})

if __name__=='__main__':
    app.run(debug=True)