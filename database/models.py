from sqlalchemy.orm import relationship
from sqlalchemy import String, Column, ForeignKey, Boolean

from .db import Base

class EmployeeNumber(Base):
    __tablename__ = "employee_mtsnumbers"

    employee_id = Column(String(length=50), ForeignKey("employees.tg_user_id", ondelete="CASCADE"), primary_key=True)
    phone = Column(String(11), ForeignKey("mts_numbers.phone", ondelete="CASCADE"), primary_key=True)

    employee = relationship("Employee", back_populates="mts_links")
    mts_number = relationship("MTSNumber", back_populates="employee_links")

class Employee(Base):
    __tablename__ = "employees"

    tg_user_id = Column(String(length=50), primary_key=True)
    full_name = Column(String(length=255), nullable=False)
    role = Column(String(length=50), default="manager", nullable=False)
    status = Column(String(length=50), default="works", nullable=False)

    # Галочки: сообщения каких площадок сотрудник получает (глобально, по всем номерам)
    # Галочка ozon заодно даёт доступ к «Получить код OZON»
    wb = Column(Boolean, default=False, nullable=False)
    ozon = Column(Boolean, default=False, nullable=False)
    yandex = Column(Boolean, default=False, nullable=False)
    mvideo = Column(Boolean, default=False, nullable=False)

    mts_links = relationship("EmployeeNumber", back_populates="employee", cascade="all, delete-orphan", passive_deletes=True)
    numbers = relationship("MTSNumber", secondary="employee_mtsnumbers", viewonly=True)


class MTSNumber(Base):
    __tablename__ = "mts_numbers"

    phone = Column(String(length=11), primary_key=True)
    status = Column(String(length=50), default="enabled", nullable=False)

    employee_links = relationship("EmployeeNumber", back_populates="mts_number", cascade="all, delete-orphan", passive_deletes=True)
    employees = relationship("Employee", secondary="employee_mtsnumbers", viewonly=True)


class Connect(Base):
    """
    Существующая таблица connects — настройки подключения магазинов.
    Здесь используется только для получения токена (пароля приложения Яндекс)
    по адресу почты магазина, чтобы забрать код подтверждения по IMAP.
    """
    __tablename__ = "connects"

    phone = Column(String(length=255), primary_key=True)
    proxy = Column(String(length=255), nullable=False)
    mail = Column(String(length=255), nullable=False)
    token = Column(String(length=255), nullable=False)
    pass_mail = Column(String(length=255), nullable=True)
