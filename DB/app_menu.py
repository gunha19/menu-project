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
    SD_SCHUL_CODE = "8140089"  # 서령고등학교 코드
    KEY = "fa9a6a4314a0489a8ae94a49063f93d1"  # 인증키
    ATPT_OFCDC_SC_CODE = "N10"  # 충남교육청 코드
    YMD = year + month + day  # 날짜 조합

    url = f"https://open.neis.go.kr/hub/mealServiceDietInfo?Type=json&KEY={KEY}&pIndex=1&pSize=100&ATPT_OFCDC_SC_CODE={ATPT_OFCDC_SC_CODE}&SD_SCHUL_CODE={SD_SCHUL_CODE}&MLSV_YMD={YMD}"

    # API 요청 및 데이터 처리
    res = requests.get(url).json()

    # 급식 정보 초기화
    breakfast, lunch, dinner = "조식 정보 없음", "중식 정보 없음", "석식 정보 없음"

    try:
        meals = res["mealServiceDietInfo"][1]["row"]
        for meal in meals:
            if meal["MMEAL_SC_NM"] == "조식":
                breakfast = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 숫자 제거
            elif meal["MMEAL_SC_NM"] == "중식":
                lunch = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 숫자 제거
            elif meal["MMEAL_SC_NM"] == "석식":
                dinner = re.sub(r"\(.*?\)", "", meal["DDISH_NM"]).replace("<br/>", "\n")  # 숫자 제거
    except KeyError:
        pass  # 데이터가 없을 경우 기본값 유지

    return {"breakfast": breakfast, "lunch": lunch, "dinner": dinner, "date": YMD}


# 이번 주의 월요일부터 금요일까지 날짜와 요일 구하는 함수
def get_week_dates(selected_date):
    # 선택된 날짜가 없으면 현재 날짜를 사용
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


# Flask 라우팅
@app.route("/", methods=["GET", "POST"])
def index():
    user = session.get("uid", "Login")  # 세션에서 사용자 정보 가져오기, 없으면 "Login"

    # 기본적으로 오늘 날짜를 선택
    selected_date = datetime.datetime.now()

    # 사용자가 날짜를 선택하면 해당 날짜로 갱신
    if request.method == "POST":
        selected_date = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d")

    # 이번 주의 월요일부터 금요일까지 날짜와 요일 구하기
    week_dates = get_week_dates(selected_date)

    # 급식 데이터 가져오기
    meal_data = get_meal_data(selected_date)

    return render_template("index.html", user=user, meal_data=meal_data, week_dates=week_dates)


@app.route("/list")
def post_list():
    post_list = DB.post_list()
    length = len(post_list) if post_list else 0
    return render_template("post_list.html", post_list=post_list.items(), length=length)


@app.route("/post/<string:pid>")
def post(pid):
    post = DB.post_detail(pid)
    return render_template("post_detail.html", post=post)


@app.route("/logout")
def logout():
    session.pop("uid", None)  # 세션에서 "uid"를 삭제
    return redirect(url_for("index"))


@app.route("/login")
def login():
    if "uid" in session:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/login_done", methods=["GET"])
def login_done():
    uid = request.args.get("id")
    pwd = request.args.get("pwd")
    if DB.login(uid, pwd):
        session["uid"] = uid
        return redirect(url_for("index"))
    else:
        flash("아이디가 없거나 비밀번호가 틀립니다.")
        return redirect(url_for("login"))


@app.route("/signin")
def signin():
    return render_template("signin.html")


@app.route("/signin_done", methods=["GET"])
def signin_done():
    if "uid" in session:
        return redirect(url_for("index"))  # 로그인 있으면 index로 보냄
    email = request.args.get("email")
    uid = request.args.get("id")
    pwd = request.args.get("pwd")
    name = request.args.get("name")
    if DB.signin(email=email, _id_=uid, pwd=pwd, name=name):
        session["uid"] = uid
        return redirect(url_for("index"))
    else:
        flash("이미 존재하는 아이디 입니다.")
        return redirect(url_for("signin"))


@app.route("/write")
def write():
    if "uid" in session:
        return render_template("write_hope.html")
    return redirect(url_for("login"))


@app.route("/write_done", methods=["POST"])
def write_done():
    title = request.form.get("title")
    contents = request.form.get("contents")
    uid = session.get("uid")
    DB.write(title, contents, uid)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)