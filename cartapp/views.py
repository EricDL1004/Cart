from django.shortcuts import render, redirect
from cartapp import models
from smtplib import SMTP, SMTPAuthenticationError, SMTPException
from email.mime.text import MIMEText
from django.core.mail import send_mail
from . import models

message = ''
cartlist = []  #購買商品串列
customname = ''  #購買者姓名
customphone = ''  #購買者電話
customaddress = ''  #購買者地址
customemail = ''  #購買者電子郵件

def index(request):
	global cartlist
	if 'cartlist' in request.session:  #若session中存在cartlist就讀出
		cartlist = request.session['cartlist']
	else:  #重新購物
		cartlist = []
	cartnum = len(cartlist)  #購買商品筆數
	productall = models.ProductModel.objects.all()  #取得資料庫所有商品
	return render(request, "index.html", locals())

def detail(request, productid=None):  #商品詳細頁面
	product = models.ProductModel.objects.get(id=productid)  #取得商品
	return render(request, "detail.html", locals())

def cart(request):  #顯示購物車
	global cartlist
	cartlist1 = cartlist  #以區域變數傳給模版
	total = 0
	for unit in cartlist:  #計算商品總金額
		total += int(unit[3])
	grandtotal = total + 100  #加入運費總額
	return render(request, "cart.html", locals())

def addtocart(request, ctype=None, productid=None):
	global cartlist
	if ctype == 'add':  #加入購物車
		product = models.ProductModel.objects.get(id=productid)
		flag = True  #設檢查旗標為True
		for unit in cartlist:  #逐筆檢查商品是否已存在
			if product.pname == unit[0]:  #商品已存在
				unit[2] = str(int(unit[2])+ 1)  #數量加1
				unit[3] = str(int(unit[3]) + product.pprice)  #計算價錢
				flag = False  #設檢查旗標為False
				break
		if flag:  #商品不存在
			temlist = []  #暫時串列
			temlist.append(product.pname)  #將商品資料加入暫時串列
			temlist.append(str(product.pprice))  #商品價格
			temlist.append('1')  #先暫訂數量為1
			temlist.append(str(product.pprice))  #總價
			cartlist.append(temlist)  #將暫時串列加入購物車
		request.session['cartlist'] = cartlist  #購物車寫入session
		return redirect('/cart/')
	elif ctype == 'update':  #更新購物車
		n = 0
		for unit in cartlist:
			unit[2] = request.POST.get('qty' + str(n), '1')  #取得數量
			unit[3] = str(int(unit[1]) * int(unit[2]))  #取得總價
			n += 1
		request.session['cartlist'] = cartlist
		return redirect('/cart/')
	elif ctype == 'empty':  #清空購物車
		cartlist = []  #設購物車為空串列
		request.session['cartlist'] = cartlist
		return redirect('/index/')
	elif ctype == 'remove':  #刪除購物車中商品
		del cartlist[int(productid)]  #從購物車串列中移除商品
		request.session['cartlist'] = cartlist
		return redirect('/cart/')

def cartorder(request):  #按我要結帳鈕
	global cartlist, message, customname, customphone, customaddress, customemail # 使用全域變數
	cartlist1 = cartlist # 將購物車清單複製到區域變數
	total = 0
	for unit in cartlist:  #計算商品總金額
		total += int(unit[3])
	grandtotal = total + 100 # 總金額加上運費（運費為100）
	customname1 = customname  # 將客戶資訊賦值給區域變數，以便傳給模板
	customphone1 = customphone
	customaddress1 = customaddress
	customemail1 = customemail
	message1 = message
	return render(request, "cartorder.html", locals())

def cartok(request):  # 按確認購買鈕
    global cartlist, message, customname, customphone, customaddress, customemail # 使用全域變數
    total = 0
    for unit in cartlist: #計算商品總金額
        total += int(unit[3])
    grandtotal = total + 100 # 總金額加上運費（運費為100）
    # message = ''
	# 從 POST 請求中獲取客戶資料
    customname = request.POST.get('CustomerName', '')
    customphone = request.POST.get('CustomerPhone', '')
    customaddress = request.POST.get('CustomerAddress', '')
    customemail = request.POST.get('CustomerEmail', '')
    paytype = request.POST.get('paytype', '')

    if customname == '' or customphone == '' or customaddress == '' or customemail == '':
		# 如果任何客戶資料未填，會出現提示並重定向回訂單頁面
        message = '姓名、電話、住址及電子郵件皆需輸入'
        return redirect('/cartorder/')
    else:
		# 建立訂單
        unitorder = models.OrdersModel.objects.create(
            subtotal=total, shipping=100, grandtotal=grandtotal, customname=customname,
            customphone=customphone, customaddress=customaddress, customemail=customemail,
            paytype=paytype)  # 建立訂單
            
        order_details = [] # 用於保存訂單詳細內容
        for unit in cartlist:  # 將購買商品寫入資料庫
            total = int(unit[1]) * int(unit[2])
            models.DetailModel.objects.create(
                dorder=unitorder, pname=unit[0], unitprice=unit[1], quantity=unit[2], dtotal=total)
            order_details.append(f"{unit[0]} - 單價: {unit[1]}, 數量: {unit[2]}, 總額: {total}元")
            
        orderid = unitorder.id  # 取得訂單id

 		# 郵件內容
        order_details_str = "\n".join(order_details) # 組裝訂單詳細內容
        mailfrom = "your_email@gmail.com"  # 發送郵件的帳號
        mailto = customemail  # 客戶的電子郵件
        mailsubject = "公仔購物網-訂單通知"  # 郵件標題
        mailcontent = (
            f"感謝您的光臨，您已經成功的完成訂購程序。\n"
            f"我們將儘快把您選購的商品郵寄給您！再次感謝您支持。\n\n"
            f"您的訂單編號為：{orderid}，您可以使用這個編號回到網站中查詢訂單的詳細內容。\n\n"
            f"訂單詳細內容:\n{order_details_str}\n\n"
            "公仔購物網"
        )  # 郵件內容，包括訂單詳細資訊

        send_simple_message(mailsubject, mailcontent, mailfrom, [mailto])  # 寄信
        
        cartlist = []  # 清空購物車
        request.session['cartlist'] = cartlist # 更新 session 中的購物車
        return render(request, "cartok.html", {'customname': customname, 'orderid': orderid, 'mailto': mailto})

def cartordercheck(request):  #查詢訂單
	orderid = request.GET.get('orderid', '')  #取得輸入id
	customemail = request.GET.get('customemail', '')  #取得輸email
	if orderid == '' and customemail == '':  #按查詢訂單鈕
		firstsearch = 1
	else:
		order = models.OrdersModel.objects.filter(id=orderid).first()
		if order == None or order.customemail != customemail:  #查不到資料
			notfound = 1
		else:  #找到符合的資料
			details = models.DetailModel.objects.filter(dorder=order)
	return render(request, "cartordercheck.html", locals())

def send_simple_message(subject, message, from_email, recipient_list):
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
    except SMTPAuthenticationError:
        message = "無法登入！"
    except Exception as e:
        message = "郵件發送產生錯誤: {}".format(e)
