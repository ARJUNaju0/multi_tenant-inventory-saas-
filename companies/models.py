import uuid
from django.db import models

class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class TenantModel(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE,related_name="%(app_label)s_%(class)s",)

    class Meta:
        abstract = True
