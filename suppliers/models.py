# from django.db import models
# from companies.models import TenantAwareModel

# class Supplier(TenantAwareModel):
#     name = models.CharField(max_length=255)
#     email = models.EmailField()
#     phone = models.CharField(max_length=20)
#     is_active = models.BooleanField(default=True)
    
#     def __str__(self):
#         return self.name