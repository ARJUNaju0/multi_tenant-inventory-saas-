# from django.db import models
# from companies.models import TenantAwareModel
# from suppliers.models import Supplier

# class Product(TenantAwareModel):
#     name = models.CharField(max_length=255)
#     sku = models.CharField(max_length=50)
#     stock = models.IntegerField(default=0)
#     # supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
#     supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.SET_NULL, null=True, blank=True)


#  Product
# Category
#  Warehouse
#  StockLevel
# StockMovement