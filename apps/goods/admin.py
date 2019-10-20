from django.contrib import admin
from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django.core.cache import cache

# 不能放在这里，放在这里程序就不走了。
# 因为使用 celery -A celery_tasks.tasks worker -l info 启动.执行的时候
# sys.path这个资源搜索列表里面并没有当前项目的目录.所以导入不进来
# 可以手动添加资源路径
# import sys
# sys.path.append('/home/haitao/Desktop/dailyfresh')


# from celery_tasks.tasks import generate_static_index_html

class BaseModelAdmin(admin.ModelAdmin):
    #   通过django后台管理员修改模型的时候会出发这个方法，
    #   对这个方法重写实现我们，已修改首页信息就重新生成静态文件的需求
    def save_model(self, request, obj, form, change):
        """新增或者更新表中的数据是调用"""
        # super(IndexPromotionBannerAdmin).save_model(request, obj, form, change) 这是错误的
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker重新生成首页静态页
        # 最好的方式还是在这里导入.程序进入这个类,解析器就会把dailyfresh这个目录添加到
        # 资源搜索路径,这个时候就能找到我们想导入的py文件了
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存数据
        cache.delete('index_page_data')

    def delete_model(self, request, obj):
        """删除表中的数据是被调用"""
        super().delete_model(request, obj)

        # 发出任务，让celery worker重新生成首页静态页
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        # 清除首页的缓存数据
        cache.delete('index_page_data')


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


# Register your models here.
class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
