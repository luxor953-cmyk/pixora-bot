# -*- coding: utf-8 -*-
# fix_sort_no_icons.py
# يلغي الرموز من أزرار الأصناف + يرتب الأصناف أبجدي بدون رموز
# الاستخدام: python fix_sort_no_icons.py pixora_bot.py
import pathlib, sys, re
p = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else "pixora_bot.py")
t = p.read_text(encoding="utf-8")

# 1) إلغاء أيقونة الصنف في catalog_rows - الاسم نص فقط
# كان: label = f'{short(name, 14)} ({len(members)})' + family_emoji ...
# يبقى: label = f'{short(name, 14)} ({len(members)})' بدون أي رمز
t = re.sub(r"\n\s*if not emoji_id:\s*\n\s*label = .*?\n", "\n", t)
# لو لسه فيه family_emoji في سطر الصنف، شيله
t = t.replace("family_emoji(name) + ' ' + label", "label")
t = t.replace("family_emoji(name) + label", "label")
# اجبر زر الصنف يتبعت بدون emoji_id
t = t.replace(
    "folder_buttons.append(btn(label, family_callback(name), ROW_STYLE_FAMILIES, emoji_id))",
    "folder_buttons.append(btn(label, family_callback(name), ROW_STYLE_FAMILIES, None))"
)
t = t.replace(
    "folder_buttons.append(btn(label, family_callback(name), 'primary', emoji_id))",
    "folder_buttons.append(btn(label, family_callback(name), 'primary', None))"
)

# 2) إلغاء الرموز من أزرار المنتجات المستقلة - عشان الترتيب الأبجدي يبان صح
# product_button: شيل prefix 🔴 / 🔵 / 📦 من قدام الاسم، وخلي اللون هو اللي يدل على التوفر
# اللون: متوفر = أزرق primary، نافذ = أحمر danger - السطر كله هيتلون، مش الاسم
old_prefix = "    prefix = '' if icon_id else (('🔴 ' if unavailable else '🔵 '))"
if old_prefix in t:
    t = t.replace(old_prefix, "    prefix = ''  # تم إلغاء الرموز: الترتيب أبجدي نقي")
t = t.replace("    label = ('' if icon_id else ('🔴 ' if unavailable else '📦 ')) + name", "    label = name  # بدون رموز")

# 3) تأكيد الترتيب الأبجدي في catalog_rows: رتب names بـ normalize بدون رموز
t = t.replace(
    "for name in sorted(names, key=normalize):",
    "for name in sorted(names, key=lambda n: normalize(n)):  # أبجدي بدون رموز"
)
# في organize: رتب families بنفس الطريقة
t = t.replace(
    "names = sorted(families, key=normalize)",
    "names = sorted(families, key=lambda n: normalize(n))  # أبجدي بدون رموز"
)

# 4) شيل الرموز من عنوان صفحة الصنف
t = t.replace("f'{family_emoji(name)} {name}\n", "f'{name}\n")
t = t.replace("f'📁 {name}\n", "f'{name}\n")

p.write_text(t, encoding="utf-8")
print("تم: إلغاء الرموز + ترتيب أبجدي")
print("الأصناف هتظهر: Amazon, Apple, CapCut, ChatGPT, Claude ... بدون أي رمز قدامها")
