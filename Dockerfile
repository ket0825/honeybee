# Not for cronjob.
FROM ubuntu:22.04
LABEL version="1.0" author='ket'

COPY . /honeybee
# Dockerfile의 RUN 명령은 새로운 임시 레이어에서 실행되므로, 
# 이전 레이어에서 생성한 심볼릭 링크를 인식하지 못합니다.

RUN apt-get update\
&& apt-get install -y python3-pip cron wget sudo\
&& cd /usr/local/bin\
&& ln -s /usr/bin/python3 python\
&& wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -\
&& echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list\
&& apt-get update\
&& apt-get install -y google-chrome-stable

# container를 시작할 때의 기본 디렉토리를 설정하는 것임.
WORKDIR /honeybee

RUN rm -rf /var/lib/apt/lists/*\
&& pip install --no-cache-dir --upgrade pip\
&& pip install --no-cache-dir -r /honeybee/requirements.txt

CMD ["python", "product_link_crawler.py"]
# For debug.
# CMD ["bin/bash"]
# ENTRYPOINT "/bin/bash"

# For cronjob.
# FROM ubuntu:22.04
# LABEL version="1.0" author='ket'

# # 크론탭 실행을 위한 cron 설치
# RUN apt-get update\
# && apt-get install -y python3.9 python3-pip cron\
# && mkdir honeybee\
# && ln -s /usr/bin/python3.9 /honeybee/python

# # container를 시작할 때의 기본 디렉토리를 설정하는 것임.
# WORKDIR /honeybee
# COPY . ./honeybee
# COPY requirements.txt .
# RUN echo "0 * * * * root /usr/local/bin/python /honeybee/product_link_crawler.py >> /var/log/cron.log 2>&1" > /etc/cron.d/crontab\
# && rm -rf /var/lib/apt/lists/*\
# && pip install --upgrade pip\
# && pip install -r requirements.txt\
# && service cron start 
# # cron 서비스 시작 명령 추가

# # 크론탭 실행
# CMD cron -f && tail -f /var/log/cron.log

