from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse  # 反向解析
from django.core.mail import send_mail  # 发送邮件的函数
from django.views.generic import View  # 类试图
from user.models import User  # 导入模型类
from django.conf import settings  # 导入settings
import re  # 正则匹配
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 导入加密的类
from itsdangerous import SignatureExpired  # 加密插件抛出的异常


# Create your views here.

# /user/register
def register(request):
    if request.method == "GET":
        """显示注册页面"""
        return render(request, 'register.html')
    if request.method == "POST":
        """处理注册信息"""
        # 获取表单数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 没有这个值就是None

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整。all方法是判断里面所有的都不为None才会返回true
            return render(request, 'register.html', {"errmsg": "数据不合法"})
        # 教研邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {"errmsg": "邮箱格式不合法"})
        # 校验是否勾选，
        if allow != 'on':
            return render(request, 'register.html', {"errmsg": "请同意协议"})

        # 进行业务处理：进行用户注册

        try:
            user = User.objects.get(username=username)
        except:
            user = None
        if user:
            return render(request, 'register.html', {"errmsg": "用户名已经被注册"})

        user = User.objects.create_user(username, password, email)
        user.is_active = 0  # 刚开始没有被激活
        user.save()
        # 返回应答
        return redirect(reverse('goods:index'))


class RegisterView(View):
    """注册"""

    def get(self, request):
        """显示注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """处理注册信息"""
        # 获取表单数据
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 没有这个值就是None

        # 进行数据校验
        if not all([username, password, email]):
            # 数据不完整。all方法是判断里面所有的都不为None才会返回true
            return render(request, 'register.html', {"errmsg": "数据不合法"})
        # 教研邮箱
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {"errmsg": "邮箱格式不合法"})
        # 校验是否勾选，
        if allow != 'on':
            return render(request, 'register.html', {"errmsg": "请同意协议"})

        # 进行业务处理：进行用户注册

        try:
            user = User.objects.get(username=username)
        except:
            user = None
        if user:
            return render(request, 'register.html', {"errmsg": "用户名已经被注册"})

        user = User.objects.create_user(username, email, password)
        user.is_active = 0  # 刚开始没有被激活
        user.save()

        # 发送激活邮件，包含激活链接：http://127.0.0.1:8080/user/active/id
        # 激活链接中，需要包含用户的身份信息并且要把身份信息进行加密
        # 加密用户的身份信息，生成激活的token
        serialezer = Serializer(settings.SECRET_KEY, 3600)  # 用户么加密，加密过期时间
        info = {'confirm': user.id}
        token = serialezer.dumps(info)

        token = token.decode()  # 默认的解码方式就是utf-8所以可以不写
        # 发邮件
        subject = '天天生鲜欢迎信息'
        message = ''
        from_email = settings.EMAIL_FROM  # 发件人
        recevier = [email]  # 收件人的邮箱，可以是多个
        html_mesage = "<h1>%s,欢迎您成为天天生鲜注册会员</h1>请点击下面链接激活您的邮箱<br/><a href='http://192.168.205.145:8080/user/active/%s'>http://192.168.205.145:8080/user/active/%s</a>" % (
        username, token, token)
        send_mail(subject, message, from_email, recevier, html_message=html_mesage)
        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):
        """进行用户激活"""
        # 获取要激活的用户信息
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取待激活用户的用户信息
            user_id = info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 返回应答：跳转到登录页面

        except SignatureExpired as e:
            # 激活链接已过期
            return HttpResponse("激活链接已过期")

        return redirect(reverse('user:login'))


# /user/login
class LoginView(View):
    """登录试图"""

    def get(self, request):
        """显示登录页面"""
        return render(request, 'login.html')
