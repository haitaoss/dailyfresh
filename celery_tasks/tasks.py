# 使用celery
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")
django.setup()
# celery -A celery_tasks.tasks worker -i info

# 创建一个Celery类的实例对象
# 参数一：随便的字符串，但最好是py文件的路径，这是规范
# 常数二：中间人（redis，RabbitMQ等等）。这里表示使用redis的8号数据库
# celery_tasks.tasks 指的是celery_tasks包下面的tasks的py文件
app = Celery('celery_tasks.tasks', broker='redis://127.0.0.1:6379/8')


@app.task  # 使用task对函数进行装饰，这样子就能实现让中间人帮我们处理任务
# 定义任务函数
def send_register_active(to_email, username, token):
    """"发送激活邮件"""

    # 组织邮件信息
    subject = '天天生鲜欢迎信息'
    message = ''
    from_email = settings.EMAIL_FROM  # 发件人
    recevier = [to_email]  # 收件人的邮箱，可以是多个
    html_mesage = "<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的邮箱<br/><a href='http://192.168.205.148:8080/user/active/%s'>http://192.168.205.148:8080/user/active/%s</a>" % (
        username, token, token)
    send_mail(subject, message, from_email, recevier, html_message=html_mesage)
    time.sleep(5)
