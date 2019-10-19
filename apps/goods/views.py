from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django_redis import get_redis_connection


# class Test(object):
#     def __init__(self):
#         self.name = 'abc'
#
#
# t = Test()
# t.age = 18
# print(t.age)

# Create your views here.
# http:127.0.0.1:8080
class IndexView(View):
    """首页"""

    def get(self, request):
        """显示首页"""
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

        # 获取用户购物车中商品的数目

        cart_count = 0
        user = request.user
        # 登录了才会显示
        if user.is_authenticated():
            # 链接到redis数据库
            conn = get_redis_connection('default')
            cart_key = 'cart_%s' % user.id
            # 获取用户的购物车条目数
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {'types': types,
                   'goods_banners': goods_banners,
                   'promotion_banners': promotion_banners,
                   # 'type_goods_banners': type_goods_banners,
                   'cart_count': cart_count
                   }
        return render(request, 'index.html', context)
