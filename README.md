# acmicpc.cc

백준 온라인 저지 전적 검색, 통계 분석

## 개발환경 세팅

```bash
$ sudo apt install python3 python3-pip
$ pip3 install virtualenv
$ git clone git@github.com:MoonHyuk/acmicpc.cc.git
$ cd acmicpc.cc
$ virtualenv .venv
$ . .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```

postegre를 로컬에 띄운 후 환경변수에 다음 두개를 추가해준다.  
`APP_SETTINGS = config.DevelopmentConfig`  
`DATABASE_URL = db 서버 주소`  

```bash
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py db upgrade
$ python application.py
```
