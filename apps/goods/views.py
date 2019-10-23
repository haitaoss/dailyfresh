from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.cache import cache
from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner, GoodsSKU, Goods
from order.models import OrderGoods
from django_redis import get_redis_connection
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator


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

        # 尝试从缓存的获取数据
        context = cache.get('index_page_data')
        if context is None:
            print("设置缓存")

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
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by(
                    'index')  # 图片的展示信息
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # python 弱类型语言,动态给type增加属性，分别保存首页分类商品的图片展示信息和文字信息
                # 添加这连个属性的目的是根据页面的需求决定的
                # 这就体现了弱类型语言的好处了
                type.image_banners = image_banners
                type.title_banners = title_banners
            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners,
                       }

        # 设置缓存 https://yiyibooks.cn/xx/django_182/topics/cache.html 搜索django.core.cache.cache

        # 设置缓存, key value timout
        cache.set('index_page_data', context, 3600)

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

        # 组织模板上下文,这个是如果键存在就是更新不存在就是添加
        context.update(cart_count=cart_count)
        # context['cart_count'] = cart_count

        return render(request, 'index.html', context)


# /goods/商品id
class DetailView(View):
    """详情页"""

    def get(self, request, goods_id):
        """显示详情页"""
        # 商品sku信息
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
        except:
            sku = None
        if sku is None:
            # 直接去首页
            return redirect(reverse('goods:index'))

        # 获取商品的种类信息
        types = GoodsType.objects.all()

        # 获取商品的评论信息
        sku_ordres = OrderGoods.objects.filter(sku=sku).exclude(comment='')

        # 获取新品信息
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取同一个spu的其他规格的商品
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=goods_id)
        # 获取用户的购物车中商品的数目
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

            # 添加用户的历史浏览记录
            conn = get_redis_connection('default')
            # 移除
            history_key = 'history_%d' % user.id
            conn.lrem(history_key, 0, goods_id)  # 0是移除所有,如果没有这个value就什么都不干
            # 添加,把goods_id从左侧插入
            conn.lpush(history_key, sku.goods_id)
            # 只保存用户最新浏览的5条信息
            conn.ltrim(history_key, 0, 4)  # 队列表裁剪,剩下[0,4]
        # 组织模板上下文
        context = {
            'sku': sku,
            'types': types,
            'sku_ordres': sku_ordres,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'same_spu_skus': same_spu_skus
        }
        return render(request, 'detail.html', context)


# 种类id 页码 排序方式
# restful api -> 请求一种资源
# /list?type_id=种类id&page=页码&sort=排序方式
# /list/种类id/页码/排序方式
# /list/种类id/页码?sort=排序方式  使用这种
class ListView(View):
    """列表页"""

    def get(self, request, type_id, page):
        """显示列表页面"""
        # 获取该分类的信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except:
            # 种类不存在,直接去首页
            return redirect(reverse('goods:index'))

        # 所有分类
        types = GoodsType.objects.all()

        # 获取排序的方式
        # sort=default 按照默认id排序
        # sort=price 按照商品的价格排序
        # sort = hot 按照商品的销量排序
        sort = request.GET.get('sort')
        if sort == 'hot':
            # 种类的所有商品
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        elif sort == 'price':
            # 种类的所有商品
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        else:
            sort = 'default'
            # 种类的所有商品
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据分页
        paginator = Paginator(skus, 1)

        try:
            page = int(page)
        except:
            page = 1
        if page > paginator.num_pages:
            page = 1

        # 获取page页的内容
        skus_page = paginator.page(page)

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

        # 新品信息
        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_time')[0:2]
        # 购物车
        user = request.user
        cart_count = 0
        if user.is_authenticated():
            # 用户已登录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织模板上下文
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus': new_skus,
            'cart_count': cart_count,
            'sort': sort,
            'pages': pages
        }
        # 使用模板
        return render(request, 'search.html/../../templates/search/search.html', context)
