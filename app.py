from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pandas as pd  # Для работы с Excel
from io import BytesIO  # Для работы с байтовыми объектами
from flask import send_file  # Для скачивания файла

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orders.db'
app.config['SECRET_KEY'] = 'super-secret-key'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@app.route('/admin/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'admin':  # Только администратор может добавлять продукты
        flash('Только администратор может добавлять продукты.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        quantity = request.form.get('quantity')
        comment = request.form.get('comment')

        if name and price and quantity:
            price = float(price)
            quantity = int(quantity)
            product = Product(name=name, price=price, quantity=quantity, comment=comment)
            db.session.add(product)
            db.session.commit()
            flash('Продукт успешно добавлен.')
            return redirect(url_for('index'))
        else:
            flash('Пожалуйста, заполните все поля.')

    return render_template('add_product.html')


@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.role != 'admin':  # Только администратор может удалять продукты
        flash('Только администратор может удалять продукты.')
        return redirect(url_for('index'))

    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        flash(f'Продукт "{product.name}" был удален.')
    else:
        flash('Продукт не найден.')

    return redirect(url_for('index'))


# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(10), default='user')  # "user" или "admin"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)  # Количество товара на складе
    comment = db.Column(db.String(200))  # Описание или комментарий к товару


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Внешний ключ на пользователя
    user = db.relationship('User', backref='orders')  # Связь с пользователем
    status = db.Column(db.String(50), default='Ожидает подтверждения')  # Статус заказа
    address = db.Column(db.String(200), nullable=False)  # Адрес доставки
    items = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Функция для добавления товаров в базу данных
def create_products():
    if Product.query.count() == 0:
        product1 = Product(name="Телефон", price=30000, quantity=10, comment="Смартфон с 6,5-дюймовым экраном.")
        product2 = Product(name="Ноутбук", price=60000, quantity=5, comment="Мощный ноутбук с процессором i7.")
        product3 = Product(name="Часы", price=10000, quantity=15, comment="Умные часы с мониторингом здоровья.")
        product4 = Product(name="Наушники", price=5000, quantity=20, comment="Беспроводные наушники с шумоподавлением.")

        db.session.add_all([product1, product2, product3, product4])
        db.session.commit()


@app.route('/')
@login_required
def index():
    if current_user.role == 'admin':
        orders = Order.query.all()  # Админ видит все заказы
        products = Product.query.all()  # Админ видит все товары
        return render_template('admin_orders.html', orders=orders, products=products)
    else:
        orders = Order.query.filter_by(user_id=current_user.id).all()  # Пользователь видит свои заказы
        products = Product.query.all()
        return render_template('index.html', orders=orders, products=products)

@app.route('/export', methods=['GET', 'POST'])
@login_required
def export():
    if request.method == 'POST':
        selected_products = request.form.getlist('products')  # Получаем выбранные продукты

        # Формируем данные для выгрузки
        data = []
        for product_id in selected_products:
            product = Product.query.get(product_id)
            sold_items = OrderItem.query.filter_by(product_id=product.id).all()
            total_sold = sum(item.quantity for item in sold_items)
            data.append({'Product Name': product.name, 'Total Sold': total_sold})

        # Создаем DataFrame для выгрузки в Excel
        df = pd.DataFrame(data)

        # Генерация Excel файла в памяти
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Sales Report')

        output.seek(0)

        # Возвращаем файл для скачивания
        return send_file(output, as_attachment=True, download_name='sales_report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Отображаем страницу с выбором продуктов
    products = Product.query.all()
    return render_template('export.html', products=products)
# Добавление маршрута для отображения страницы заказа товара
@app.route('/order_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def order_product(product_id):
    product = Product.query.get(product_id)
    if request.method == 'POST':
        quantity = int(request.form.get('quantity'))
        address = request.form.get('address')

        # Проверяем, достаточно ли товара на складе
        if quantity > product.quantity:
            flash('Запрошенное количество больше, чем на складе!')
            return redirect(url_for('order_product', product_id=product.id))

        # Расчет итоговой цены
        total_price = product.price * quantity

        # Если пользователь нажал кнопку "Оформить заказ"
        if 'confirm_order' in request.form:
            # Уменьшаем количество товара на складе
            product.quantity -= quantity
            db.session.commit()

            # Создаем заказ
            new_order = Order(user_id=current_user.id, address=address)
            db.session.add(new_order)
            db.session.commit()

            # Добавляем товары в заказ
            order_item = OrderItem(order_id=new_order.id, product_id=product.id, product_name=product.name,
                                   quantity=quantity)
            db.session.add(order_item)
            db.session.commit()

            flash(f'Заказ на {quantity} шт. товара "{product.name}" успешно оформлен!')
            return redirect(url_for('index'))

        return render_template('order_product.html', product=product, quantity=quantity, total_price=total_price)

    return render_template('order_product.html', product=product)


# Маршрут для удаления продукта
#@app.route('/delete_product/<int:product_id>', methods=['POST'])
#@login_required
#def delete_product(product_id):
#    if current_user.role != 'admin':  # Только администратор может удалять продукты
#        flash('Только администратор может удалять продукты.')
#        return redirect(url_for('index'))
#
#    product = Product.query.get(product_id)
#    if product:
#        db.session.delete(product)
#        db.session.commit()
#        flash(f'Продукт "{product.name}" был удален.')
#    else:
#        flash('Продукт не найден.')
#
#    return redirect(url_for('index'))

@app.route('/admin/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    order = Order.query.get(order_id)
    order.status = 'Готовится к отправке'
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/admin/cancel_order/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    order = Order.query.get(order_id)
    order.status = 'Отклонено'
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')  # По умолчанию "user"
        user = User(username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


#@app.route('/add_product', methods=['GET', 'POST'])
#@login_required
#def add_product():
#    if current_user.role != 'admin':  # Только администратор может добавлять продукты
#        return redirect(url_for('index'))
#
#    error = None
#    if request.method == 'POST':
#        name = request.form.get('name')
#        price = request.form.get('price')
#        quantity = request.form.get('quantity')
#        comment = request.form.get('comment')
#
#        if price and quantity:
#            price = float(price)
#            quantity = int(quantity)
#            product = Product(name=name, price=price, quantity=quantity, comment=comment)
#            db.session.add(product)
#            db.session.commit()
#            return redirect(url_for('index'))
#        else:
#            error = 'Пожалуйста, введите цену и количество товара'
#    return render_template('add_product.html', error=error)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_products()  # Добавляем товары в базу данных при запуске
    app.run(debug=True)