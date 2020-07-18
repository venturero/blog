#Başlatmadan önce xammp ı başlat  
#makaledeki havalı şeyleri çıkartan ckeditor
#Makale güncelleme ve silme olmuyor, Makale eklediğinde yeşil flash yanmıyor
#Field must be between 4 and 25 characters long. kısmını türkçe yap
#djangodaki hakkımda kısmına bak yazı fontu için
#mysqldb nasıl değiiştirilir öğren
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request#kaydetmeden localhosta gidersen değişikliği göremezsin
from flask_mysqldb import MySQL#sayfa kaynağını görüntüleye gidip layout.html i görebilirsin
from wtforms import Form,StringField,TextAreaField,PasswordField,validators#block lar sayfa kaynağını görüntülede çıkmaz
from passlib.hash import sha256_crypt#xampteki password ü bu kütüphane ile encrypt ederek göndereceğiz
from functools import wraps
from flask_session import Session
from flask_login import LoginManager
#from flask.ext.mobility.decorators import mobilized
#from flask.ext.mobility.decorators import mobile_template

#Kullanıcı giriş decoratorları 
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın.","danger")
            return redirect(url_for("login"))
    return decorated_function

app = Flask(__name__)#wtformları kullanırken inheritance yapman gerekiyor
app.secret_key = "semiventurero"


#validatorun görevi sınırlandırma getirme
#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35)])
    email = StringField("Email Adresi",validators=[validators.Length(min = 10,max = 35),validators.Email(message= "Lütfen Geçerli Bir Email Adresi Girin")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message= "Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
    ])
    confirm = PasswordField("Parola Doğrula")
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")



app.config["MYSQL_HOST"] = "localhost"#eğer mysql veritabanı uzakta kiralanmış bir veri tabanının içinde çalışsaydı onun ismini verecektik
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "YBBLOG"   
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)#flask mysql ilişkisi
@app.route("/")
def index():
    articles = [
        {"id":1,"title":"Deneme1","content":"Deneme1 icerik"},
        {"id":2,"title":"Deneme1","content":"Deneme1 icerik"},
        {"id":3,"title":"Deneme1","content":"Deneme1 icerik"},
        {"id":4,"title":"Deneme1","content":"Deneme1 icerik"}



    ]

    return render_template("index.html",articles = articles)

@app.route("/about")
def about():
    return render_template("about.html")
#Makale sayfası
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)
    
    if result > 0:#bu veri tabanında makale var anlamına geliyor
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")
@app.route("/contact")
def contact():
    return render_template("contact.html")
@app.route("/dashboard")#bunu kontrol eden decorator yazacğız
@login_required#decorator u yerleştiriyoruz
def dashboard():#kendi makalelerini almak için kod
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))#tek elemanlı bir demet olduğu için virgül bırakıyoruz

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:

        return render_template("dashboard.html")
#Kayıt olma
@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email
        password = sha256_crypt.encrypt(form.password.data)
        
        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()#veri tabanında silme işlemi vs. yapmadığında bunu koymak zorunda değilsin

        cursor.close()#bunu alışkanlık haline getir
        flash("Başarıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))#ana sayfaya get request yapıyor
    else:
        return render_template("register.html", form=form )
#Login İşlemi
@app.route("/login",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    #Formu ekstradan kontrol edeceğiz
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()#cursor oluşturduk
        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu,(username,))#demet olması için username in yanına virgül koyduk
        if result > 0:#result 0 değil demek kullanıcı var demek, o zamanda girilen parolayla veri tabanındakini karşılaştırıyoruz
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarı ile giriş yaptınz","succes")
                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("login"))            
        else:#result 0 geldiğinde buraya geliyor
            flash("Böyle bir kullanıcı bulunmuyor...","danger")#tekrardan logine dönüyoruz
            return redirect(url_for("login"))

    return render_template("login.html", form = form)
#Detay Sayfası

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")
#Logout işlemi  
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/article/<string:id>")
def detail(id):
    return "Article id"+ id
#Makale Ekleme
@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    #işlemin post mu get mi olduğunu anlıyoruz
    if request.method == "POST" and form.validate():#postta kaydetmeye çalışıyoruz
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()
        cursor.close()#bağlantı kesiyoruz

        flash("Makale Başarıyla Eklendi","succes")
        return redirect(url_for("dashboard"))
    return render_template("addarticle.html",form = form)
#Makale silme
@app.route("/delete/<string:id>")#Deletein başındaki slash ı unutma
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:#makale bize ait ve varsa result 0 dan büyük gelecek
        sorgu2 = "Delete  from articles where id = %s"
        
        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya yetkiniz yok","danger")
        return redirect(url_for("index")) 
#Makale Güncelleme
@app.route("/edit<string:id>", methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor =mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"],))#orijinalde ikinci virgül yok
        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
    else:
        #POST REQUEST
        form = ArticleForm(request.form)
        if():
            pass #validator kontrolü yap

        newTitle = form.title.data
        newContent = form.title.data

        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))#veri tabanındaki bilgi şu anda güncellenmiş oldu

        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")

        return redirect(url_for("dashborad"))

#Makale Form
class ArticleForm(Form):#formdan inheritence yaptık
    title = StringField("Makale Başlığı",validators=[validators.Length(min = 5,max = 100)])
    #content in büyük alana ihtiyacı var o yüzden textareafildde yapıyoruz
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min =10)])

#Arama URL
@app.route("/search",methods = ["GET","POST"])#adres çubuğuna search yazarsan otomatik ana sayfaya gitmeyi sağlıyorum
def search():#hem post hem get request gelebilir sadece post requeste izin vermemiz gerekiyor
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        cursor = mysql.connection.cursor()
       
        sorgu = "Select * From articles where title like '%"+ keyword +"%'"

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))#url forun içindeki articleın string halinde olması gerekiyor
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",aricles = articles)
def profile(durum):
    if durum == "changeinfo":
        if request.method=="POST" :
            form = ChangeinfoForm(request.form)
            if form.validate() :
                new_name=form.name.data
                new_username=form.username.data
                new_email=form.email.data
                
                cursor=mysql.connection.cursor()
         
                sorgu="Update users Set name=%s,email=%s,username=%s where id=%s"
                
                cursor.execute(sorgu,(new_name,new_email,new_username,id))
 
                mysql.connection.commit()
                print(new_username)
                cursor.close()
                flash("Başarıyla güncellendi","success")
                return redirect(url_for("index"))
         
         
        else:
           
            cursor = mysql.connection.cursor()
    
            sorgu = "Select * from users where username = %s"
    
            cursor.execute(sorgu,(session["username"],))
    
            user = cursor.fetchone()
            form = ChangeinfoForm()
    
            form.name.data = user["name"] 
            form.username.data = user["username"]
            form.email.data = user["email"]
 
            return render_template("profile.html",form = form,durum = durum)
    else:
        form = ChangepassForm()
 
        if request.method=="POST" and form.validate():
    
            name=form.name.data
            username=form.username.data
            email=form.email.data
                
            cursor=mysql.connection.cursor()
         
            sorgu="Update users Set name=%s,username=%s,email=%s where username=%s"
              
            mysql.connection.commit()
            
            cursor.execute(sorgu,(name,username,email,id))
               
            cursor.close()
         
            return redirect(url_for("index"))
         
         
        else:
            
            return render_template("profile.html",form = form,durum = durum)
 # Profil Bilgi Formu
class ChangeinfoForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=4,max=25,message="Lütfen adınız 4 karakter ile 25 karakter arasında olsun.")])#validators ile kısıtlamalalar getiriyoruz. Birden fazla kısıtlama için liste kullanıyoruz.
    username = StringField("Kullanıcı Adı",validators=[validators.length(min=5,max=35)])
    email = StringField("Email Adresi",validators=[validators.Email(message="Lütfen Geçerli Bir Email Adresi Girin...")])#valitadors.email, girilen email'in gerçek olup olmadığını kontrol eder
#Profil Şifre Formu
class ChangepassForm(Form):
    password = PasswordField("Parola", validators=[
        validators.data_required(message="Lütfen bir parola belirleyin..."), #veri girişi ister, boş bırakılmaz.
        validators.EqualTo(fieldname = "confirm", message="Parolanız Uyuşmuyor...") #iki şifrenin de(confirm-password) birbirine eşit olması gerekir.
    ])
    confirm = PasswordField("Parola Doğrula")

if __name__ == '__main__':
    app.run(debug=True)
    