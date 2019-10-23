from django.shortcuts import render
from django.views.generic import View
from django_redis import get_redis_connection
from django.http import JsonResponse
from goods.models import GoodsSKU
from utils.mixin import LoginRequireMixin


# Create your views here.
# ajax发起的请求都在后台,在浏览器中看不到效果
# cart/add
class CartAddView(View):
    """购物车添加记录"""

    def post(self, request):
        """购物车记录的添加"""
        # 登录才能执行下面的操作
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 获取表单数据
        sku_id = request.POST.get("sku_id")
        count = request.POST.get("count")

        # 校验数据的完整
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数据出错
            JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理:添加购物车记录
        # 创建redis连接
        conn = get_redis_connection('default')
        # 创建键
        cart_key = 'cart_%d' % int(user.id)
        # 先获取这个键对应的值,做加法 -> hget cart_key 属性
        cart_count = conn.hget(cart_key, sku_id)  # 获取不到返回的是None
        if cart_count:
            # 累加
            count += int(cart_count)

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        # 设置hash中sku_id对应的值
        conn.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的条目数
        total_count = conn.hlen(cart_key)
        # 返回应答
        return JsonResponse({'res': 5, 'message': '添加成功', 'total_count': total_count})


# cart
class CartInfoView(LoginRequireMixin, View):
    """购物车页面显示"""

    def get(self, request):
        # 获取用户
        user = request.user

        # 获取用户购物车的所有商品
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # sku_ids = conn.hkeys(cart_key)  # 一个包含哈希表中所有域的表。当key不存在时，返回一个空表。
        # if not sku_ids:
        #     # 没有购物商品
        #     return render(request, 'cart.html')
        # 通过sku_id获取sku
        # skus = []
        # for id in sku_ids:
        #     sku = GoodsSKU.objects.get(id=id)
        #     # 弱类型.临时的变量
        #     sku.count = conn.hget(cart_key, id)
        #     skus.append(sku)
        cart_dict = conn.hgetall(cart_key)
        skus = []
        # 计算总价
        total_price = 0
        # 计算总件数
        total_count = 0
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            # 动态添加属性,保存购物车中商品的数量
            sku.count = int(count)
            # 计算商品小计
            sku.amount = sku.price * sku.count
            skus.append(sku)
            # 累加总价格
            total_price += sku.amount
            # 累加总数目
            total_count += sku.count
        # 返回应答
        return render(request, 'cart.html', {'skus': skus, 'total_price': total_price, 'total_count': total_count})


# 更新购物车记录
# 采用ajax post请求
# 前段需要传递的参数,:商品id(sku_id),更新的商品的数量(count)
class CartUpdateView(View):
    """购物车记录更新"""

    def post(self, request):

        # 登录才能执行下面的操作
        user = request.user
        if not user.is_authenticated():
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 获取表单数据
        sku_id = request.POST.get("sku_id")
        count = request.POST.get("count")

        # 校验数据的完整
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数据出错
            JsonResponse({'res': 2, 'errmsg': '商品数目出错'})
        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理:更新redis里面的数据
        conn = get_redis_connection('default')
        cart_ket = 'cart_%d' % user.id

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        # 更新
        conn.hset(cart_ket, sku_id, count)

        # 计算用户购物车中商品的总件数
        total_count = 0
        for num in conn.hvals(cart_ket):  # 获取hash里面的所有值,返回值是列表
            total_count += int(num)
        # 返回应答
        return JsonResponse({'res': 5, 'message': '更新成功', 'total_count': total_count})
