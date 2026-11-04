def verify_binance_payment(order_id, expected_amount):
    clean_id = str(order_id).strip()
    if clean_id in USED_TRANSACTIONS:
        return False, "رقم العملية هذا تم استخدامه مسبقاً من قبل!"
    
    timestamp = int(time.time() * 1000)
    
    # 1. فحص بوابة Binance Pay
    url_pay = "https://api.binance.com/sapi/v1/pay/transactions"
    qs_pay = urllib.parse.urlencode({"timestamp": timestamp, "limit": 100})
    sig_pay = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), qs_pay.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 2. فحص سجل الإيداعات والتحويلات لحسابك الشخصي
    url_dep = "https://api.binance.com/sapi/v1/capital/deposit/hisrec"
    qs_dep = urllib.parse.urlencode({"timestamp": timestamp, "coin": "USDT"})
    sig_dep = hmac.new(BINANCE_SECRET_KEY.encode('utf-8'), qs_dep.encode('utf-8'), hashlib.sha256).hexdigest()
    
    try:
        # تجربة فحص Pay أولاً
        res = requests.get(f"{url_pay}?{qs_pay}&signature={sig_pay}", headers={"X-MBX-APIKEY": BINANCE_API_KEY}, timeout=8)
        data = res.json()
        
        # إذا ردت باينانس بخطأ صلاحيات (ليس حساب تاجر)
        if data.get("code") not in [None, "000000", 200]:
            err_msg = data.get("msg", str(data))
            # تجربة فحص الإيداع العادي
            res_dep = requests.get(f"{url_dep}?{qs_dep}&signature={sig_dep}", headers={"X-MBX-APIKEY": BINANCE_API_KEY}, timeout=8)
            dep_data = res_dep.json()
            if isinstance(dep_data, list):
                for tx in dep_data:
                    if (str(tx.get("txId", "")) == clean_id) and float(tx.get("amount", 0)) >= expected_amount:
                        USED_TRANSACTIONS.add(clean_id)
                        return True, "تم التحقق بنجاح من محفظتك"
            
            return False, f"رد باينانس: {err_msg} (كود: {data.get('code')})"

        if data.get("code") == "000000" and "data" in data:
            for tx in data["data"]:
                t_id = str(tx.get("orderId", ""))
                p_id = str(tx.get("prepayId", ""))
                if (t_id == clean_id or p_id == clean_id) and float(tx.get("amount", 0)) >= expected_amount and tx.get("currency") == "USDT":
                    USED_TRANSACTIONS.add(clean_id)
                    return True, "تم التحقق بنجاح"
            return False, "لم يتم العثور على حوالة بهذا الرقم في باينانس أو أن المبلغ غير مطابق."

        return False, f"رد المنصة: {data.get('msg', 'غير معروف')}"

    except Exception as e:
        return False, f"استثناء أثناء الاتصال: {str(e)}"
