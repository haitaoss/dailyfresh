from django.contrib import admin
from goods.models import GoodsType, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
from django.core.cache import cache


# 不能放在这里，放在这里程序就不走了。为什么
# from celery_tasks.tasks import generate_static_index_html

class BaseModelAdmin(admin.ModelAdmin):
    #   通过django后台管理员修改模型的时候会出发这个方法，
    #   对这个方法重写实现我们，已修改首页信息就重新生成静态文件的需求
    def save_model(self, request, obj, form, change):
        """新增或者更新表中的数据是调用"""
        # super(IndexPromotionBannerAdmin).save_model(request, obj, form, change) 这是错误的
        super().save_model(request, obj, form, change)

        # 发出任务，让celery worker重新生成首页静态页
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
