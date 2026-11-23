# -*- coding: utf-8 -*-
# fix_pixora.py - يصلح ألوان السطور + اللغة العامية
# الاستخدام: python fix_pixora.py pixora_bot.py
import pathlib, sys
p = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'pixora_bot.py')
t = p.read_text(encoding='utf-8')
REPL = [('هتشوف معاينة قبل الحفظ', 'ستظهر معاينة قبل الحفظ'), ('ابعت صورة الصنف', 'أرسل صورة الصنف'), ('ابعت Custom Emoji', 'أرسل Custom Emoji'), ('ابعت ID المنتج', 'أرسل ID المنتج'), ('العائلة اتغيرت', 'تغيرت العائلة'), ('افتح المنتجات من جديد', 'افتح المنتجات من جديد'), ('اتعملت أيقونة', 'تم إنشاء أيقونة'), ('اتربطت بزر المنتج', 'تم ربطها بزر المنتج'), ('اتحفظت بالفعل', 'تم حفظها بالفعل'), ('اتحفظت', 'تم حفظها'), ('اتمسحت', 'تم حذفها'), ('رجعنا الصورة', 'تمت استعادة الصورة'), ('تقدر تحاول', 'يمكنك المحاولة'), ('هتشوف', 'ستظهر'), ('عشان', 'حتى'), ('عايز', 'تريد'), ('اتغيرت', 'تغيرت'), ('لو كانت', 'إذا كانت'), ('كل المنتجات التي تحتوي على صور لها أيقونات محدثة', 'جميع المنتجات التي تحتوي على صور لها أيقونات محدثة'), ('اضغط الزر مرة أخرى لاستكمال الباقي', 'اضغط على الزر مرة أخرى لاستكمال الباقي'), ('دفعة من', 'دفعة من'), ('ابعت الصورة', 'أرسل الصورة'), ('اكتب حذف', 'اكتب حذف'), ('مفيش', 'لا توجد'), ('دلوقتي', 'الآن')]
for a,b in REPL:
    t = t.replace(a,b)

# --- ألوان السطور: أصناف = أزرق primary، منتجات متوفرة = أزرق، فيها نافذ = أحمر danger ---
# نضيف ثابت الألوان بعد FAMILIES_PER_ROW
if 'ROW_STYLE_FAMILIES' not in t:
    t = t.replace('SINGLES_PER_ROW = 2', 'SINGLES_PER_ROW = 2\nROW_STYLE_FAMILIES = "primary"  # سطور الأصناف: أزرق\nROW_STYLE_AVAILABLE = "primary"  # سطر متوفر: أزرق\nROW_STYLE_OUT = "danger"  # سطر فيه نافذ: أحمر', 1)
# نعدل catalog_rows: نمرر الستايل لكل زر حسب السطر
old = "        folder_buttons.append(btn(label, family_callback(name), 'primary', emoji_id))"
new = "        folder_buttons.append(btn(label, family_callback(name), ROW_STYLE_FAMILIES, emoji_id))"
if old in t:
    t = t.replace(old, new)
# product_button: اللون حسب التوفر - متوفر أزرق، نافذ أحمر
t = t.replace("return btn(label, f\"item:{product['id']}\", 'danger' if unavailable else 'primary', icon_id)", "return btn(label, f\"item:{product['id']}\", ROW_STYLE_OUT if unavailable else ROW_STYLE_AVAILABLE, icon_id)")
p.write_text(t, encoding='utf-8')
print('تم: ألوان السطور + لغة رسمية')
print('عدد الاستبدالات العامية:', len(REPL))
