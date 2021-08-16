from logging import root
import re
from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField, form,validators
from flask_wtf.file import FileField, FileRequired

from passlib.hash import sha256_crypt
from functools import wraps
import os
from flask import Flask, flash, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from werkzeug.datastructures import CombinedMultiDict



def LoginControl(f):
    @wraps(f)
    def LoginControlDecorator(*args, **kwargs):
        if session.get("IsLogged"):
           return f(*args, **kwargs)
        else:
            flash("Lutfen once giris yapin","warning")
            return redirect(url_for("login"))
    return LoginControlDecorator
            




class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(message="lsjdlfj",min=4,max=30)])
    username = StringField("Kullanici Adi",validators=[validators.length(min=4,max=30)])
    email=StringField("Email",validators=[validators.Email("Gecerli email girin")])
    password=PasswordField("parola",validators=[validators.data_required("Sifre zorunlu"),validators.equal_to(fieldname="confirm",message="Sifreyi dogrulayin")])
    confirm=PasswordField("parola dogrula")
class LoginForm(Form):
    username=StringField()
    password=PasswordField()

class AddArticleForm(Form):
    title=StringField("Baslik",validators=[validators.length(min=5,max=50)])
    content=TextAreaField("Content",validators=[validators.length(max=10000000)])
class UploadForm(FlaskForm):
    file = FileField(validators=[FileRequired()])

app = Flask(__name__)
app.secret_key="asdf"
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="alperab"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

mysql=MySQL(app)



@app.route("/users/<string:username>")
@LoginControl
def profile(username):
    if username == session["username"]:
        return render_template("profile.html")
    else:
        flash("Bu hesaba girmek icin oturum acmalisiniz","danger")
        return redirect(url_for("yazi"))
@app.route("/uploadarticle",methods=["GET","POST"])
@LoginControl
def uploadarticle():




    return redirect(url_for("addarticle"))
 

@app.route("/")
def yazi():

    return render_template("index.html")
@app.route("/about")
def about():

    return render_template("about.html")
@app.route("/register",methods=["GET","POST"])
def register():

    form=RegisterForm(request.form)

    if request.method=="POST" and form.validate() :
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        sorgu="Insert into users (name,email,username,password) values(%s,%s,%s,%s)"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Basariyla kayit oldunuz","success")

        return  redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    tempUsername=form.username.data
    tempPassword=form.password.data



    if request.method=="POST":
        cursor = mysql.connection.cursor()
        sorgu="Select * from users where username=%s"
        index=cursor.execute(sorgu,(tempUsername,))
        data=cursor.fetchone()
        if index>0:
            realPassword=data["password"]
            if sha256_crypt.verify(tempPassword,realPassword):
                session["IsLogged"]=True
                session["username"]=tempUsername
                flash("Giris Basarili","success")
                return redirect(url_for("yazi"))
            else:
                flash("Sifre Yanlis","danger")
                return redirect(url_for("login"))

        else:
            flash("kullanici yok","danger")
            return redirect(url_for("login"))            
    return render_template("login.html",form=form)
@app.route("/logout")
def logout():
    
    session.clear()
    return redirect(url_for("yazi"))
@app.route("/dashboard")
@LoginControl
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        tempCurrentArticles=cursor.fetchall()
        return render_template("dashboard.html",articleList=tempCurrentArticles)

    else:
        return render_template("dashboard.html")
@app.route("/addarticle",methods=["GET","POST"])
@LoginControl
def addarticle():
    form=AddArticleForm(request.form)
    fileForm=UploadForm(CombinedMultiDict((request.files, request.form)))

    if request.method=="POST":
        if request.form.get('submit_button') == 'Do Something':   
            f=fileForm.file.data
            form.title.data= secure_filename(f.filename).rsplit(".",1)[0]
            for line in f.stream.readlines():
                form.content.data+=str(line.decode("utf-8"))

                
        elif form.validate():
            
            title=form.title.data
            content=form.content.data
            cursor=mysql.connection.cursor()
            sorgu=("Insert into articles(title,author,content) values(%s,%s,%s)")
            cursor.execute(sorgu,(title.upper(),session["username"],content))
            mysql.connection.commit()
            cursor.close()        
            flash("Makale basariyla eklendi","success")
            return redirect(url_for("dashboard"))            
    return render_template("addarticle.html",form=form,fileForm=fileForm)
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="Select * from articles"
    makaleSayisi=cursor.execute(sorgu)
    if makaleSayisi>0:
        articleList=cursor.fetchall()
        return render_template("articles.html",articleList=articleList)
    else:
        return render_template("articles.html")
@app.route("/article/<string:i>")
def article(i):
    cursor=mysql.connection.cursor()    
    sorgu="Select * from articles where id = %s"
    result=cursor.execute(sorgu,(i,))
    if result>0:
        article=cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
@app.route("/dashboard/delete/<string:id>")
@LoginControl
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author=%s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where author = %s and id = %s"

        cursor.execute(sorgu2,(session["username"],id))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))
@app.route("/dashboard/edit/<string:id>",methods=["GET","POST"])
@LoginControl
def editarticle(id):
    cursor=mysql.connection.cursor()
    if request.method=="GET":
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result ==0:
            flash("Boyle bir makale bulunmuyor ya da yetkiniz yok","danger")
            return redirect(url_for("yazi"))
        else:
            article = cursor.fetchone()
            form = AddArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]

            return render_template("editarticle.html",form=form)
        
    else:
        sorgu2="Update articles Set title =%s,content=%s where id =%s"
        form=AddArticleForm(request.form)

        cursor.execute(sorgu2,(form.title.data,form.content.data,id))
        mysql.connection.commit()
        flash("Makale basariyle guncellendi","success")
        return redirect(url_for("dashboard"))
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("yazi"))
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%" + keyword +"%'"
        result=cursor.execute(sorgu)
        if result ==0:
            flash("Aradiginiz kelimeye gore bir makale bulunamadi","danger")
            return redirect(url_for("articles"))

        else:
            articleList=cursor.fetchall()

            return render_template("articles.html",articleList=articleList)

        
        
    
    




        


if __name__ =="__main__":
    app.run(debug=True)
