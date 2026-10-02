# from rest_framework.permissions import BasePermission, SAFE_METHODS

# class CanEditProductObject(BasePermission):
    
#     def has_permission(self, request, view):
#         """
#         Stage 1: Endpoint access.
#         Only Admins and Managers are allowed inside the building.
#         """
#         if not (request.user and request.user.is_authenticated and request.auth):
#             return False
            
#         role = request.auth.get('role')
#         return role in ['Admin', 'Manager']

#     def has_object_permission(self, request, view, obj):
#         """
#         Stage 2: Object access.
#         Evaluated only for detail routes (e.g., /api/products/<id>/).
#         """
#         # 1. Allow read-only methods (GET, HEAD, OPTIONS) for everyone who passed Stage 1
#         if request.method in SAFE_METHODS:
#             return True
            
#         role = request.auth.get('role')

#         # 2. Admins have unconditional access to modify the object
#         if role == 'Admin':
#             return True
            
#         # 3. Managers can modify the object UNLESS it is locked
#         if role == 'Manager':
#             if getattr(obj, 'is_locked_by_admin', False):
#                 # Blocks the Manager and returns a 403 Forbidden
#                 return False 
            
#             # You can also restrict specific actions. For example, Managers can't delete:
#             if view.action == 'destroy':
#                 return False
                
#             return True

#         return False