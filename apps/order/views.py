from django.shortcuts import render, redirect
from django.views.generic import View
from django.core.urlresolvers import reverse
from goods.models import GoodsSKU
from user.models import Address
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from utils.mixin import LoginRequireMixin
from django.http import JsonResponse
from datetime import datetime
from django.db import transaction
from alipay import AliPay, ISVAliPay
from django.conf import settings
import os
from utils.mixin import LoginRequireMixin


# Create your views here.
# /order/place
class OrderPlaceView(LoginRequireMixin, View):
    """提交订单页面展示"""

    def get(self, request):

        # 购物车页面
        return redirect(reverse('cart:show'))

    def post(self, request):
        """提交订单页面展示"""
        # 获取用户信息
        user = request.user

        # 获取参数sku_id
        sku_ids = request.POST.getlist('sku_id')

        # 校验参数
        if not sku_ids:
            # 条件到购物车页面
            return redirect(reverse('cart:show'))
        # 遍历sku_ids获取用户要购买的商品的信息
        skus = []
        total_count = 0  # 总件数
        total_price = 0  # 总金额
        conn = get_redis_connection('default')
        for sku_id in sku_ids:
            # 根据商品的id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 根据商品的id购买了几件商品
            cart_key = 'cart_%d' % user.id
            count = int(conn.hget(cart_key, sku_id))  # 数量
            amount = count * sku.price  # 商品小计

            # 累加数量,和总金额
            total_count += count
            total_price += amount

            sku.count = count  # 动态添加属性
            sku.amount = amount  # 动态添加属性

            skus.append(sku)
        # 运费:实际开发过程的时候,属于一个子系统
        transit_price = 10  # 写死
        # 实付款
        total_pay = total_price + transit_price

        # 获取用户的收货地址
        addrs = Address.objects.filter(user=user)

        # 拼接成字符串,方便生成订单的时候使用
        sku_ids = ','.join(sku_ids)  # [1,2] ->1,2
        # 组织参数
        context = {
            'skus': skus,
            'total_count': total_count,
            'total_price': total_price,
            'total_pay': total_pay,
            'transit_price': transit_price,
            'addrs': addrs,
            'sku_ids': sku_ids
        }
        # 返回应答
        return render(request, 'place_order.html', context)


# /order/commit
# 前端传递的常数:地址id(addr_id) 支付方式(pay_method) 用户要购买的商品id(sku_ids)
# mysql事物:一组sql操作,要么都成功,要么都失败
# 高并发:秒杀
# 支付宝支付
class OrderCommitView(View):
    """订单创建"""

    @transaction.atomic  # 会对这个函数里面的sql语句开始其实,我估计就是一开始就开启事物
    def post(self, request):
        """订单创建"""
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # 接受参数
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')  # 1,2,3

        # 校验数据的完整性
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        # 校验支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '非法的支付方式'})
        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '地址非法'})

        # todo 创建订单核心业务

        # 组织常数
        # 订单id:201910241135+用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)
        # 运费
        transit_price = 10  # 写死
        # 总数目和总金额 先设置默认值,待会在重新设置
        total_count = 0
        total_price = 0

        # 设置事务保存点
        save_id = transaction.savepoint()
        # todo: 向df_order_info表中添加一条记录
        try:
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=addr,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             total_price=total_price,
                                             transit_price=transit_price
                                             )
            # todo: 用户的订单中有几个商品,就需要想df_order_goods中加入几条记录
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            for sku_id in sku_ids.split(","):
                for i in range(3):

                    # import time 模拟并发的时候网速没别人快.被别人先买了
                    # time.sleep(10)
                    # 获取商品的信息
                    try:

                        # todo 加锁,select * from df_goods_sku where id=sku_id for update
                        # sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                        sku = GoodsSKU.objects.get(id=sku_id)  # 在更新的时候在判断
                    except GoodsSKU.DoesNotExist:
                        # 回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 4, 'errmsg': '商品不存在'})

                    # 从redis中获取商品的数量
                    count = int(conn.hget(cart_key, sku_id))
                    # todo 判断商品的库存
                    if count > sku.stock:
                        # 回滚
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'res': 6, 'errmsg': '商品库存不足'})

                    # todo: 更新商品的库存和销量
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()
                    orgin_stock = sku.stock
                    new_stock = orgin_stock - count
                    new_sales = sku.sales + count

                    print('user:%d times:%d stock:%d' % (user.id, i, sku.stock))
                    # import time
                    # time.sleep(10)

                    # update df_goods_sku set stock=new_stock ,sales=new_sales where id=sku_id
                    # and stock = orgin_stock
                    # 返回受影响的行数
                    res = GoodsSKU.objects.filter(id=sku_id, stock=orgin_stock).update(stock=new_stock, sales=new_sales)
                    if res == 0:
                        # 尝试3次都下单失败，就认为失败（主要目的是，有3件商品，两个客户一人买一个的情况，可能出现下单失败）
                        if i == 2:
                            transaction.savepoint_rollback(save_id)
                            return JsonResponse({'res': 7, 'errmsg': '下单失败'})
                        continue

                    # todo: 向df_order_goods表中添加一条记录
                    amount = count * sku.price
                    #  累加总数目和总价格
                    total_count += count
                    total_price += amount
                    OrderGoods.objects.create(order=order, sku=sku, count=count, price=sku.price)

                    # 如果到了这里，且i不为2我们需要手动跳出循环
                    break

            # todo: 更新订单信息表中的商品的中数量和总价格
            order.total_price = total_price
            order.total_count = total_count
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 7, 'errmsg': '下单失败'})

        # 提交事物
        transaction.savepoint_commit(save_id)  # 将保存到点包含的sql语句提交

        # todo:清除用户购物车中对应的记录[1,2,3] -> 1,2,3
        conn.hdel(cart_key, *sku_ids)  # 这里是位置参数,所以把列表拆包处理
        # 返回应答
        return JsonResponse({'res': 5, 'message': '创建成功'})


# ajax post
# 前端传递的参数，订单id(order_id)
# /order/pay
class OrderPayView(View):
    """订单支付"""

    def post(self, request):
        """订单支付"""
        # 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, "errmsg": "用户未登陆"})
        # 接受参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, "errmsg": '参数不合法'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, "errmsg": '订单不存在'})

        # 业务处理：使用python sdk调用支付宝的支付接口
        # # 初始化
        alipay = AliPay(
            appid="2016101300673201",  # 应用id
            app_notify_url=None,  # 默认回调url
            # 这里使用path方式打开，使用string还得自己打开文件open
            app_private_key_string=open(settings.BASE_DIR + "/apps/order/app_private_key.pem").read(),
            # app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            # alipay_public_key_string=open(settings.BASE_DIR + "/apps/order/alipay_public_key.pem").read(),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, "apps/order/alipay_public_key.pem"),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False是访问真实的地址。True就是访问沙箱的地址
        )

        total_pay = order.total_price + order.transit_price  # Decimal
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 订单id
            total_amount=str(total_pay),  # 支付总金额,因为我们的是Decimal类型无法被json序列化，所以变成字符串
            subject='天天生鲜%s' % order_id,
            return_url=None,
            notify_url=None  # 可选, 不填则使用默认notify url
        )
        # 返回应答
        pay_url = 'https://openapi.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, "pay_url": pay_url})


# ajax post
# 前端传递的参数，订单id(order_id)
# /order/check
class CheckPayView(View):
    """查看订单支付结果"""

    def post(self, request):
        # 用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, "errmsg": "用户未登陆"})
        # 接受参数
        order_id = request.POST.get('order_id')
        # 校验参数
        if not order_id:
            return JsonResponse({'res': 1, "errmsg": '参数不合法'})
        try:
            order = OrderInfo.objects.get(order_id=order_id,
                                          user=user,
                                          pay_method=3,
                                          order_status=1
                                          )
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, "errmsg": '订单不存在'})

        # 调用支付宝的交易查询借口
        # # 初始化
        alipay = AliPay(
            appid="2016101300673201",  # 应用id
            app_notify_url=None,  # 默认回调url
            # 这里使用path方式打开，使用string还得自己打开文件open
            app_private_key_string=open(settings.BASE_DIR + "/apps/order/app_private_key.pem").read(),
            # app_private_key_path=os.path.join(settings.BASE_DIR, 'apps/order/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            # alipay_public_key_string=open(settings.BASE_DIR + "/apps/order/alipay_public_key.pem").read(),
            alipay_public_key_path=os.path.join(settings.BASE_DIR, "apps/order/alipay_public_key.pem"),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=True,  # 默认False是访问真实的地址。True就是访问沙箱的地址
        )
        while True:
            response = alipay.api_alipay_trade_query(order_id)
            # response = {
            #
            #     "trade_no": "2017032121001004070200176844", # 支付宝交易号
            #     "code": "10000", # 接口调用是否成功
            #     "invoice_amount": "20.00",
            #     "open_id": "20880072506750308812798160715407",
            #     "fund_bill_list": [
            #         {
            #             "amount": "20.00",
            #             "fund_channel": "ALIPAYACCOUNT"
            #         }
            #     ],
            #     "buyer_logon_id": "csq***@sandbox.com",
            #     "send_pay_date": "2017-03-21 13:29:17",
            #     "receipt_amount": "20.00",
            #     "out_trade_no": "out_trade_no15",
            #     "buyer_pay_amount": "20.00",
            #     "buyer_user_id": "2088102169481075",
            #     "msg": "Success",
            #     "point_amount": "0.00",
            #     "trade_status": "TRADE_SUCCESS", # 支付结果
            #     "total_amount": "20.00"
            # }
            # 查看网址https://docs.open.alipay.com/api_1/alipay.trade.query/
            code = response.get('code')
            if code == '10000' and response.get('trade_status') == 'TRADE_SUCCESS':
                # 支付成功
                # 获取支付宝交易号
                order.trade_no = response.get('trade_no')
                # 更新订单状态
                order.order_status = 4  # 待评价
                order.save()
                return JsonResponse({'res': '3', 'message': '支付成功'})
                # 返回应答
            elif code == '40004' or code == '10000' and response.get('trade_status') == 'WAIT_BUYER_PAY':
                # 等待卖家付款
                # 业务处理失败，可能一会就会成功，40004就是用户正在执行交易的步骤，输入密码之类的
                import time
                time.sleep(5)
                continue
            else:
                print(code)
                # 支付出错
                return JsonResponse({'res': '4', 'errmsg': '支付失败'})


class CommentView(LoginRequireMixin, View):
    """订单评论"""

    def get(self, request, order_id):
        """提供评论页面"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 根据订单的状态获取订单的状态标题
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 获取订单商品信息
        order_skus = OrderGoods.objects.filter(order_id=order_id)

        for order_sku in order_skus:
            # 计算商品的小计
            amount = order_sku.count * order_sku.price
            # 动态给order_sku增加属性amount,保存商品小计
            order_sku.amount = amount
        # 动态给order增加属性order_skus, 保存订单商品信息
        order.order_skus=order_skus
        # 使用模板
        return render(request, "order_comment.html", {"order": order})

    def post(self, request, order_id):
        """处理评论内容"""
        user = request.user
        # 校验数据
        if not order_id:
            return redirect(reverse('user:order'))

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect(reverse("user:order"))

        # 获取评论条数
        total_count = request.POST.get("total_count")
        total_count = int(total_count)

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # cotent_1 content_2 content_3
            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            order_goods.comment = content
            order_goods.save()

        order.order_status = 5  # 已完成
        order.save()

        return redirect(reverse("user:order", kwargs={"page": 1}))
