from datetime import date

from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.models import Customer, Product, Sale


def analytics(
    db: Session,
    business_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    product: str | None = None,
    category: str | None = None,
    customer: str | None = None,
) -> dict:
    conditions = [Sale.business_id == business_id]
    if start_date:
        conditions.append(Sale.sale_date >= start_date)
    if end_date:
        conditions.append(Sale.sale_date <= end_date)
    if product:
        conditions.append(Product.name == product)
    if category:
        conditions.append(Product.category == category)
    if customer:
        conditions.append(Customer.name == customer)

    def base(*columns):
        return (
            select(*columns)
            .select_from(Sale)
            .join(Product, Sale.product_id == Product.id)
            .outerjoin(Customer, Sale.customer_id == Customer.id)
            .where(*conditions)
        )

    revenue = Sale.quantity * Sale.unit_price
    total_cost = Sale.quantity * Sale.cost
    summary = db.execute(
        base(
            func.count(Sale.id),
            func.coalesce(func.sum(revenue), 0),
            func.coalesce(func.sum(Sale.quantity), 0),
            func.count(distinct(Sale.external_order_id)),
            func.sum(case((Sale.cost.is_(None), 1), else_=0)),
            func.coalesce(func.sum(total_cost), 0),
        )
    ).one()
    count, revenue_value, units, orders, missing_cost, cost_value = summary
    amount = float(revenue_value)
    profit = round(amount - float(cost_value), 2) if count and not missing_cost else None
    kpis = {
        "revenue": round(amount, 2),
        "gross_profit": profit,
        "profit_margin": round(profit / amount * 100, 2) if profit is not None and amount else None,
        "orders": orders,
        "units": float(units),
        "average_order_value": round(amount / orders, 2) if orders else 0,
        "cost_available": bool(count and not missing_cost),
    }

    trend_rows = db.execute(
        base(Sale.sale_date, func.sum(revenue), func.count(distinct(Sale.external_order_id)))
        .group_by(Sale.sale_date)
        .order_by(Sale.sale_date)
    ).all()
    product_rows = db.execute(
        base(Product.name, Product.category, func.sum(revenue), func.sum(Sale.quantity))
        .group_by(Product.name, Product.category)
        .order_by(func.sum(revenue).desc())
    ).all()
    category_rows = db.execute(
        base(Product.category, func.sum(revenue), func.sum(Sale.quantity))
        .group_by(Product.category)
        .order_by(func.sum(revenue).desc())
    ).all()
    customer_rows = db.execute(
        base(Customer.name, func.sum(revenue), func.count(distinct(Sale.external_order_id)))
        .where(Customer.id.is_not(None))
        .group_by(Customer.name)
        .order_by(func.sum(revenue).desc())
    ).all()
    recent_rows = db.execute(
        base(Sale.sale_date, Sale.external_order_id, Product.name, Customer.name, Sale.quantity, Sale.unit_price)
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
        .limit(10)
    ).all()
    return {
        "kpis": kpis,
        "trends": [
            {"date": str(day), "revenue": round(float(value), 2), "orders": orders} for day, value, orders in trend_rows
        ],
        "products": [
            {"name": name, "category": group, "revenue": round(float(value), 2), "units": float(qty)}
            for name, group, value, qty in product_rows
        ],
        "categories": [
            {"name": name, "revenue": round(float(value), 2), "units": float(qty)} for name, value, qty in category_rows
        ],
        "customers": [
            {
                "name": name,
                "spending": round(float(value), 2),
                "orders": orders,
                "average_spending": round(float(value) / orders, 2),
            }
            for name, value, orders in customer_rows
        ],
        "recent_sales": [
            {
                "date": str(day),
                "order_id": order,
                "product": name,
                "customer": buyer,
                "quantity": float(qty),
                "revenue": round(float(qty * price), 2),
            }
            for day, order, name, buyer, qty, price in recent_rows
        ],
    }


def filter_options(db: Session, business_id: int) -> dict:
    products = db.scalars(
        select(Product.name).distinct()
        .join(Sale, Sale.product_id == Product.id)
        .where(Sale.business_id == business_id)
        .order_by(Product.name)
    ).all()
    categories = db.scalars(
        select(Product.category).distinct()
        .join(Sale, Sale.product_id == Product.id)
        .where(Sale.business_id == business_id)
        .order_by(Product.category)
    ).all()
    customers = db.scalars(
        select(Customer.name).distinct()
        .join(Sale, Sale.customer_id == Customer.id)
        .where(Sale.business_id == business_id)
        .order_by(Customer.name)
    ).all()
    return {"products": products, "categories": categories, "customers": customers}
