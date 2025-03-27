import numpy as np
import pandas as pd


product_data = {
    "ball": "toys",
    "doll": "toys",
    "skirt": "clothing",
    "pencil": "stationary",
    "paper": "stationary",
    "shirt": "clothing",
    "shoes": "clothing",
}

# =================== numpy ====================

# מערך של מוצרים
products_name = list(product_data.keys())
# מערך של כמויות - עם הגרלת מספרים מאחד עד עשר
products_qty = np.random.randint(1,10, len(products_name))
# יצירת מערך עם מחירים רמדומליים עם הגדרה שיהיה עם שתי ספרות אחרי הנקודה
products_price = np.random.uniform(10, 150, len(products_name)).round(2)


# הדפסות
# print(products_name)
# print(products_qty)
# print(products_price)

# =================== pandas ====================

# יצירת דאטה פריים עם נתונים שאני הכנסתי ידנית
df = pd.DataFrame(
    {
     "a" : [4, 5, 6],
     "b" : [7, 8, 9],
     "c" : [10, 11, 12]
    },
    index = [1, 2, 3])

# יצירת דאטה פריים מהנתונים של המערכת
products_df = pd.DataFrame(
    {
     "name" : products_name,
     "qty" : products_qty,
     "price" : products_price,
     "categories": [product_data[product] for product in products_name]
    },
    index = np.arange(1, len(products_name)+1)
)

# print(df)
# print(products_df)


