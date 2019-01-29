from django.shortcuts import render,HttpResponseRedirect
from Buy.models import *
from Seller.views import myencode
from Seller.models import Goods,Image
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
import random,datetime,time,os
from ShopProject.settings import MEDIA_ROOT
def cookieValid(fun):
    def inner(request,*args,**kwargs):
        cookie = request.COOKIES
        username = cookie.get("name")
        session = request.session.get("user") #获取session
        user = Buy.objects.filter(username = username).first()
        if user and session == user.username: #校验session
            return fun(request,*args,**kwargs)
        else:
            return HttpResponseRedirect("/buy/login/")
    return inner

@cookieValid
def index(request):
    data=[]
    goods=Goods.objects.all()
    for i in goods:
        image=i.image_set.first()
        img=image.img_adress.url
        data.append({'img':img,'name':i.goods_name,'price':i.goods_price,"id":i.id})
    return render(request,'buy/index.html',{'data':data})


def register(request):
    data=''
    if request.method=='POST' and request.POST:
        username=request.POST.get("username")
        password=request.POST.get("userpass")
        userpassword=request.POST.get("password")
        if userpassword==password:
            b=Buy()
            b.username=username
            b.password=myencode(password)
            b.save()
            return HttpResponseRedirect('/buy/login/')
        else:
            data="密码不一致！"
    return render(request, 'buy/register.html',{'data':data})

def registerPhone(request):
    data=''
    if request.method=='POST' and request.POST:
        username=request.POST.get("phone")
        password=request.POST.get("userpassword")
        userpassword=request.POST.get("password")
        if userpassword==password:
            b=Buy()
            b.username=username
            b.phone=username
            b.password=myencode(password)
            b.save()
            return HttpResponseRedirect('/buy/login/')
        else:
            data="密码不一致！"
    return render(request, 'buy/phone.html',{'data':data})

def login(request):
    data=''
    if request.method=='POST' and request.POST:
        name=request.POST.get('username')
        password=request.POST.get('userpass')
        user=Buy.objects.filter(username=name).first()
        email=Buy.objects.filter(email=name).first()
        phone=Buy.objects.filter(phone=name).first()
        if user or email or phone  and user.password==myencode(password):
            response=HttpResponseRedirect('/buy/index/')
            response.set_cookie('name',name)
            response.set_cookie('id',user.id)
            request.session['user']=name
            return response
        else:
            data='用户名或密码错误'
    return render(request, 'buy/login.html',{'data':data})

def logout(request):
    response = HttpResponseRedirect("/buy/login/")
    response.delete_cookie("name")
    response.delete_cookie("id")
    del request.session["user"]
    return response

def randomNum():
    num=random.randint(100000,999999)
    return num

def sendemail(request):
    data={"data":"返回值"}
    if request.method=="GET" and request.GET:
        email=request.GET.get("email")
        subject = "注册邮件"
        num=randomNum()
        text_content = "hello python"
        html_content ="""
            <p>尊敬的用户，你的验证码为%s</p>
        """%num
        message = EmailMultiAlternatives(subject,text_content,"18224516533@163.com",[email])
        message.attach_alternative(html_content,"text/html")
        message.send()
        check=CheckEmail()
        check.num=num
        check.time=datetime.datetime.now()
        check.email=email
        check.save()
    return JsonResponse(data)

def registerEmail(request):
    data=''
    if request.method=='POST' and request.POST:
        username=request.POST.get("email")
        password=request.POST.get("userpassword")
        userpassword=request.POST.get("password")
        code=request.POST.get("code")
        email = CheckEmail.objects.filter(email=username).first()
        if email and code==email.num:
            now=time.mktime(datetime.datetime.now().timetuple())
            old=time.mktime(email.time.timetuple())
            if now-old>=84600:
                data='验证码过期'
                email.delete()
            else:
                if userpassword==password:
                    b=Buy()
                    b.username=username
                    b.email=username
                    b.password=myencode(password)
                    b.save()
                    email.delete()
                    return HttpResponseRedirect('/buy/login/')
                else:
                    data="密码不一致！"
                    email.delete()
        else:
            data='验证码或邮箱错误'
            email.delete()
    return render(request, 'buy/email.html',{'data':data})

@cookieValid
def detail(request,num):
    all={}
    data=0
    allimg=[]
    good=Goods.objects.get(id=num)
    seller=good.seller.id
    goods=Goods.objects.filter(seller_id=seller)
    mg=good.image_set.all()
    for i in mg:
        allimg.append(i.img_adress.url)
    for i in goods:
        images=i.image_set.first()
        paths=(str(images.img_adress))
        if int(i.id)!=int(num) and data<=10:
            all[i]=paths
            data+=1
    img=good.image_set.first()
    path = str(img.img_adress)
    return render(request,'buy/details.html',locals())

@cookieValid
def car(request):
    id = request.COOKIES.get('id')
    add=Address.objects.filter(buyer=int(id))
    data=[]
    pay=0
    id=request.COOKIES.get("id")
    goodlist=BuyCar.objects.filter(user=int(id))
    for good in goodlist:
        money=float(good.price)*int(good.num)
        pay+=money
        data.append({'money':money,'good':good})
    return render(request,'buy/buyCar.html/',locals())

@cookieValid
def jump(request,goodid):
    id=request.COOKIES.get("id")
    good = Goods.objects.filter(id=int(goodid)).first()
    img = good.image_set.first()
    image = str(img.img_adress)
    if request.method=="POST" and request.POST:
        count=request.POST.get("count")
        money = float(good.goods_price) * int(count)
        butcar=BuyCar.objects.filter(user=int(id),goodId=goodid).first()
        if butcar:
            butcar.num+=int(count)
            butcar.save()
        else:
            car=BuyCar()
            car.goodId=goodid
            car.name=good.goods_name
            car.price=good.goods_price
            car.user=Buy.objects.get(id=int(id))
            car.num=int(count)
            car.picture=img.img_adress
            car.save()
    else:
        HttpResponseRedirect('/buy/login/')
    return render(request,'buy/jump.html/',locals())

@cookieValid
def delete(request,num):
    id = request.COOKIES.get("id")
    goods=BuyCar.objects.filter(user=int(id),goodId=num)
    goods.delete()
    return HttpResponseRedirect('/buy/car/')

@cookieValid
def clear(request):
    id = request.COOKIES.get("id")
    goods = BuyCar.objects.filter(user=int(id))
    goods.delete()
    return HttpResponseRedirect('/buy/car/')

@cookieValid
def address(request):
    id=request.COOKIES.get('id')
    if request.method=='POST' and request.POST:
        recver=request.POST.get('recver')
        phone=request.POST.get('phone')
        address=request.POST.get('address')
        add=Address()
        add.recver=recver
        add.phone=phone
        add.address=address
        add.buyer=Buy.objects.get(id=int(id))
        add.save()
        return HttpResponseRedirect('/buy/addressList/')
    return render(request,'buy/address.html')

@cookieValid
def addressList(request):
    id = request.COOKIES.get('id')
    add=Address.objects.filter(buyer=int(id))
    return render(request, 'buy/addressList.html', locals())

@cookieValid
def addressDel(request,id):
    add = Address.objects.filter(id=int(id))
    add.delete()
    return HttpResponseRedirect('/buy/addressList/')

@cookieValid
def addressChange(request,id):
    addChange=Address.objects.filter(id=int(id)).first()
    if request.method == 'POST' and request.POST:
        recver = request.POST.get('recver')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        addChange.recver = recver
        addChange.phone = phone
        addChange.address = address
        addChange.save()
        return HttpResponseRedirect('/buy/addressList/')
    return render(request, 'buy/address.html',locals())

@cookieValid
def orderAdd(request):
    buyId=request.COOKIES.get('id')
    list=[]
    all=[]
    if request.method=="POST" and request.POST:
        address=request.POST.get('address')
        print(address,"aa")
        pay=request.POST.get('pay')
        money=0
        for k,v in request.POST.items():
            if k.startswith('ok'):
                car=BuyCar.objects.get(id=int(v))
                price=float(car.num)*float(car.price)
                money+=price
                list.append({'price':price,'buy':car})
        Addr=Address.objects.get(id=int(address))
        order=Order()
        now=datetime.datetime.now()
        order.number=str(random.randint(10000,99999))+now.strftime("%Y%m%d%I%M%S")
        order.time=now
        order.statue=1
        order.money=money
        order.user=Buy.objects.get(id=int(buyId))
        order.orderAddress=Addr
        order.save()
        for i in list:
            good=i['buy']
            g=OrderGoods()
            g.goodsId=good.id
            g.goodsName=good.name
            g.goodsPrice=good.price
            g.goodsPicture=good.picture
            g.order=order
            g.goodsNum=good.num
            g.save()
        id=Order.objects.get(number=order.number)
        data=OrderGoods.objects.filter(order=id)
        for k in data:
            j=int(k.goodsNum)*float(k.goodsPrice)
            all.append({"money":j,"data":k})
        return render(request,'buy/order.html',locals())
    return HttpResponseRedirect('buy/car/')


from alipay import AliPay
@cookieValid
def jiezhang(request):
    a = ''
    if request.method == "POST" and request.POST:
        zhifu = request.POST.get("zhifu")
        alipay_public_key_string = '''-----BEGIN PUBLIC KEY-----
            MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwpMXTo+5HvNRQYN5wVimVMrR+LdBYAUJvbwKp+DDjB+4UKt2x8xzmRvP3qmMHNSU98rosxw96O6R4cW34e5/tHVKZU7Sp1DTD0Osrx9IFXv2bTIlDOA6B5Yh8A6O58tgug/oIyOmdTvrDCN6lOfFEgAJNcjzopgMkixSXcpBdEYiVR1OAseXk4bZvVsFeMH10J5GTqUcg56BsYcsWixTH0YTJkR0YRMgyypIrNyJyIg4HCVuNIY2JjKN5ufBcSmUrh5tu5bkHVR7SJ31wDjYiuqLq/7Z7QVcTlQE8p4w0o3TSg1Ig9ktLbt4d5iKP7sBtjBKJegh7a0IrB/3vdTLuwIDAQAB
        -----END PUBLIC KEY-----'''
        app_private_key_string = '''-----BEGIN RSA PRIVATE KEY-----
           MIIEpAIBAAKCAQEAwpMXTo+5HvNRQYN5wVimVMrR+LdBYAUJvbwKp+DDjB+4UKt2x8xzmRvP3qmMHNSU98rosxw96O6R4cW34e5/tHVKZU7Sp1DTD0Osrx9IFXv2bTIlDOA6B5Yh8A6O58tgug/oIyOmdTvrDCN6lOfFEgAJNcjzopgMkixSXcpBdEYiVR1OAseXk4bZvVsFeMH10J5GTqUcg56BsYcsWixTH0YTJkR0YRMgyypIrNyJyIg4HCVuNIY2JjKN5ufBcSmUrh5tu5bkHVR7SJ31wDjYiuqLq/7Z7QVcTlQE8p4w0o3TSg1Ig9ktLbt4d5iKP7sBtjBKJegh7a0IrB/3vdTLuwIDAQABAoIBABwaltE4HSsFRgVKcjmlDlFNAksEXSL7V07abEeXRWdl5X9xZLSzKTdCNyIYJy663dF0s2u7do3Ad72+izLM+hEcp+Q+IFseZ33a7oRU5lqEDzHyfjt/36Hc44YC9E0yqQP27Da3HYHtZ6PXNAtx9psE+k+UeOxRPe+XC0aUwiODBQF7Cie2+KZW9iuxNK8nQlna5dwf0xF6H0GDsUN65YsSIns8W5u1egN3vvKvY96JLYT8zzlgQu31hOx6cI0qdIItqI5sIRNRuhJi7mqZuHmP1sANZKMNxiV9zOQWqGybj95ct64VzUtoB3jwRldsYGa0jdYXoCSoDyHi7+qY4mECgYEA9teZikHXpLJjTUJ2voTDjr+e1rj/YWxoNqP2yVK14FzNBOtOghm8Un4RLhqNgK65HG2vP0O4+6+2a7hWjn9aJGBjPYMoIdcTR2bbGeW4BnNYyQ3ZLTxV8UysIRQuePYeHugheGpuRzCR6yNIyLSoO+8BOAT8xb0esLsmh1qoeLkCgYEAycsTfLcd6fk3+vb8twOuT6uMZdIuRYWFIlWVgRIPRjEXmb25PIpFZZ1fIw0+CW1mt1fbfCx5mX1zPTnjjDNyQNnemKmsz8+5ulelhW7dHs8HSSNqugm0F1oJngs71WnE/S/7Vcitf3V5F5tj81ALJp74bU3TxXAatVpx2E27hhMCgYEAv9sPcdB/RXmJiTFRjf8u6DKzyHz9scFKtr12QUBSMNKwX1RtLt3F6/AkdksZFJ25LwlpnqiKjMUj6lHapOMDMybfu53HgZXjXCnrvhM4l3rr1Uk4Ndqhie1oFEXVYRsaijcuXKOMlzR/Fd3U4nrYD81SizIFLcQyqHauGaIzM7ECgYBu9FVjtsAg/WJ1gMbVzpVSwy2wcs/0dAUPKuXIkWiKnMWwSCyJCDI+PDiqakaZImlfGFTbwwydg+gQWzstxL/mvqTxZiJaJYqm1jhx1NKKdSU5ZtrxLhKy4FP3bY/ZuY2R9YcJ1Qzoz2vkuhFMIM/wzWoll6yAnDJjUzbTy3H3twKBgQDB+lTLPnV8uQM4GoAxS2lhoLgFpF6VuS+57D7EPMNj185Zr+r0iyaR+UCdczFlcoI7Rs2ecKNHat9W0rI74OOqdaTpK/KGur+3OcDyY3RZdz1yCvfDkxQHAvygMw32JJovLUksvPdAFMBAychmbtbyX2DSGaC0uy7Su0sbj7Rlog==
        -----END RSA PRIVATE KEY-----'''
        # 如果在Linux下，我们可以采用AliPay方法的app_private_key_path和alipay_public_key_path方法直接读取.emp文件来完成签证
        # 在windows下，默认生成的txt文件，会有两个问题
        # 1、格式不标准
        # 2、编码不正确 windows 默认编码是gbk


        #实例化应用
        alipay = AliPay(
            appid = "2016092500591642", #支付宝app的id
            app_notify_url = None,   #会掉视图
            app_private_key_string = app_private_key_string,  #私钥字符
            alipay_public_key_string = alipay_public_key_string, #公钥字符
            sign_type= "RSA2",  #加密方法
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no = "00106123",
            total_amount =str(zhifu), # 将Decimal类型转换为字符串交给支付宝
            subject ="鲜果商城",
            return_url = "http://127.0.0.1:8000/buy/car/",
            notify_url=None # 可选, 不填则使用默认notify url
        )
        a = ("https://openapi.alipaydev.com/gateway.do?"+order_string)
    return HttpResponseRedirect(a)



# Create your views here.
