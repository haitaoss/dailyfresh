from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, CommentView

urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'),  # 订单页面
    url(r'^commit$', OrderCommitView.as_view(), name='commit'),  # 创建订单
    url(r'^pay$', OrderPayView.as_view(), name='pay'),  # 用户支付
    url(r'^check$', CheckPayView.as_view(), name='check'),  # 检测支付
    url(r'^comment/(?P<order_id>\d+)$', CommentView.as_view(), name='comment'),  # 订单评论
]
