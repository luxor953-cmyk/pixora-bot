# -*- coding: utf-8 -*-
# fix_sort_final.py - ترتيب أبجدي نهائي للأصناف
# الاستخدام: python fix_sort_final.py pixora_bot.py
import pathlib, sys, re
p = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "pixora_bot.py")
t = p.read_text(encoding="utf-8")

# 1) دالة ترتيب أبجدي صح: تشيل الرموز + تخلي الحروف صغيرة + تشيل المسافات الزيادة
sort_func = 
