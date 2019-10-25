from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.urlresolvers import reverse  # 反向解析
from django.core.mail import send_mail  # 发送邮件的函数
from django.views.generic import View  # 类试图
# from apps.user.models import User  # 导入模型类
from user.models import User, Address  # 导入模型类
from order.models import OrderInfo, OrderGoods
from django.core.paginator import Paginator
from goods.models import GoodsSKU
from django.conf import settings  # 导入settings
import re  # 正则匹配
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # 导入加密的类
from itsdangerous import SignatureExpired  # 加密插件抛出的异常
from celery_tasks.tasks import send_register_active
from django.contrib.auth import authenticate, login, logout
from utils.mixin import LoginRequireMixin
from django_redis import get_redis_connection



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

                # 获取登录后,所要跳转的地址（被拦截回来的时候会有这个next的值）
                # 默认跳转到首页
                next_url = request.GET.get('next', reverse('goods:index'))
                # next_url = request.GET.get('next')
                # if next_url:
                #     response = redirect(next_url)
                # else:
                #     response = redirect(reverse('goods:index'))
                response = redirect(next_url)

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


# /user/logout
class LogoutView(View):
    """退出登录"""

    def get(self, request):
        """退出登录"""
        # 清除用户的session信息
        logout(request)
        # 跳转到首页
        return redirect(reverse('goods:index'))


# /user
class UserInfoView(LoginRequireMixin, View):
    """用户中心-信息页"""

    def get(self, request):
        """显示"""
        # page ='user'
        # request.user
        # 如果用户未登录-》AnonymousUse类的实例
        # 如果用户登录-》User类的实例
        # .is_authenticated()
        # 如果是User类的实例该方法返回的True，另一个类的实例返回的值False

        # 获取用户的个人信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户的历史浏览记录
        # from redis import StrictRedis
        # sr = StrictRedis(host='127.0.0.1', port=6379, db=9)
        con = get_redis_connection('default')

        history_key = 'history_%d' % user.id

        # 获取用户最新浏览的5个商品id
        sku_id = con.lrange(history_key, 0, 4)  # [2,3,1]

        # 从数据库中,查询用户浏览的
        # goods_li = GoodsSKU.objects.filter(id__in=sku_id)
        #
        # # 排列顺序,因为从数据库查到的顺序不是我们想要的
        # goods_res = []
        # for a_id in sku_id:
        #     for goods in goods_li:
        #         if a_id == goods.id:
        #             goods_res.append(goods)

        goods_li = []
        for id in sku_id:
            goods_li.append(GoodsSKU.objects.get(id=id))

        # 组织上下文
        context = {'page': 'user',
                   'user': user,
                   'address': address,
                   'goods_li': goods_li
                   }
        # 除了你给模板文件传递的模板变量之外，django框架会把request.user也传递给模板文件
        return render(request, 'user_center_info.html', context)


# /user/order
class UserOrderView(LoginRequireMixin, View):
    """用户中心-订单页"""

    def get(self, request, page):
        """显示"""
        # page ='order'
        # 获取用户的订单信息
        user = request.user

        # 获取用户的所有订单
        orders = OrderInfo.objects.filter(user=user)

        # 遍历获取订单商品的信息
        for order in orders:
            # 根据order获取订单商品信息
            order_goods_s = OrderGoods.objects.filter(order=order).order_by('create_time')

            # 遍历order_goods计算小计
            for order_goods in order_goods_s:
                # 计算小计
                amount = order_goods.price * order_goods.count
                # 动态给order_goods增加属性，保存订单商品的小计
                order_goods.amount = amount
            # 动态给order增加属性，保存订单状态标题
            order.stauts_name = OrderInfo.ORDER_STATUS[order.order_status]
            # 动态给order增加属性，保存订单商品的信息
            order.order_goods_s = order_goods_s

        # 进行分页
        paginator = Paginator(orders, 2)
        # 处理页码
        try:
            page = int(page)
        except:
            page = 1
        if page > paginator.num_pages:
            page = 1

        # 获取page页的内容
        order_page = paginator.page(page)

        # todo 进行页码的控制,页面上最多显示5个页码
        # 1.总页数小于5,页面上显示所有的页码
        # 后面的情况都是总页数大于5
        # 2.如果当前页是前3页,显示1-5页
        # 3.如果当前页是后3页,显示后5页
        # 4.其他情况,显示当前页的前2页,当前页,当前页的后两页
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        # 组织上下文
        context = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order'

        }

        # 使用模板
        return render(request, 'user_center_order.html', context)


# /user/address
class UserSiteView(LoginRequireMixin, View):
    """用户中心-地址页"""

    def get(self, request):
        """显示"""
        # page ='address'

        # 获取登录用户对应的User对象
        user = request.user
        # try:
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None
        address = Address.objects.get_default_address(user)
        # 使用模板的时候,传递地址
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        """地址的添加"""
        # 接收数据
        receiver = request.POST.get("receiver")
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')  # 数据库定义了,可以为空.所以不需要校验
        phone = request.POST.get('phone')

        # 校验数据
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {"errmsg": '数据不完整'})
        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {"errmsg": '请输入正确的手机号'})
        # 业务处理:地址添加
        # 如果用户已存在默认收货地址,添加的地址不作为默认收货地址,否则作为默认收货地址
        # 获取登录用户对应的User对象
        user = request.user
        # try:改写了模型管理器
        #     address = Address.objects.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     address = None

        address = Address.objects.get_default_address(user)
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答,刷新地址页面
        return redirect(reverse('user:address'))  # 重定向就是get请求


