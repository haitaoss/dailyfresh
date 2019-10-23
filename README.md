# dailyfresh
天天生鲜


访问项目首先启动,在settings里面配置的redis服务器,再启动fdfs tracker和storage,再启动访问fdfs的nginx服务
sudo redis-server /etc/redis/redis.conf 首页需要查询redis缓存有没有
sudo service fdfs_trackerd start 上传文件才需要[可以先不启动]
sudo service fdfs_storaged start 上传文件才需要[可以先不启动]
sudo /usr/local/nginx/sbin/nginx  访问存在fdfs文件存储系统里面的图片文件需要

第一天：实现注册功能
首先显示注册页面，在写出注册提交的试图函数 。然后实现发邮件的功能

第二天:

历史浏览记录的分析:
1.什么时候需要添加历史浏览记录?
    访问商品的详情页面的时候(在商品详情对应的试图中),需要添加历史浏览记录.
2. 什么时候需要获取历史浏览记录?
    访问用户个人中心信息页的时候,获取历史浏览记录.
    
3.历史浏览记录需要存储在哪里?
    redis数据库>内存型的数据库********
    使用redis数据库存储历史浏览记录.
 
4. redis中存储历史浏览记录个格式?
    string,hash,list,set,sortset
  
5.存储用户的历史浏览记录时,所有用户的历史浏览记录用一条数据保存,还是每个用户的历史浏览记录用一条数据保存.
    hash:
        history user_用户Id:'1,2,3'
    每个用户的历史浏览记录用一条数据保存:
    list:
        history_用户id:[1,2,3,4]
    添加历史浏览记录时,用户最新浏览的商品的id从列表左侧插入
    
    结论使用list
    
第三天 FastDFS
不使用django默认的文件管理系统保存图片？那是因为django文件管理系统，保存的位置是服务器上。不能解决海量存储的问题。
特点：
1.解决海量存储的问题
2.存储容量扩展很方便
3.解决文件内容重复的问题。
流程,客户端首先会请求tracker server(跟踪服务器)这里可以是一个集群。tracker server又回去请求storage server(存储服务器)这里也是一个集群，
会返回存储服务器的id给跟踪服务器。跟踪服务器又会把这个信息给到客户端。这个时候客户端，就知道要把图片存储到那个地方。这个时候客户端就会给存储服务器上传
文件。让存储服务器保存文件。

第四天 首页动态显示，购物车记录的添加，页面静态化
一、首页动态显示
    1.分析goods里面的模型类
    GoodsType是商品分类表。就是首页的左边的全部商品分类那一块
    GoodsSKU是商品库存量单位，商品详情页面需要这个
    Goods就是SPU标准产品单位，比如颜色这些属性属于这个分类。
    GoodsImage，一个商品有多个详细的照片，所以用这个存放多个照片
    IndexGoodsBanner，首页商品轮播图。
    IndexTypeGoodsBanner,分类商品展示信息，根据字段type决定展示的是文字还是图片
    IndexPromotionBanner，就是轮播图右边的活动轮播图
    
    2，首页需要什么信息
    # 获取商品的种类信息
    # 获取首页轮播商品信息
    # 获取首页促销活动信息
    # 获取首页分类商品展示信息
        这里很关键，利用python是弱类型语言简化我们的代码
    # 获取用户购物车中商品的数目

    向数据库插入数据之后，还不能正常显示图片。因为图片是从fdfs服务器获取的，所以需要将图片上传到fdfs文件存储系统
    我在utils包下面有一个upload_image_fdfs.py的文件能够扫描指定文件目录下的图片并将文件上传到服务器上。
    
    然后就苦逼着修改，数据库里面的图片的url。否则还是找不到图片

二、购物车记录
    1. 什么时候添加购物车记录？
        当用户点击加入购物车时需要添加购物车记录
    2. 什么时候需要获取购物车记录？
        使用购物车中的数据和访问购物车页面的时候需要获取购物车记录。
    3.使用什么存储购物车记录？
        redis存储购物车记录。
    4.分析存储购物车记录的格式？
        一个用户的购物车记录用一条数据保存（保存的信息有商品SKU_id，购买商品数量）
        使用什么类型来存储？
        string,list,hash,set,zset。
        假如使用list：
            'cart_用户id':['1,2','2,4'] #SKU_id唯一数量为2
             很明显这么设计不好（如果用户修改商品数量，涉及到字符串处理，不好整）
        最好是使用hash：
            'cart_用户id'：{'1':'2','2':'4'}
        例子：
        'cart_1': {'1':'3','2':'5'}
        获取用户购物车中商品的条目数：使用hlen。
        （redis命令常考http://doc.redisfans.com/
           python里面的命令https://redis-py.readthedocs.io/en/stable/
        ）
        
三、首页静态化,页面数据的缓存
    页面静态化.
        什么时候首页的静态静态页面需要重新生成?
            当管理员后台修改首页信息对应的表格中的数据的时候,需要重新生成首页静态页
         需要掌握
            使用celery生成静态页面.
            配置nginx提供静态页面.
            管理员修改首页表中的数据时,重新生成静态页面.

            流程，1.使用celery生成静态页面.2.使用nginx访问静态资源（需要配置nginx来实现访问）
            
            重写admin.Manager里面的save_model()和delete_model()方法实现,修改数据就重新生成静态文件
            https://yiyibooks.cn/xx/django_182/ref/contrib/admin/index.html
            
    页面数据的缓存
        目的:把页面使用到的数据存放在缓存中,当再次使用这些数据时,现从缓存中获取,如果获取不到,再去查询数据库.减少数据库查询的次数
    什么时候需要更新首页的缓存数据?
        当管理员后台修改首页信息对应的表格中的数据的时候,需要重新更新首页的缓存数据
        
    用到的方法from django.core.cache import cache (根据在setting里面的配置,决定缓存到那个数据库,这里配置的是redis)
         cache.set('键','数据','缓存过期时间,秒,不设置就是永久') # 过期时间最好设置,防止管理员忘记删除缓存
         cache.get('键')
         cache.delete('键')
     
     页面静态化和页面数据的缓存好处
        网站本身性能的优化,减少数据库的查询次数
        防止恶意的攻击,DDOS攻击(就是多台电脑同时访问你的网站)
        
       
第五天:商品详情页面
一,商品详情页面
    需要分类信息,商品sku信息,商品评论信息,新品推荐信息,购物车信息.
    GoodsType.object.all(),GoodsSKU.object.get(id=sku_id),OrderGoods(sku=GoodsSKU),
    GoodsSKU.objects.filter(type=sku.type).exclude(id=sku_id).order_by('-create_time'),购物车信息从redis中获取
    
二,列表页,使用分页模型,学会自定义要显示的页码


第六天:全文搜索,购物车页面的加减js的书写,js的操作
    一,全文检索框架
        例子 :草莓
        
        select * from df_goods_sku where like name '%草莓%' or desc like '%草莓%';
        这种效率很低,百度的搜索利用的是搜索引擎,我们这里也能使用.
        
        我们采用的是调用全文检索框架,由框架去调用搜索引擎搜索数据
        全文检索框架:
            可以帮助用户使用搜索引擎.
        搜索引擎:
            可以对表中的某些字段进行关键词分析,建立关键词对应的索引数据.
        
        在django里面使用全文检索引擎的步骤.
        安装全文检索框架pip install haystack
        安装搜索引擎 pip install whoose
        
        然后在配置haystack和url配置项即可
        
        去看看detail.html下方的js函数(商品的加减)
    二,购物车
        添加商品到购物车
        1,请求方式,采用ajax
            如果涉及到数据的修改(新增,更新,删除),采用post
            如果只涉及到数据的获取,采用get
        2,传递参数:商品id,商品数量
        
        get传参数/cart/add?sku_id=1&count=3
        post传参数:{sku_id:1,count:3}
        url传参数:url配置是捕获参数
        
    三,详情页面加入购物车,已经购物车页面修改数据的js可以好好看一看,加深对jquery的学习,还有就是
    python_redis里面hash的操作
        conn.hvals(cart_ket)获取hash里面的所有值
        conn.hgetall(cart_key)获取hash里面的所有键值对返回值是字典
        conn.hlen(cart_key)获取hash里面键的个数

