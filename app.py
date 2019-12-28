import datetime
from datetime import datetime, timedelta
import random
from flask import Flask, session, flash, abort, request, render_template, render_template_string, jsonify, redirect, url_for
from flask_babelex import Babel
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_user import current_user, login_required, roles_required, UserManager, UserMixin, user_logged_in, user_logged_out
from flask_login import LoginManager, login_user, logout_user
from sqlalchemy.sql import table, column, select
from sqlalchemy import MetaData, func
import os

class ConfigClass(object):
    SECRET_KEY = '172114205_MUCAHIT_YILMAZ_FLASK_FLY_PROJESI'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mucahit_yilmaz.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USE_TLS = False
    MAIL_USERNAME = 'xyz@gmail.com'
    MAIL_PASSWORD = 'sifre'
    MAIL_DEFAULT_SENDER = '"Flask Fly Mücahit" <xyz@gmail.com>'

    USER_APP_NAME = "Flask Fly Mücahit"
    USER_ENABLE_EMAIL = True
    USER_ENABLE_USERNAME = False
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    USER_EMAIL_SENDER_EMAIL = "noreply@example.com"

    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_REMEMBER_ME = False

    USER_LOGIN_TEMPLATE = 'login.html'
    USER_REGISTER_TEMPLATE = 'register.html'

    USER_UNAUTHORIZED_ENDPOINT = 'admin_yetkisiz'

def fly_app():

    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    login_manager = LoginManager()
    login_manager.init_app(app)

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
       translations = [str(translation) for translation in babel.list_translations()]

    db = SQLAlchemy(app)

    class User(db.Model, UserMixin):
        __tablename__ = 'users'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')
        email = db.Column(db.String(255, collation='NOCASE'), nullable=False, unique=True)
        email_confirmed_at = db.Column(db.DateTime())
        password = db.Column(db.String(255), nullable=False, server_default='')
        name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        roles = db.relationship('Role', secondary='user_roles')

    class Role(db.Model):
        __tablename__ = 'roles'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(50), unique=True)

    class UserRoles(db.Model):
        __tablename__ = 'user_roles'
        id = db.Column(db.Integer(), primary_key=True)
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
        role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))

    class UcusYeri(db.Model):
        __tablename__ = 'ucus_yeri'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(100), nullable=False, server_default='')

    class KullaniciUcuslar(db.Model):
        __tablename__ = 'kullanici_ucuslar'
        id = db.Column(db.Integer(), primary_key=True)
        departure = db.Column(db.String(100), nullable=False, server_default='')
        arrival = db.Column(db.String(100), nullable=False, server_default='')
        datetime = db.Column(db.String(100), nullable=False, server_default='')
        price = db.Column(db.String(30), nullable=False, server_default='0')
        passenger_name = db.Column(db.String(100), nullable=False, server_default='')
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))

    class Bonus(db.Model):
        __tablename__ = 'bonuslar'
        id = db.Column(db.Integer(), primary_key=True)
        name = db.Column(db.String(200), nullable=False, server_default='')
        datetime = db.Column(db.String(100), nullable=False, server_default='')
        win = db.Column(db.Integer(), nullable=False, server_default='')
        passenger_name = db.Column(db.String(100), nullable=False, server_default='')
        user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))

    class Ucuslar(db.Model):
        __tablename__ = 'ucuslar'
        id = db.Column(db.Integer(), primary_key=True)
        departure = db.Column(db.String(100), nullable=False, server_default='')
        arrival = db.Column(db.String(100), nullable=False, server_default='')
        time = db.Column(db.String(100), nullable=False, server_default='')
        price = db.Column(db.Float(), nullable=False, server_default='0')

    class Sepet:
        rezervasyonlar = {}
        bonus = {'harcanan' : 0, 'puan' : '-1'}

    user_manager = UserManager(app, db, User)

    db.create_all()
    engine = create_engine('sqlite:///mucahit_yilmaz.sqlite')
    meta = MetaData(engine).reflect()
    #table = meta.tables['gonderiler']
    #table_isim = meta.tables['isimler']

    @user_logged_in.connect_via(app)
    def _after_login_hook(sender, user, **extra):
        sender.logger.info('user logged in')

    @user_logged_out.connect_via(app)
    def _after_logout_hook(sender, user, **extra):
        sender.logger.info('user logged out')
        Sepet.rezervasyonlar = {}

    def totimestamp(dt, epoch=datetime(1970,1,1)):
        td = dt - epoch
        return int((td.microseconds + (td.seconds + td.days * 86400) * 10**6) / 10**6 )


    if not UcusYeri.query.filter(UcusYeri.name == 'İstanbul').first():
        ucusyeri = UcusYeri(
            name='İstanbul'
        )
        db.session.add(ucusyeri)
        db.session.commit()

    if not UcusYeri.query.filter(UcusYeri.name == 'Ankara').first():
        ucusyeri = UcusYeri(
            name='Ankara'
        )
        db.session.add(ucusyeri)
        db.session.commit()

    if not User.query.filter(User.email == 'uye@uye.com').first():
        user = User(
            name='Üye Üye',
            email='uye@uye.com',
            email_confirmed_at=datetime.utcnow(),
            password=user_manager.hash_password('123uye')
        )
        db.session.add(user)
        db.session.commit()

    if not User.query.filter(User.email == 'admin@admin.com').first():
        user = User(
            name='Admin Admin',
            email='admin@admin.com',
            email_confirmed_at=datetime.utcnow(),
            password=user_manager.hash_password('123admin')
        )
        user.roles.append(Role(name='Admin'))
        user.roles.append(Role(name='Agent'))
        db.session.add(user)
        db.session.commit()


    @app.route('/')
    def index():
        username = 'Ziyaretçi'
        if current_user.is_authenticated:
            username = current_user.name

        ucus_yerleri = UcusYeri.query.order_by(UcusYeri.name).all()
        return render_template('index.html', user = username, ucus_yerleri = ucus_yerleri)

    @app.route('/iletisim')
    def iletisim():
        return render_template('contact.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        Sepet.rezervasyonlar = {}
        Sepet.bonus = {'harcanan' : 0, 'puan' : '-1'}
        return redirect('/')

    @app.route('/giris', methods = ['GET', 'POST'])
    def giris():
        durum = {}
        if current_user.is_authenticated:
            return redirect('/hesabim')
        if request.method == 'POST':
            eposta = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=eposta).first()
            if not user or not user_manager.verify_password(password, user.password):
                durum = {
                    'type' : 'danger',
                    'msg' : 'Eposta adresi veya şifreniz hatalı/eksik!..'
                }
                next = request.form['next']
                return redirect(next or url_for('giris'))
            else :
                login_user(user, remember=True)
                next = request.form['next']
                return redirect(next or url_for('hesabim'))
        return render_template('login.html', durum = durum)

    @app.route('/kayit', methods = ['GET', 'POST'])
    def kayit():
        durum = {}
        if current_user.is_authenticated:
            return redirect('/')
        if request.method == 'POST':
            adsoyad = request.form['name']
            eposta = request.form['email']
            password = request.form['password']
            existing_user = User.query.filter_by(email=eposta).first()
            if existing_user is None:
                user = User(
                    name = adsoyad,
                    email = eposta,
                    email_confirmed_at = datetime.utcnow(),
                    password = user_manager.hash_password(password)
                )
                db.session.add(user)
                db.session.commit()
                durum = {
                    'type' : 'success',
                    'msg' : 'Başarıyla kayıt olundu, Giriş yapabilirsiniz'
                }
                return redirect('/giris?kayit=basarili')
            else :
                durum = {
                    'type' : 'danger',
                    'msg' : 'Kayıt olurken hata oluştu, lütfen kayıt formunu eksiksiz doldurunuz..'
                }
        return render_template('register.html', durum = durum)

    @app.route('/hesabim')
    @login_required
    def hesabim():
        return render_template('account.html')

    @app.route('/hesabim/gelecek')
    @login_required
    def hesabim_gelecek():
        now = datetime.now()
        nowdate = now.strftime("%Y-%m-%d %H:%M:%S")
        ucuslar = KullaniciUcuslar.query.filter(KullaniciUcuslar.datetime>=nowdate).filter_by(user_id=current_user.id).order_by(KullaniciUcuslar.datetime).all()
        return render_template('account/next.html', ucuslar = ucuslar)

    @app.route('/hesabim/gecmis')
    @login_required
    def hesabim_gecmis():
        now = datetime.now()
        nowdate = now.strftime("%Y-%m-%d %H:%M:%S")
        ucuslar = KullaniciUcuslar.query.filter(KullaniciUcuslar.datetime<=nowdate).filter_by(user_id=current_user.id).order_by(KullaniciUcuslar.datetime).all()
        return render_template('account/prev.html', ucuslar = ucuslar)

    @app.route('/hesabim/bonus')
    @login_required
    def hesabim_bonus():
        sum = 0
        bonus_varmi = Bonus.query.filter_by(user_id=current_user.id).first()
        if bonus_varmi:
            sum = db.session.query(func.sum(Bonus.win)).filter_by(user_id=current_user.id).one()[0]
        bonuslar = Bonus.query.filter_by(user_id=current_user.id).order_by(Bonus.id).all()
        return render_template('account/bonus.html', bonuslar = bonuslar, sum = int(sum))

    @app.route('/bonus_uygula', methods = ['POST'])
    @login_required
    def bonus_uygula():
        sum = db.session.query(func.sum(Bonus.win)).filter_by(user_id=current_user.id).one()[0]
        bonus = int(sum)
        if int(request.form['bonus_puan']) <= bonus:
            bonus = int(request.form['bonus_puan'])
        Sepet.bonus['harcanan'] = bonus
        return redirect('/sepet?bonus=basarili')

    @app.route('/sepet')
    def sepet():
        if current_user.is_authenticated:
            bonus_varmi = Bonus.query.filter_by(user_id=current_user.id).first()
            if bonus_varmi:
                Sepet.bonus['puan'] = int(db.session.query(func.sum(Bonus.win)).filter_by(user_id=current_user.id).one()[0])
        now = datetime.utcnow()
        return render_template('cart.html', ucuslarim = Sepet.rezervasyonlar, simdi = totimestamp(now), bonus = Sepet.bonus)

    @app.route('/odeme')
    @login_required
    def odeme():
        if len(Sepet.rezervasyonlar) < 1:
            return redirect('/')
        return render_template('checkout.html', ucuslarim = Sepet.rezervasyonlar, bonus = Sepet.bonus)

    @app.route('/odeme/basarili')
    @login_required
    def odeme_basarili():
        return render_template('success.html')

    @app.route('/odeme_tamamla', methods = ['POST'])
    @login_required
    def odeme_tamamla():
        if len(Sepet.rezervasyonlar) < 1:
            return redirect('/odeme?sepet=bos')
        if request.method == 'POST':
            yolcu = request.form['adsoyad']
            toplam = 0
            sepet_tarih = '25.12.2019 12:00'
            bonus_pop = int(Sepet.bonus['harcanan']) / len(Sepet.rezervasyonlar)
            for id in Sepet.rezervasyonlar:
                toplam += float(Sepet.rezervasyonlar[id]['fiyat'])
                sepet_tarih = Sepet.rezervasyonlar[id]['tarihsaat']
                kullanici_ucus = KullaniciUcuslar(
                    departure = Sepet.rezervasyonlar[id]['nereden'],
                    arrival = Sepet.rezervasyonlar[id]['nereye'],
                    datetime = datetime.strptime(Sepet.rezervasyonlar[id]['tarihsaat'], "%d.%m.%Y %H:%M"),
                    price = float(Sepet.rezervasyonlar[id]['fiyat']) - bonus_pop,
                    passenger_name = yolcu,
                    user_id = current_user.id
                )
                db.session.add(kullanici_ucus)

            if Sepet.bonus['harcanan'] == 0:
                kullanici_bonus = Bonus(
                    name = 'Kazanılan Bonus',
                    datetime = datetime.strptime(sepet_tarih, "%d.%m.%Y %H:%M"),
                    win = int(int(toplam) * 0.03),
                    passenger_name = current_user.name,
                    user_id = current_user.id
                )
            else :
                kullanici_bonus = Bonus(
                    name = 'Kullanılan Bonus',
                    datetime = datetime.strptime(sepet_tarih, "%d.%m.%Y %H:%M"),
                    win = - int(Sepet.bonus['harcanan']),
                    passenger_name = current_user.name,
                    user_id = current_user.id
                )

            db.session.add(kullanici_bonus)
            db.session.commit()

            Sepet.rezervasyonlar = {}
            if request.form['odeme_turu'] == 'kredikarti':
                return render_template('credi-card.html', toplam = toplam, bonus = '')
            return redirect('/odeme/basarili')
        return redirect('/odeme')

    @app.route('/ucuslar', methods = ['GET','POST'])
    def ucuslar():
        if request.method != 'POST':
            return redirect('/')
        nereden = request.form['nereden']
        nereye = request.form['nereye']
        ucus_tarih = request.form['tarih']
        bilet_turu = 1
        if request.form['bilet_turu'] == '1':
            bilet_turu = 1.25

        now = datetime.now()
        nowtime = '00:00'
        nowtoday = now.strftime("%d.%m.%Y")
        if nowtoday == ucus_tarih:
            nowtime = now.strftime("%H:%M")

        ucuslar = Ucuslar.query.filter(Ucuslar.time>=nowtime).filter_by(departure = nereden, arrival = nereye).order_by(Ucuslar.time).all()
        return render_template('fly.html', nereden = nereden, nereye = nereye, ucak_tarih = ucus_tarih, bilet_turu = bilet_turu, ucuslar = ucuslar)

    @app.route('/ucus-bilgi', methods = ['GET', 'POST'])
    def ucus_bilgi():
        now = datetime.now()
        min_date = now.strftime("%Y-%m-%d 00:00:00")
        max_date = now.strftime("%Y-%m-%d 23:59:59")
        day = now.strftime("%d.%m.%Y")
        if request.method == 'POST':
            min_date = datetime.strptime(request.form['bilgi_tarih'], "%d.%m.%Y")
            max_date = datetime.strptime(request.form['bilgi_tarih'], "%d.%m.%Y") + timedelta(hours=24)
            day = request.form['bilgi_tarih']
        arrival = db.session.query(
            func.count(KullaniciUcuslar.id).label('count'), KullaniciUcuslar.arrival
        ).filter(KullaniciUcuslar.datetime>=min_date, KullaniciUcuslar.datetime<=max_date).group_by(KullaniciUcuslar.arrival).all()
        departure = db.session.query(
            func.count(KullaniciUcuslar.id).label('count'), KullaniciUcuslar.departure
        ).filter(KullaniciUcuslar.datetime>=min_date, KullaniciUcuslar.datetime<=max_date).group_by(KullaniciUcuslar.departure).all()
        return render_template('stats.html', arrival = arrival, departure = departure, day = day);

    @app.route('/hesabim/ucus_iptal/<ucus_id>')
    @login_required
    def hesabim_ucus_iptal(ucus_id):
        sil = KullaniciUcuslar.query.filter_by(id=int(ucus_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/hesabim/gelecek')

    ''' Sepet İşlemleri '''
    @app.route('/sepet_listele', methods=['POST'])
    def sepet_listele():
        return {'rezervasyonlar': Sepet.rezervasyonlar, 'bonus': Sepet.bonus}

    @app.route('/sepete_ekle/<eklenecekUcusID>', methods=['POST'])
    def sepete_ekle(eklenecekUcusID):
        ucus_id = request.form['id'];
        if ucus_id in Sepet.rezervasyonlar:
            durum = 'zaten ekli'
        else :
            now = datetime.utcnow()
            tarihsaat = request.form['tarih'] + ' ' + request.form['saat']
            Sepet.rezervasyonlar[ucus_id] = {
                'id': ucus_id,
                'nereden': request.form['nereden'],
                'nereye': request.form['nereye'],
                'tarihsaat': tarihsaat,
                'fiyat': float(request.form['fiyat']),
                'eklenme':totimestamp(now)
            }
            durum = 'eklendi'
        return durum

    @app.route('/sepetten_cikar/<silinecekUcusID>', methods=['POST'])
    def sepetten_cikar(silinecekUcusID):
        sil_ucus = request.form['id'];
        del Sepet.rezervasyonlar[sil_ucus]
        if sil_ucus in Sepet.rezervasyonlar:
            durum = 'basarisiz'
        else :
            durum = 'silindi'
        return durum

    @app.route('/sepet_tumsil')
    def sepet_tumsil():
        Sepet.rezervasyonlar = {}
        return redirect('/sepet')
    ''' Sepet İşlemleri '''

    ''' Admin İşlemleri '''
    @app.route('/admin_yetkisiz')
    @login_required
    def admin_yetkisiz():
        return redirect('/hesabim?admin_yetkisiz=true')

    @app.route('/admin')
    @roles_required('Admin')
    def admin_index():
        ucus_yerleri = UcusYeri.query.order_by(UcusYeri.name).all()
        ucuslar = Ucuslar.query.order_by(Ucuslar.departure).all()
        return render_template('admin/index.html', ucus_yerleri = ucus_yerleri, ucuslar = ucuslar)

    @app.route('/admin/rezervasyonlar')
    @roles_required('Admin')
    def admin_rezervasyon():
        rezervasyonlar = KullaniciUcuslar.query.order_by(KullaniciUcuslar.id).all()
        return render_template('admin/rezervasyon.html', rezervasyonlar = rezervasyonlar)

    @app.route('/admin/bonuslar')
    @roles_required('Admin')
    def admin_bonuslar():
        bonuslar = Bonus.query.order_by(Bonus.id).all()
        return render_template('admin/bonuslar.html', bonuslar = bonuslar)

    @app.route('/admin/kullanicilar')
    @roles_required('Admin')
    def admin_kullanici():
        kullanicilar = User.query.order_by(User.id).all()
        return render_template('admin/kullanicilar.html', kullanicilar = kullanicilar)

    @app.route('/admin/kullanici_sil/<user_id>')
    @roles_required('Admin')
    def admin_kullanici_sil(user_id):
        sil = User.query.filter_by(id=int(user_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/admin/kullanicilar')

    @app.route('/admin/ucus_yeri', methods = ['POST'])
    @roles_required('Admin')
    def admin_ucus_yeri():
        if request.method == 'POST':
            ucus_yeri = request.form['ucus_yeri']
            existing_ucusyeri = UcusYeri.query.filter_by(name=ucus_yeri).first()
            if existing_ucusyeri is None:
                ucusyeri = UcusYeri(
                    name = ucus_yeri
                )
                db.session.add(ucusyeri)
                db.session.commit()
                return redirect('/admin?ucus_yeri=basarili')
            else :
                return redirect('/admin?ucus_yeri=zatenvar')
        return redirect('/admin')

    @app.route('/admin/ucus_yeri_sil/<yer_id>')
    @roles_required('Admin')
    def admin_ucus_yeri_si(yer_id):
        sil = UcusYeri.query.filter_by(id=int(yer_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/admin')

    @app.route('/admin/ucus_ekle', methods = ['POST'])
    @roles_required('Admin')
    def admin_ucus_ekle():
        if request.method == 'POST':
            nereden = request.form['nereden']
            nereye = request.form['nereye']
            saat = request.form['saat']
            fiyat = float(request.form['fiyat'])
            existing_ucus = Ucuslar.query.filter_by(departure=nereden, arrival=nereye, time=saat).first()
            if existing_ucus is None:
                ucus = Ucuslar(
                    departure = nereden,
                    arrival = nereye,
                    time = saat,
                    price = fiyat
                )
                db.session.add(ucus)
                db.session.commit()
                return redirect('/admin?ucus=basarili')
            else :
                ucus_guncelle = existing_ucus
                ucus_guncelle.price = fiyat
                db.session.commit()
                return redirect('/admin?ucus=guncelleme')
        return redirect('/admin')

    @app.route('/admin/bonus_sil/<bonus_id>')
    @roles_required('Admin')
    def admin_bonus_sil(bonus_id):
        sil = Bonus.query.filter_by(id=int(bonus_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/admin/bonuslar')

    @app.route('/admin/rezervasyon_sil/<rez_id>')
    @roles_required('Admin')
    def admin_rezervasyon_sil(rez_id):
        sil = KullaniciUcuslar.query.filter_by(id=int(rez_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/admin/rezervasyonlar')

    @app.route('/admin/ucus_sil/<ucus_id>')
    @roles_required('Admin')
    def admin_ucus_sil(ucus_id):
        sil = Ucuslar.query.filter_by(id=int(ucus_id)).first()
        db.session.delete(sil)
        db.session.commit()
        return redirect('/admin')

    return app

if __name__ == '__main__':
    app = fly_app()
    app.run(port=8040, debug=True)
