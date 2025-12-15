from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from .config import Config

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False)
    product_id = Column(String, unique=True, nullable=False)
    name = Column(String)
    current_price = Column(Float)
    previous_price = Column(Float)
    last_check = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserProduct(Base):
    __tablename__ = 'user_products'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Database:
    def __init__(self):
        self.config = Config()
        self.engine = create_engine(self.config.DATABASE_URL)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_user(self, telegram_id, username):
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            self.session.add(user)
            self.session.commit()
        return user

    def add_product(self, url, product_id, name, price):
        product = self.session.query(Product).filter_by(product_id=product_id).first()
        if product:
            # Округляем цены
            product.previous_price = round(product.current_price, 2) if product.current_price else price
            product.current_price = round(price, 2)
            product.last_check = datetime.utcnow()
        else:
            product = Product(
                url=url,
                product_id=product_id,
                name=name,
                current_price=round(price, 2),
                previous_price=round(price, 2),
                last_check=datetime.utcnow()
            )
            self.session.add(product)
        self.session.commit()
        return product

    def update_product_price(self, product_id, new_price):
        """Обновляет цену товара с сохранением предыдущей цены"""
        product = self.session.query(Product).filter_by(id=product_id).first()
        if product:
            # Округляем цены
            product.previous_price = round(product.current_price, 2) if product.current_price else new_price
            product.current_price = round(new_price, 2)
            product.last_check = datetime.utcnow()
            self.session.commit()
            return True
        return False

    def add_user_product(self, user_id, product_id):
        if not self.session.query(UserProduct).filter_by(
                user_id=user_id, product_id=product_id
        ).first():
            user_product = UserProduct(user_id=user_id, product_id=product_id)
            self.session.add(user_product)
            self.session.commit()

    def get_user_products(self, user_id):
        return self.session.query(Product).join(
            UserProduct, Product.id == UserProduct.product_id
        ).filter(UserProduct.user_id == user_id).all()

    def get_all_tracked_products(self):
        return self.session.query(Product).all()

    def get_product_by_name(self, name):
        """Найти товар по имени"""
        return self.session.query(Product).filter(Product.name.like(f"%{name}%")).first()

    def create_test_price_change(self, product_id):
        """Создать искусственное изменение цены для теста"""
        product = self.session.query(Product).filter_by(id=product_id).first()
        if product and product.current_price > 0:
            # Устанавливаем предыдущую цену на 10% ниже
            product.previous_price = product.current_price * 0.9
            self.session.commit()
            return True
        return False