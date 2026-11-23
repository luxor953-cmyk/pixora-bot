# الوان السطور - Row Colors - PIXORA.EGY / Pixora
# تيليجرام مش بيسمح نختار لون خلفية السطر براحتنا، بيسمح بس بـ 3 ستايلات:
# primary = ازرق، success = اخضر، danger = احمر
# فاحنا بنتحكم في لون السطر كله من هنا:

ROW_COLORS = {
    'families': 'primary',      # سطور الاصناف كلها ازرق زي الصورة
    'available': 'primary',     # سطر منتجات متوفرة = ازرق
    'out_of_stock': 'danger',   # سطر فيه منتج نافذ = احمر زي الصورة
    'mixed': 'danger',          # سطر فيه متوفر + نافذ = احمر عشان يبان
}

# لو عايز سطور الاصناف تتبدل الوانها، بدل السطر اللي فوق بـ:
# ROW_COLORS = {'families_row_0': 'primary', 'families_row_1': 'success', ...}
# مثال: صف ازرق، صف اخضر، صف ازرق، صف اخضر...

def row_style_for_products(products_in_row):
    # لو اي منتج في السطر نافذ -> السطر كله احمر زي الصورة
    if any(sold_out(p) for p in products_in_row):
        return ROW_COLORS['out_of_stock']
    return ROW_COLORS['available']

# في catalog_rows:
# - ازرار الاصناف: btn(..., ROW_COLORS['families'])
# - ازرار المنتجات المستقلة: قسمهم صفين صفين، وكل صف ياخد row_style_for_products(صف)
