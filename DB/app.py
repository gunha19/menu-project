

import os
print("Current working directory:", os.getcwd())


from flask import Flask, redirect,render_template, url_for,request, flash, session
from DB_handler import DBModule
app = Flask(__name__, template_folder="templates")
DB = DBModule()
app.secret_key="secret!"




@app.route("/")
def index():
  if "uid" in session:
    user = session["uid"]
  else:
    user="Login"
  return render_template("index.html", user = user)

@app.route("/list")
def post_list():
  post_list = DB.post_list()
  if post_list == None:
    length = 0
  else:
    length=len(post_list)  
  return render_template("post_list.html", post_list = post_list.items(), length = length)

@app.route("/post/<string:pid>")
def post(pid):
  post = DB.post_detail(pid)
  return render_template("post_detail.html",post=post)


@app.route("/logout")
def logout():
  if "uid" in session:
    session.pop("uid")
    return redirect(url_for("index"))
  else:
    return redirect(url_for("login"))

@app.route("/login")
def login():
  if "uid" in session:
    return redirect(url_for("index"))
  return render_template("login.html")
  

@app.route("/login_done",methods=["get"])
def login_done():
  uid = request.args.get("id")
  pwd = request.args.get("pwd")
  if DB.login(uid,pwd):
    session["uid"] = uid
    return redirect(url_for("index"))
  else:
    flash("아이디가 없거나 비밀번호가 틀립니다.")
    
    
    return redirect(url_for("login"))

@app.route("/signin")
def signin():
  return render_template("signin.html")

@app.route("/signin_done", methods=["get"])
def signin_done():
  if "uid" in session:
    return redirect("index") #로그인 있으면 index로 보냄
  email = request.args.get("email")
  uid = request.args.get("id")
  pwd = request.args.get("pwd")
  name = request.args.get("name")
  if DB.signin(email = email,_id_=uid, pwd=pwd,name=name):
    session["uid"] = uid
    return redirect (url_for("index"))
  else:
    flash("이미 존재하는 아이디 입니다.")
    return redirect (url_for("signin"))


@app.route("/user/<uid>")
def user(uid):
  pass

@app.route("/write") 
def write_hope():
  if "uid" in session:
    return render_template("write_hope.html")
  else:
    return redirect(url_for("login"))

@app.route("/write_done", methods = ["GET"])
def write_done():
  title = request.args.get("title")
  contents = request.args.get("contents")
  uid = session.get("uid")
  DB.write_post(title, contents, uid)
  return redirect(url_for("index"))

if __name__ =="__main__":
  app.run(host="0.0.0.0", debug=True)
#

