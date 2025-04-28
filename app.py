# בשביל שנוכל ליצור שרת flask יבוא של הספריה 
from flask import Flask, render_template, request, redirect, send_file, current_app
# יבוא מתוך קובץ חיצוני את הדאטה בייס
from extensions import db, login_manager, current_user, login_user, logout_user
# יבוא ספרייה זו לשם יצירת דאטה פריים
import pandas as pd
# ספרייה ליצירת מערכים
import numpy as np
# יבוא ספריה ליצירת גרפים
from matplotlib import pyplot as plt
from matplotlib import rc
# ספרייה שתאפשר "גלישה" לאתרים
from bs4 import BeautifulSoup
import lxml
# יבוא של המחלקות 
from models.Purchases import Purchases
from models.User import User
# לצורך שמירת הגרפים os יבוא המודול 
import os
# שנוכל להתעסק עם תאריכים datetime יבוא המודול
from datetime import datetime, timedelta
from decimal import Decimal


# הגדרת גופן תומך בעברית
rc('font', family='Arial')  # ודאי שגופן Arial מותקן במערכת
plt.rcParams['axes.unicode_minus'] = False  # תמיכה בסימנים מתמטיים

def create_app():
    # app הכנת אוביקק חכם ליצירת שרת והכנסתו לתוך משתנה 
    app = Flask(__name__)
    # הגדרת ניתוב לדאטה בייס
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///householer.db"
    
    # Required for session management
    app.secret_key = "your_secret_key"  
    # app - אתחול קובץ ההרחבה
    # הכנסה לתוך משתנה מופע מסוג הדאטה בייס
    db.init_app(app)
    login_manager.init_app(app)


    # בנית הטבלאות בדאטה בייס
    with app.app_context():
        # db.drop_all()
        db.create_all()
        
    return app

app = create_app()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================
# בקשות שרת 
# ==================

# ניתוב התחלתי - דף הבית
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

# דף שבו משתמש חדש יכול להרשם - POST ו GET בקשות של  
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # בדיקה שכל השדות מלאים
        if not name or not email or not password:
            return render_template("register.html", message = "יש למלא את כל השדות", name=name, email=email, password=password)
        # בודק אם קיים משתמש זהה
        exist = User.query.filter_by(email=email).first()
        
        # במקרה וקיים
        if exist:
            return render_template("register.html", message = "משתמש זה קיים כבר, נסה שנית")
        # אם לא קיים
        new_user = User(name = name, email = email, password =password)
        db.session.add(new_user)
        db.session.commit()
        
        return render_template("profile.html")
 
# דף שבו משתמש יכול להתחבר - POST ו GET בקשות של    
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        
        # בדיקה שכל השדות מלאים
        if not email or not password:
            return render_template("login.html", message = "יש למלא את כל השדות", email=email, password=password)
        # בודק אם קיים משתמש זהה
        user = User.query.filter_by(email=email).first()
        
        # במקרה ולא קיים
        if not user:
            return render_template("login.html", message = "משתמש זה אינו, נסה שנית", email=email, password=password)
        
        # שומרת את המשתמש בנוכחי
        login_user(user)
        
        # אם קיים
        return redirect('profile')

# באיזור האישי המשתמש יוכל לראות את רשימת הקניות שלו   
@app.route('/profile', methods=["GET"])
def profile():
    # במקרה שהמשתמש לא מחובר
    if not current_user.is_authenticated:
        return render_template("register.html", message="התחבר לאפליקציה")
    # אם המשתמש מחובר - יוצר רשימה מסוננת רק של הקניות של המשתמש הנוכחי
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    message = "אין לך עדיין קניות ברשימה, צור רשימה"
    return render_template('profile.html', purchases=purchases, message=message)

# הצגת הקניות מהשבוע האחרון
@app.route('/profileWeek', methods=["GET"])
def profileWeek():
    
    # חישוב התאריך של 7 ימים אחורה
    seven_days_ago = (datetime.now() - timedelta(days=7)).date()
    
    # שליפת קניות המשבוע האחרון
    purchases = Purchases.query.filter(
        Purchases.user_id == current_user.id,
        Purchases.date >= seven_days_ago
    ).all()
    message = "אין לך קניות מהשבוע האחרון"
    # ניתוב מחדש עם הרשימה של השבוע האחרון
    return render_template('profile.html', purchases=purchases, message=message)

# הצגת הקניות לפי טווח תאריכים
@app.route('/profileRange', methods=["GET", "POST"])
def profileRange():
    
    # אם המשתמש לא מחובר - למקרה של דוגמא
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")    
    
    if request.method == "POST":
    # שליפת תאריך מהטופס 
        date_str_from = request.form.get("from")
        date_str_to = request.form.get("to")
    
        # datetime המרת התאריכים לפורמט 
        date_from = datetime.strptime(date_str_from, '%Y-%m-%d')
        date_to = datetime.strptime(date_str_to, '%Y-%m-%d')
    
        purchases = Purchases.query.filter(
            Purchases.user_id == current_user.id,
            Purchases.date >= date_from,
            Purchases.date <= date_to
        ).all()
        
        message = "אין לך קניות בטווח הנתון"
        # ניתוב מחדש עם הרשימה של השבוע האחרון
        return render_template('profile.html', purchases=purchases, message=message)
    
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    message = "אין לך עדיין קניות ברשימה, צור רשימה"
    return render_template('profile.html', purchases=purchases, message=message)

# הוספת קניה לרשימת הקניות
@app.route('/add', methods=["POST"])
def add():
    
    # אם המשתמש לא מחובר - למקרה של דוגמא
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")    
    
    # שליפת הנתונים מהטופס
    user_id = current_user.id
    name = request.form.get("name")
    qty = request.form.get("qty")
    price = request.form.get("price")
    category = request.form.get("category")
    date_str = request.form.get("date")
    
    # המרה למספר עשרוני
    price = Decimal(price)  
    # המרה של התאריך לפורמט הנכון
    date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.now()
        
    # יצירת קניה חדשה
    purchases = Purchases(user_id=user_id, name=name, qty=qty, price=price, category=category, date=date)
    
    # הוספת הקניה לדאטה בייס ושמירה
    db.session.add(purchases)
    db.session.commit()
        
    # שליפה חדשה של רשימת הקניות
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', purchases=purchases)

# מחיקת מוצר מרשימת הקניות
@app.route('/delete/<int:id>')
def delete(id):
    
    # אם המשתמש לא מחובר - למקרה של דוגמא
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")    
    
    delete_purchase = Purchases.query.get_or_404(id)
    db.session.delete(delete_purchase)
    db.session.commit()
    # כאשר נמצאים בניתוב עם כל הקניות
    if request.path == '/profile':
        return redirect('/profile')
    # כאשר נמצאים בניתוב עם קניות רק של השבוע
    if request.path == '/profileWeek':
        return redirect('/profileWeek')
    # אחרת בניתוב של הקניות בטווח מסוים
    else:
        return redirect('/profileRange')

# התנתקות מהפליקציה
@app.route('/logout', methods=["GET"])
def logout():
    # במקרה ויש משמתש מחובר
    if current_user.is_authenticated:
        logout_user()
    return redirect("/")


# שמירת הנתונים - רשימת הקניות בדאטה פריים
@app.route('/saveData')
def saveData():
    
    # אם המשתמש לא מחובר - למקרה של דוגמא
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")    
    # שליפת כל הקניות של הלקוח
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    # מתוך הנתונים dataframe יצירת 
    data = [{
        "id": purchase.id,
        "user_id": purchase.user_id,
        "name": purchase.name,
        "qty": purchase.qty,
        "price": float(purchase.price),
        "category": purchase.category,
        "date": purchase.date.strftime('%Y-%m-%d %H:%M:%S')
    } for purchase in purchases]

    df = pd.DataFrame(data)
    file_path = "purchases_backup.csv"
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
     # שליחת הקובץ להורדה
    return send_file(file_path, as_attachment=True)

# הצגת גרף של נתונים שבועיים בשנה האחרונה
@app.route('/graph1', methods=["GET"])
def showGraph1():
    
    # בדיקה אם המשתמש מחובר
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")
    
    # שליפת כל הקניות של הלקוח
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    # מתוך הנתונים dataframe יצירת 
    data = [{
        "price": float(purchase.price),
        "date": purchase.date.strftime('%Y-%m-%d %H:%M:%S')
    } for purchase in purchases]

    df = pd.DataFrame(data)

    # בדיקה אם ה-DataFrame ריק
    if df.empty:
        return render_template("graph.html", message="אין נתונים להצגת גרף")

    # המרת עמודת date לפורמט datetime
    df['date'] = pd.to_datetime(df['date'])

    # סינון נתונים מהשנה האחרונה
    one_year_ago = datetime.now() - timedelta(days=365)
    df = df[df['date'] >= one_year_ago]
    
    # הוספת עמודת שבוע
    df['week'] = df['date'].dt.strftime('%Y-%U')

    # חישוב סך ההוצאות לכל שבוע
    weekly_expenses = df.groupby('week')['price'].sum()
    
    # יצירת גרף
    plt.figure(figsize=(10, 6))
    ax = weekly_expenses.plot(kind='bar', color='#80c3bc')

    # הגדרת כותרת וצירים עם טקסט בעברית
    ax.set_title('סך ההוצאות בכל שבוע בשנה האחרונה'[::-1], fontsize=14)
    ax.set_xlabel('שבוע'[::-1], fontsize=12, labelpad=15)
    ax.set_ylabel('סך ההוצאות'[::-1], fontsize=12)

    # סיבוב תוויות ציר ה-X
    plt.xticks(rotation=0, fontsize=10, ha='center')

    # שמירת הגרף כקובץ PNG
    graph_path = os.path.join('static', 'graphs', 'weekly_expenses.png')
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    plt.savefig(graph_path)
    plt.close()

    # הצגת הגרף
    return render_template('graph.html', graph_path=graph_path)

# גרף עוגה המציג את ההוצאות לפי קטגוריה
@app.route('/graph2', methods=["GET"])
def showGraph2():
    
    # בדיקה אם המשתמש מחובר
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")
    
    # שליפת כל הקניות של המשתמש
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    
    # יצירת DataFrame
    data = [{
        "category": purchase.category,
        "price": float(purchase.price)
    } for purchase in purchases]
    
    df = pd.DataFrame(data)
    
    # בדיקה אם ה-DataFrame ריק
    if df.empty:
        return render_template("graph.html", message="אין נתונים להצגת גרף")

    
    # חישוב סך ההוצאות לפי קטגוריות
    category_expenses = df.groupby('category')['price'].sum()
    
    # יצירת גרף עוגה
    plt.figure(figsize=(8, 8))

    # היפוך סדר האותיות עבור שמות הקטגוריות
    category_expenses.index = [category[::-1] for category in category_expenses.index]
    category_expenses.plot(
        kind='pie',
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.Paired.colors,
        textprops={'horizontalalignment': 'center'}
    )
    
    category_expenses.plot(kind='pie', autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors, textprops={'horizontalalignment': 'center'})
    plt.title('אחוז ההוצאות לפי קטגוריות'[::-1], fontsize=14)
    plt.ylabel('')  # הסתרת התווית של ציר ה-Y

    
    # שמירת הגרף כקובץ PNG
    graph_path = os.path.join('static', 'graphs', 'category_expenses.png')
    os.makedirs(os.path.dirname(graph_path), exist_ok=True)
    plt.savefig(graph_path)
    plt.close()
    
    # הצגת הגרף בדף HTML
    return render_template('graph.html', graph_path=graph_path)
  
  
@app.route('/demoProfile', methods=["GET"])
def demo():
    
    product_data = {
        "כדור": "משחקים",
        "בובה": "משחקים",
        "חצאית": "ביגוד",
        "עפרון": "מכשירי כתיבה",
        "דפים": "מכשירי כתיבה",
        "חולצה": "ביגוד",
        "נעליים": "הנעלה",
    }
    # מערך אפסים - id
    array_of_zeros = np.zeros(len(product_data), dtype=int)
    # מערך של מוצרים
    products_name = list(product_data.keys())
    # מערך של כמויות - עם הגרלת מספרים מאחד עד עשר
    products_qty = np.random.randint(1,10, len(products_name))
    # יצירת מערך עם מחירים רמדומליים עם הגדרה שיהיה עם שתי ספרות אחרי הנקודה
    products_price = np.random.uniform(10, 150, len(products_name)).round(2)
    # יצירת מערך של תאריכים רנדומליים
    product_dates = pd.to_datetime(
        np.random.uniform(
            (datetime.now() - timedelta(days=2*365)).timestamp(),  # תחילת הטווח (שנתיים אחורה)
            datetime.now().timestamp(),  # סוף הטווח (התאריך הנוכחי)
            len(products_name)  # מספר התאריכים הרצוי
        ),
        unit='s'  # המרה משניות לתאריכים
    )
    
    # יצירת דאטה פריים מהנתונים של המערכת
    products_df = pd.DataFrame(
        {
         "id": array_of_zeros,
         "name" : products_name,
         "qty" : products_qty,
         "price" : products_price,
         "category": [product_data[product] for product in products_name],
         "date": product_dates
        },
        index = np.arange(1, len(products_name)+1)
    )  
    
    # ודא שהעמודה 'date' היא מסוג datetime
    products_df['date'] = pd.to_datetime(products_df['date'])

    purchases = products_df.to_dict(orient='records')

    message = f"יש לך {len(products_name)} מוצרים ברשימת הקניות"
    return render_template('demoProfile.html', purchases=purchases, message=message)

@app.route('/demoBtns', methods=["GET"])
def demoBtsn():
    return render_template("register.html", message="עליך להתחבר לאתר")

@app.route('/products', methods=["GET"])
def products():
    
    # בדיקה אם המשתמש מחובר
    if not current_user.is_authenticated:
        return render_template("register.html", message="עליך להתחבר לאתר")

    return render_template("products.html")

@app.route('/compare', methods=["GET"])
def compare():
        
    # בניית נתיב מוחלט לקובץ products.html
    products_path = os.path.join(current_app.root_path, 'templates', 'products.html')
    
    # פתיחת הקובץ למצב של קריאה
    with open (products_path, "r", encoding="utf-8") as file:
        content = file.read() 

    soup = BeautifulSoup(content, 'lxml')
    
    # שליפת שמות ומחירי המוצרים
    products_in_store = []
    products = soup.find_all('div', class_='product')  # איתור כל המוצרים
    for product in products:
        name = product.find('p', class_='name').text.strip()  # שליפת שם המוצר
        price_text = product.find('p', class_='price').text.strip()  # שליפת המחיר
        price = float(price_text.replace('ש"ח', '').strip())  # המרת המחיר למספר
        products_in_store.append({"name": name, "price": price})

    # שליפת רשימת הקניות של המשתמש
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()

    # השוואת מחירים
    cheaper_products = []
    for purchase in purchases:
        for product in products_in_store:
            if purchase.name == product["name"] and purchase.price/purchase.qty > product["price"]:
                cheaper_products.append({
                    "name": purchase.name,
                    "user_price": purchase.price,
                    "store_price": product["price"]
                })

    # הצגת התוצאות למשתמש
    return render_template('compare.html', cheaper_products=cheaper_products)

# ======================
# הרצת התוכנית אם תנאי
# ======================
if __name__ == "__main__":
    app.run(debug=True)
