import pyrebase
import json
import os
import uuid
import datetime  # datetime 모듈 import
from datetime import datetime
import pytz

class DBModule:
    def __init__(self):
        # 현재 파일(DB_handler.py)이 있는 디렉토리 경로를 기준으로 firebase.json 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        firebase_path = os.path.join(current_dir, "auth/firebase.json")
        
        # firebase.json 파일 열기
        with open(firebase_path) as f:
            config = json.load(f)

        # Firebase 초기화
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()

    def login(self, uid, pwd):
        users = self.db.child("users").get().val()
        try: 
            usersinfo = users[uid]
            if usersinfo["pwd"] == pwd:
                return True
            else:
                return False
        except:
            return False

    def signin_verification(self, uid):
        users = self.db.child("users").get().val()
        for i in users:
            if uid == i:
                return False
        return True

    def signin(self, _id_, pwd, name, email):
        information = {
            "pwd": pwd,
            "uname": name,
            "email": email
        }

        if self.signin_verification(_id_):
            self.db.child("users").child(_id_).set(information)
            return True
        else:
            return False

    ###################################################
    def format_time(self, time_str):
        # 기존 형식 '2024.12.22.20:53'을 '2024년 12월 22일 20시 53분'으로 변환
        time_obj = datetime.strptime(time_str, "%Y.%m.%d.%H:%M")
        return time_obj.strftime("%Y년 %m월 %d일 %H시 %M분")
###########################################################

    def write(self, title, contents, uid):
        current_time = datetime.now().strftime("%Y.%m.%d.%H:%M")
        #############################
        formatted_time = self.format_time(current_time)
        #########################################
        pid = str(uuid.uuid4())[:7]
        print(pid)

    # Firestore에서 posts 데이터를 가져오기
        posts = self.db.child("posts").get().val()

    # posts가 None이 아니고, dict 형식인 경우에만 처리
        max_sequence = 0
        if posts and isinstance(posts, dict):
            for post in posts.values():
                if post.get('Sequence', 0) > max_sequence:
                    max_sequence = post['Sequence']
    
    # 새로운 Sequence 값 할당 (최대 Sequence + 1)
        new_sequence = max_sequence + 1

    # 포스트 정보 준비
        information = {
            "title": title,
            "contents": contents,
            "uid": uid,
            "time": formatted_time,
            "Sequence": new_sequence  # 새로운 Sequence 값 설정
        }

    # 포스트 데이터 Firestore에 저장
        self.db.child("posts").child(pid).set(information)


    def post_list(self):
    # Firestore에서 posts 데이터를 가져오기
        post_lists = self.db.child("posts").get().val()
    
        

    # post_lists가 None이 아니고, dict 형식인 경우에만 처리
        if post_lists and isinstance(post_lists, dict):
        # Sequence 값 기준으로 내림차순으로 정렬
            sorted_posts = sorted(post_lists.items(), key=lambda x: x[1].get('Sequence', 0), reverse=True)
            sorted_posts_dict = {post[0]: post[1] for post in sorted_posts}
            return sorted_posts_dict
        else:
            print("Error: posts 데이터가 dict 형태가 아닙니다.")
            return {}

    

    def post_detail(self, pid):
        post = self.db.child("posts").get().val()[pid]
        return post

    def get_user(self, uid):
        pass
