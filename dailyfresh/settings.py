"""
Django settings for dailyfresh project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1-817^-n#djs@b6#v7zh8m9(u^su@7tm7$c5-fd+thucx5%6!j'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

# 在资源的搜索路径里面添加上apps。
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tinymce',  # 富文本编辑器
    'user',  # 用户模块
    'cart',  # 购物车模块
    'goods',  # 商品模块
    'order',  # 订单模块
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'dailyfresh.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dailyfresh.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        # connect(host='192.168.205.141',port=3306,database='jing_dong',user='root',password='root',charset='utf8')

        'ENGINE': 'django.db.backends.mysql',  # 数据库类型
        'NAME': 'dailyfresh',  # 数据库名称，数据库必须先手动创建
        'USER': 'root',  # 链接MySQL的用户名
        'PASSWORD': 'root',  # 用户名对应的密码
        'HOST': 'localhost',  # 指定mysql数据库所在的电脑ip
        'PORT': 3306,  # mysql服务器的电脑
    }
}
# django认证系统使用的模型类(设置这个的目的是，不在使用django给我们的auth_user表存储
# 用户的信息。使用我们指定的模型类对应的表来存储。当然你的模型类必须继承django.AbstractUser)
# AUTH_USER_MODEL配置参数要在第一次迁移数据库之前配置，否则可能django的认证系统工作不正
# 如果执行python manage.py makemigrations出错，就按照提示先生成。依赖的app的迁移文件
# 在执行生成迁移文件的步骤即可
AUTH_USER_MODEL = 'user.User'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-hans'  # 使用中文

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Shanghai'  # 中国的时间

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# 富文本编辑器的配置
TINYMCE_DEFAULT_CONFIG = {
    'theme': 'advanced',
    'width': 600,
    'height': 400,
}

# 发送邮件配置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# smtp服务器的地址
EMAIL_HOST = 'smtp.qq.com'
# 服务器的端口
EMAIL_PORT = 25
# 发送邮件的邮箱
EMAIL_HOST_USER = '1486504210@qq.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'xqdukjqvgppljdje'
# 收件人看到的发件人，<>里面必须是发送人的邮箱
EMAIL_FROM = '天天生鲜<1486504210@qq.com>'

# Django的缓存的配置
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/9",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# 配置session存储
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# 配置登录url地址
LOGIN_URL = '/user/login'

# 设置django的文件存储类（这么设计之后，django就会调用这个类来处理存储文件）
DEFAULT_FILE_STORAGE = 'utils.fdfs.storage.FDFSStorage'

# 　设置fdfs使用的client.conf文件路径
FDFS_CLIENT_CONF = BASE_DIR + '/utils/fdfs/client.conf'
# 设置fdfs存储服务器的nginx的IP和端口
FDFS_URL = 'http://192.168.205.148:8888'
