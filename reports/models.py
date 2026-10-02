# from inventory.models import Product

# def get_low_stock_report(company_id):
#     """
#     Fetches all products for a specific company where stock is below 5.
#     """
#     return Product.objects.filter(company_id=company_id, stock__lt=5)