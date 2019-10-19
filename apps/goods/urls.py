from django.conf.urls import url
from goods.views import IndexView

# from goods import views

urlpatterns = [
    url(r'^index$', IndexView.as_view(), name='index'),  # 首页
]
