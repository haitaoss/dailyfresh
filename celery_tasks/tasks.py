# 使用celery
from django.template import loader, RequestContext
from django_redis import get_redis_connection
from celery import Celery
from django.conf import settings
from django.core.mail import send_mail
import time
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dailyfresh.settings")

django.setup()

from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner

# celery -A celery_tasks.tasks worker -l info

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


@app.task
def generate_static_index_html():
    # 获取商品的种类信息
    types = GoodsType.objects.all()

    # 获取首页轮播商品信息
    goods_banners = IndexGoodsBanner.objects.all().order_by('index')  # 0 1 2

    # 获取首页促销活动信息
    promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

    # 获取首页分类商品展示信息
    # type_goods_banners = IndexTypeGoodsBanner.objects.all() 这样子是不行的
    for type in types:  # GoodsType
        # 获取type种类首页分类商品的展示信息
        image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')  # 图片的展示信息
        # 获取type种类首页分类商品的文字展示信息
        title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

        # python 弱类型语言,动态给type增加属性，分别保存首页分类商品的图片展示信息和文字信息
        # 添加这连个属性的目的是根据页面的需求决定的
        # 这就体现了弱类型语言的好处了
        type.image_banners = image_banners
        type.title_banners = title_banners

    # # 获取用户购物车中商品的数目,这里不需要，因为这是静态页面，就是不登录的用户想看看网站
    #
    # cart_count = 0
    # user = request.user
    # # 登录了才会显示
    # if user.is_authenticated():
    #     # 链接到redis数据库
    #     conn = get_redis_connection('default')
    #     cart_key = 'cart_%s' % user.id
    #     # 获取用户的购物车条目数
    #     cart_count = conn.hlen(cart_key)

    # 组织模板上下文
    context = {'types': types,
               'goods_banners': goods_banners,
               'promotion_banners': promotion_banners,
               # 'type_goods_banners': type_goods_banners,
               # 'cart_count': cart_count
               }
    # 使用模板
    # 加载模板文件
    temp = loader.get_template('static_index.html')
    # # 定义模本上下文对象
    # context = RequestContext(request, dict=context)
    # 渲染模板文件,不传递RequestContext对象也是可以的，直接传递字典也能实现数据的替换
    static_index_html = temp.render(context)

    # 生成首页对应的静态文件
    save_path = os.path.join(settings.BASE_DIR, 'static/index.html')
    with open(save_path, 'w') as f:
        f.write(static_index_html)
