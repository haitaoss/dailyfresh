from django.conf.urls import url
from cart.views import CartAddView, CartInfoView, CartUpdateView,CartDeleteOneView

urlpatterns = [
    url(r'^add$', CartAddView.as_view(), name='add'),  # 购物车记录添加
    url(r'^$', CartInfoView.as_view(), name='show'),  # 购物车页面显示
    url(r'^update$', CartUpdateView.as_view(), name='update'),  # 购物车页面数据更新
    url(r'^delete_one$', CartDeleteOneView.as_view(), name='delete_one'),  # 购物车页面数据删除

]
