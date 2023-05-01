from django.urls import path
from . import views

urlpatterns = [
    path('groups', views.GroupView.as_view()),
    path('register/', views.RegisterUser.as_view()),
    path('menu-items/', views.MenuItemView.as_view()),
    path("menu-items/<int:pk>", views.SingleMenuItemView.as_view()),
    path('cart/menu-items', views.CartView.as_view()),
    path("cart/menu-items/<int:pk>", views.CartView.as_view()),
    path("cart/orders", views.OrderView.as_view()),
    path('groups/manager/users/', views.manager),
    path('groups/delivery-crew/users/', views.DeliveryCrewView.as_view()),
    path("groups/delivery-crew/users/<int:pk>", views.DeliveryCrewView.as_view()),
    path("orders", views.AssignOrder.as_view()),
    path("order/delivered", views.UpdateDeliveryStatus.as_view())
    #path('orders/<int:pk>', views.OrderItemView.as_view())
]