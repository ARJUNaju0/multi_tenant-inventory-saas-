# from rest_framework import viewsets
# from accounts.permissions import IsManagerOrAdmin, IsCompanyMember
# from .models import Product, StockMovement

# class ProductViewSet(viewsets.ModelViewSet):
#     """
#     CRITERIA: 
#     - Manager (and Admin): Manage products (Create, Update, Delete)
#     - Staff: Read products only (List, Retrieve)
#     """
#     def get_permissions(self):
#         if self.action in ['create', 'update', 'partial_update', 'destroy']:
#             permission_classes = [IsManagerOrAdmin]
#         else:
#             permission_classes = [IsCompanyMember] # Allows Staff to GET
#         return [permission() for permission in permission_classes]

# class StockMovementViewSet(viewsets.ModelViewSet):
#     """
#     CRITERIA: 
#     - Staff (and everyone): Record stock in/out (Create)
#     - Manager (and Admin): Manage stock movements (Update, Delete)
#     """
#     def get_permissions(self):
#         if self.action == 'create':
#             # Staff can record stock
#             permission_classes = [IsCompanyMember] 
#         elif self.action in ['update', 'partial_update', 'destroy']:
#             # Only Managers/Admins can alter historical records
#             permission_classes = [IsManagerOrAdmin]
#         else:
#             # Everyone can view their own stock movements
#             permission_classes = [IsCompanyMember]
            
#         return [permission() for permission in permission_classes]