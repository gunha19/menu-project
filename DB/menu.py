from flask import Flask, render_template, request
import requests
import datetime
import re

app = Flask(__name__)

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

# 이번 주의 월요일부터 금요일까지 날짜 구하는 함수
def get_week_dates():
    today = datetime.datetime.now()
    # 이번 주의 월요일 날짜 계산
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
    # 월요일부터 금요일까지의 날짜 계산
    week_dates = [start_of_week + datetime.timedelta(days=i) for i in range(5)]
    
    return week_dates

# Flask 라우팅
@app.route("/", methods=["GET", "POST"])
def home():
    # 이번 주의 월요일부터 금요일까지 날짜 구하기
    week_dates = get_week_dates()

    # 선택된 날짜 (POST 요청이 있을 때 해당 날짜, 기본값은 월요일)
    selected_date = week_dates[0]
    if request.method == "POST":
        selected_date = datetime.datetime.strptime(request.form["date"], "%Y-%m-%d")

    # 급식 데이터 가져오기
    meal_data = get_meal_data(selected_date)
    
    return render_template("meal.html", meal_data=meal_data, week_dates=week_dates)
if __name__ == "__main__":
    app.run(debug=True)
