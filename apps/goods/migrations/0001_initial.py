# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Goods',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('name', models.CharField(verbose_name='商品SPU名称', max_length=20)),
                ('detail', tinymce.models.HTMLField(verbose_name='商品详情', blank=True)),
            ],
            options={
                'verbose_name': '商品SPU',
                'verbose_name_plural': '商品SPU',
                'db_table': 'df_goods',
            },
        ),
        migrations.CreateModel(
            name='GoodsImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('image', models.ImageField(upload_to='goods', verbose_name='图片路径')),
            ],
            options={
                'verbose_name': '商品图片',
                'verbose_name_plural': '商品图片',
                'db_table': 'df_goods_image',
            },
        ),
        migrations.CreateModel(
            name='GoodsSKU',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('name', models.CharField(verbose_name='商品名称', max_length=20)),
                ('desc', models.CharField(verbose_name='商品简介', max_length=256)),
                ('price', models.DecimalField(max_digits=10, verbose_name='商品价格', decimal_places=2)),
                ('unite', models.CharField(verbose_name='商品单位', max_length=20)),
                ('image', models.ImageField(upload_to='goods', verbose_name='商品图片')),
                ('stock', models.IntegerField(verbose_name='商品库存', default=1)),
                ('sales', models.IntegerField(verbose_name='商品销量', default=0)),
                ('status', models.SmallIntegerField(verbose_name='商品状态', choices=[(0, '下线'), (1, '上线')], default=1)),
                ('goods', models.ForeignKey(to='goods.Goods', verbose_name='商品SPU')),
            ],
            options={
                'verbose_name': '商品',
                'verbose_name_plural': '商品',
                'db_table': 'df_goods_sku',
            },
        ),
        migrations.CreateModel(
            name='GoodsType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('name', models.CharField(verbose_name='种类名称', max_length=20)),
                ('logo', models.CharField(verbose_name='标识', max_length=20)),
                ('image', models.ImageField(upload_to='type', verbose_name='商品类型图片')),
            ],
            options={
                'verbose_name': '商品种类',
                'verbose_name_plural': '商品种类',
                'db_table': 'df_goods_type',
            },
        ),
        migrations.CreateModel(
            name='IndexGoodsBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('image', models.ImageField(upload_to='banner', verbose_name='图片')),
                ('index', models.SmallIntegerField(verbose_name='展示顺序', default=0)),
                ('sku', models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品')),
            ],
            options={
                'verbose_name': '首页轮播商品',
                'verbose_name_plural': '首页轮播商品',
                'db_table': 'df_index_banner',
            },
        ),
        migrations.CreateModel(
            name='IndexPromotionBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('name', models.CharField(verbose_name='活动名称', max_length=20)),
                ('url', models.URLField(verbose_name='活动链接')),
                ('image', models.ImageField(upload_to='banner', verbose_name='活动图片')),
                ('index', models.SmallIntegerField(verbose_name='展示顺序', default=0)),
            ],
            options={
                'verbose_name': '主页促销活动',
                'verbose_name_plural': '主页促销活动',
                'db_table': 'df_index_promotion',
            },
        ),
        migrations.CreateModel(
            name='IndexTypeGoodsBanner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(verbose_name='更新时间', auto_now=True)),
                ('id_delete', models.BooleanField(verbose_name='删除标记', default=False)),
                ('display_type', models.SmallIntegerField(verbose_name='展示类型', choices=[(0, '标题'), (1, '图片')], default=1)),
                ('index', models.SmallIntegerField(verbose_name='展示顺序', default=0)),
                ('sku', models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品SKU')),
                ('type', models.ForeignKey(to='goods.GoodsType', verbose_name='商品类型')),
            ],
            options={
                'verbose_name': '主页分类展示商品',
                'verbose_name_plural': '主页分类展示商品',
                'db_table': 'df_index_type_goods',
            },
        ),
        migrations.AddField(
            model_name='goodssku',
            name='type',
            field=models.ForeignKey(to='goods.GoodsType', verbose_name='商品种类'),
        ),
        migrations.AddField(
            model_name='goodsimage',
            name='sku',
            field=models.ForeignKey(to='goods.GoodsSKU', verbose_name='商品'),
        ),
    ]
