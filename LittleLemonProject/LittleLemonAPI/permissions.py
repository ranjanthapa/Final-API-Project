from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.groups.filter(name='Manager').exists())


class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.groups.filter(name='Delivery').exists())


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and not request.user.groups.filter(name='Manager').exists() and not
        request.user.groups.filter(name='Delivery').exists())


class IsAuthorizedGetMethod(BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET" and request.user.is_authenticated:
            return True
        else:
            return False
