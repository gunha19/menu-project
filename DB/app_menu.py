import datetime
import re
import requests
from flask import Flask, redirect, render_template, url_for, request, flash, session
from DB_handler import DBModule

app = Flask(__name__, template_folder="templates")
DB = DBModule()
app.secret_key = "secret!"


# 급식 데이터 가져오기 함수
def get_meal_data(date):
    year = date.strftime("%Y")
    month = date.strftime("%m")
    day = date.strftime("%d")

    # NEIS API 정보
    SD_SCHUL_CODE = "8140089"  # 서령고 코드
    KEY = "fa9a6a4314a0489a8ae94a49063f93d1"  # 인증키
    ATPT_OFCDC_SC_CODE = "N10"  # 충남교육청 코드
    YMD = year + month + day  # 날짜 조합

    url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&KEY={KEY}&pIndex=1&pSize=100&ATPT_OFCDC_SC_CODE={ATPT_OFCDC_SC_CODE}&SD_SCHUL_CODE={SD_SCHUL_CODE}&MLSV_YMD={YMD}"

    res = requests.get(url).json() #요청을 requests.get(url)로 보내고 json 형태로 데이터 처리

    # 급식 정보 초기화
    breakfast, lunch, dinner = "조식 정보 없음", "중식 정보 없음", "석식 정보 없음"

    try:
        meals = res["mealServiceDietInfo"][1]["row"] #급식정보 추출
        for meal in meals: #반복문을 통해 급식 메뉴 확인인
            if meal["MMEAL_SC_NM"] == "조식": #값에 따라 조식 중식 석식 구별
                breakfast = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 필요없는 숫자 제거
            elif meal["MMEAL_SC_NM"] == "중식":
                lunch = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 필요없는 숫자 제거
            elif meal["MMEAL_SC_NM"] == "석식":
                dinner = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 필요없는 숫자 제거
    except KeyError:
        pass  # 데이터가 없을 경우 기본값 유지

    return {"breakfast": breakfast, "lunch": lunch, "dinner": dinner, "date": YMD}


# 날짜와 요일 구하는 함수인데 인터넷 보고 해서 이해 안됨
def get_week_dates(selected_date):
    #날짜 선택 안할 시 당일의 날짜 사용
    if not selected_date:
        selected_date = datetime.datetime.now()

    # 이번 주의 월요일 날짜 계산
    start_of_week = selected_date - datetime.timedelta(days=selected_date.weekday())

    # 월요일부터 금요일까지의 날짜 계산
    week_dates = [((start_of_week + datetime.timedelta(days=i)).strftime('%A'), start_of_week + datetime.timedelta(days=i)) for i in range(5)]


    # 요일을 한글로 바꾸기
    week_dates = [(date[0], date[1]) for date in week_dates]
    week_dates = [("월요일", week_dates[0][1]), ("화요일", week_dates[1][1]), ("수요일", week_dates[2][1]), ("목요일", week_dates[3][1]), ("금요일", week_dates[4][1])]

    return week_dates



@app.route("/", methods=["GET", "POST"])
def index():
    user = session.get("uid", "Login")  # 세션에서 사용자 정보 가져오기, 없으면 "Login"

    # 당일의 날을 기본으로 함
    selected_date = datetime.datetime.now()

    
    if request.method == "POST":
        selected_date = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d") #날짜 선택에 따른 급식 정보와 날짜

    # 이번 주의 월요일부터 금요일까지 날짜와 요일 구하기
    week_dates = get_week_dates(selected_date)

    # 급식 데이터 가져오기
    meal_data = get_meal_data(selected_date)

    return render_template("index.html", user=user, meal_data=meal_data, week_dates=week_dates)

#데이터베이스에서 게시물 목록 가져와서 post_list로 전송하여 목록 표시
@app.route("/list")
def post_list():
    post_list = DB.post_list()
    length = len(post_list) if post_list else 0
    return render_template("post_list.html", post_list=post_list.items(), length=length)


@app.route("/post/<string:pid>")
def post(pid):
    post = DB.post_detail(pid) #DB에서 정보 갖고옴
    return render_template("post_detail.html", post=post) # 가져온 정보를 post_detail.html 전달달


@app.route("/logout")
def logout():
    session.pop("uid", None)  #로그아웃 시 uid 삭제함
    return redirect(url_for("index")) # 로그아웃 시 홈페이지
    


@app.route("/login")
def login():
    if "uid" in session:
        return redirect(url_for("index")) # 로그인 일 떄 홈페이지로 보냄
    return render_template("login.html") # 비로그인 일 때 로그인으로 보냄


@app.route("/login_done", methods=["GET"])
def login_done():
    uid = request.args.get("id") #로그인 아이디 받아옴
    pwd = request.args.get("pwd")#로그인 비밀번호 받아옴
    if DB.login(uid, pwd): #로그인 판단 여부
        session["uid"] = uid
        return redirect(url_for("index")) #로그인 성공 시 uid 저장 및 홈페이지로 보냄
    else:
        flash("아이디가 없거나 비밀번호가 틀립니다.") #로그인 실패 시 나오는 말
        return redirect(url_for("login")) # 다시 로그인으로 보냄


@app.route("/signin")
def signin():
    return render_template("signin.html")


@app.route("/signin_done", methods=["GET"])
def signin_done():
    if "uid" in session: #로그인 상태 여부 확인
        return redirect(url_for("index")) #로그인 일 때 홈페이지
    #유저가 회원가입에 입력한 데이터를 가져옴
    email = request.args.get("email")
    uid = request.args.get("id")
    pwd = request.args.get("pwd")
    name = request.args.get("name")
    #정보를 DB에 저장함
    if DB.signin(email=email, _id_=uid, pwd=pwd, name=name): 
        session["uid"] = uid #회원가입 성공 시 uid 세션에 저장
        return redirect(url_for("index"))   
    #DB 저장 실패 시
    else:
        flash("이미 존재하는 아이디 입니다.")
        return redirect(url_for("signin"))


@app.route("/write")
def write():
    if "uid" in session:
        return render_template("write_hope.html") # 로그인 상태일 때 희망사항 작성 페이지로 갈수있음
    return redirect(url_for("login")) # 비 로그인 상태일 때는 로그인으로 보냄


@app.route("/write_done", methods=["POST"])
def write_done():
    title = request.form.get("title") #유저가 입력한 제목을 가져옴
    contents = request.form.get("contents") #유저가 입력한 내용을 가져옴
    uid = session.get("uid") #유저의 uid를 가져옴
    DB.write(title, contents, uid) # 제목, 내용, uid 를 DB에 저장
    return redirect(url_for("index")) # 저장 후 홈페이지로 보냄


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True) #실행 코드