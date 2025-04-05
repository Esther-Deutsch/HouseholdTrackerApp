# בשביל שנוכל ליצור שרת flask יבוא של הספריה 
from flask import Flask, render_template, request, redirect
# 
from extensions import db, login_manager, current_user, login_user, logout_user
# יבוא של המחלקות 
from models.Purchases import Purchases
from models.User import User

# שנוכל להתעסק עם תאריכים datetime יבוא המודול
from datetime import datetime, timedelta
from decimal import Decimal

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
        exist = User.query.filter_by(password=password).first()
        
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
        user = User.query.filter_by(password=password).first()
        
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
        return render_template("login.html", message="התחבר לאפליקציה")
    # אם המשתמש מחובר - יוצר רשימה מסוננת רק של הקניות של המשתמש הנוכחי
    purchases = Purchases.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', purchases=purchases)

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
    # ניתוב מחדש עם הרשימה של השבוע האחרון
    return render_template('profile.html', purchases=purchases)

# הוספת קניה לרשימת הקניות
@app.route('/add', methods=["POST"])
def add():
    
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
    delete_purchase = Purchases.query.get_or_404(id)
    db.session.delete(delete_purchase)
    db.session.commit()
    return redirect('/profile')

# התנתקות מהפליקציה
@app.route('/logout', methods=["GET"])
def logout():
    # במקרה ויש משמתש מחובר
    if current_user.is_authenticated:
        logout_user()
    return redirect("/")

# ======================
# הרצת התוכנית אם תנאי
# ======================
if __name__ == "__main__":
    app.run(debug=True)
