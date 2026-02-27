from database.models import Material, Transaction, ProductInward, MRS, Invoice, db
from peewee import fn
import datetime

class AnalyticsService:
    @staticmethod
    def get_inventory_health():
        all_materials = Material.select()
        low_stock = [m for m in all_materials if m.quantity <= m.min_stock]
        dead_stock = [m for m in all_materials if m.quantity == 0]
        
        return {
            'all_materials': list(all_materials),
            'low_stock': low_stock,
            'dead_stock': dead_stock
        }

    @staticmethod
    def get_cost_trends():
        # Sum of inward transactions per month
        inwards = (Transaction
                   .select(Transaction.timestamp, Transaction.quantity, Material.unit_cost)
                   .join(Material)
                   .where(Transaction.type == 'INWARD'))
        
        trends = {}
        for tx in inwards:
            month = tx.timestamp.strftime("%Y-%m")
            cost = tx.quantity * tx.material.unit_cost
            trends[month] = trends.get(month, 0) + cost
            
        return [{'date': k, 'cost': v} for k, v in sorted(trends.items())]

    @staticmethod
    def get_sales_performance():
        # 1. Monthly Revenue Trend
        invoices = Invoice.select(Invoice.created_at, Invoice.grand_total)
        trends = {}
        for inv in invoices:
            month = inv.created_at.strftime("%Y-%m")
            trends[month] = trends.get(month, 0) + inv.grand_total
            
        # 2. Revenue by Consumer
        consumer_sales = (Invoice
                         .select(Invoice.client_name, fn.SUM(Invoice.grand_total).alias('total'))
                         .group_by(Invoice.client_name)
                         .order_by(fn.SUM(Invoice.grand_total).desc()))
        
        return {
            'trends': [{'date': k, 'revenue': v} for k, v in sorted(trends.items())],
            'consumers': [{'name': i.client_name or "Unknown", 'value': float(i.total)} for i in consumer_sales]
        }

    @staticmethod
    def get_material_insights():
        # Top 5 Materials by Consumption (Issues)
        top_materials = (Transaction
                        .select(Material.name, fn.SUM(fn.ABS(Transaction.quantity)).alias('total'))
                        .join(Material)
                        .where(Transaction.type == 'ISSUE')
                        .group_by(Material.name)
                        .order_by(fn.SUM(fn.ABS(Transaction.quantity)).desc())
                        .limit(5))
        
        return [{'name': m.material.name, 'value': m.total} for m in top_materials]

    @staticmethod
    def get_invoice_stats():
        stats = (Invoice
                .select(Invoice.status, fn.COUNT(Invoice.id).alias('count'))
                .group_by(Invoice.status))
        
        return [{'name': s.status, 'value': s.count} for s in stats]

    @staticmethod
    def get_forecast():
        # Simple forecast: Avg daily consumption over last 30 days
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        issues = (Transaction
                  .select(Transaction.material, fn.SUM(Transaction.quantity).alias('total'))
                  .where(Transaction.type == 'ISSUE', Transaction.timestamp >= thirty_days_ago)
                  .group_by(Transaction.material))
        
        consumption = {tx.material_id: abs(tx.total) / 30 for tx in issues}
        
        results = []
        for m in Material.select():
            avg_daily = consumption.get(m.id, 0)
            days_left = m.quantity / avg_daily if avg_daily > 0 else 999
            
            results.append({
                'name': m.name,
                'current_stock': m.quantity,
                'avg_daily': round(avg_daily, 2),
                'forecast_7_days': round(avg_daily * 7, 2),
                'suggested_reorder': max(0, (m.min_stock * 2) - m.quantity),
                'status': 'REORDER_NOW' if days_left < 7 else 'SUFFICIENT'
            })
        return results
