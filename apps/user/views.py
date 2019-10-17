from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse  # 反向解析
from django.core.mail import send_mail  # 发送邮件的函数
from django.views.generic import View  # 类试图
# from apps.user.models import User  # 导入模型类
from user.models import User  # 导入模型类
from django.conf import settings  # 导入settings
import re  # 正则匹配
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 导入加密的类
from itsdangerous import SignatureExpired  # 加密插件抛出的异常
from celery_tasks.tasks import send_register_active
from django.contrib.auth import authenticate, login


# Create your views here.


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
        # 导入我们写好的函数，调用的时候使用delay即可实现。把任务交给中间人处理
        from celery_tasks.tasks import send_register_active

        # 发邮件 todo 使用celery帮我们发邮件,delay是因为我们用了装饰器装饰了函数,所以有这个函数
        send_register_active.delay(email, username, token)

        # 返回应答
        return redirect(reverse('goods:index'))


class ActiveView(View):
    def get(self, request, token):

        print("我收到请求了")
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
        # 判断用户是否记住用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get("username")
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username': username, 'checked': checked})

    def post(self, request):
        """登录的校验"""
        # 接受请求常数
        username = request.POST.get("username")
        password = request.POST.get("pwd")

        # 校验数据
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})
        # 业务处理：登录校验
        # from django.contrib.auth import authenticate导入认证函数（我们使用的django的认证系统）
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                # 用户已经激活
                # 记录用户的登录状态,这个是django认证系统提供的
                login(request, user)

                response = redirect(reverse('goods:index'))

                # 判断用户是否需要记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')

                # 跳转到首页
                return response
            else:
                return render(request, 'login.html', {'errmsg': '请去邮箱激活你的账户'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
        # 返回应答
