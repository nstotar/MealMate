from django.urls import path
from . import views

urlpatterns = [
    # Basic pages
    path("", views.index, name='index'),
    
    # Authentication
    path("open_login/", views.open_login, name='open_login'),
    path("open_signup/", views.open_signup, name='open_signup'),
    path("signup/", views.signup, name='signup'),
    path("signin/", views.signin, name='process_signin'),
    path("logout/", views.logout, name='logout'),
    
    # Customer routes
    path("customer_home/", views.customer_home, name='customer_home'),
    path("search_restaurants/", views.search_restaurants, name='search_restaurants'),
    path("my_orders/", views.my_orders, name='my_orders'),
    
    # Restaurant management
    path("open_add_restaurant/", views.open_add_restaurant, name='open_add_restaurant'),
    path("add_restaurant/", views.add_restaurant, name='add_restaurant'),
    path("show_restaurants/", views.showRestaurants, name='show_restaurants'),
    path("update_restaurant/<int:restaurant_id>/", views.update_restaurant, name='update_restaurant'),
    path("delete_restaurant/<int:restaurant_id>/", views.delete_restaurant, name='delete_restaurant'),
    
    # Menu and reviews
    path("restaurant/<int:restaurant_id>/menu/", views.view_menu, name='view_menu'),
    path("restaurant/<int:restaurant_id>/review/", views.submit_review, name='submit_review'),
    path("restaurant/<int:restaurant_id>/add_menu_item/", views.addMeuItem, name='addMeuItem'),
    path("restaurant/<int:restaurant_id>/manage_menu/", views.manage_menu, name='manage_menu'),
    path("menu_item/<int:item_id>/update/", views.update_menu_item, name='update_menu_item'),
    path("menu_item/<int:item_id>/delete/", views.delete_menu_item, name='delete_menu_item'),
    
    # Cart functionality
    path("add_to_cart/<int:menu_item_id>/", views.add_to_cart, name='add_to_cart'),
    path("view_cart/", views.view_cart, name='view_cart'),
    path("update_cart_item/<int:item_id>/", views.update_cart_item, name='update_cart_item'),  # New pattern with only item_id
    path("update_cart_item/<int:item_id>/<str:action>/", views.update_cart_item, name='update_cart_item_with_action'),
    path("clear_cart/", views.clear_cart, name='clear_cart'),
    path("force_clear_cart/", views.force_clear_cart, name='force_clear_cart'),
    path("check_cart/", views.check_cart, name='check_cart'),
    
    # Order processing
    path("checkout/", views.checkout, name='checkout'),
    path("create_order/", views.create_order, name='create_order'),
    path("order_confirmation/<int:order_id>/", views.order_confirmation, name='order_confirmation'),
    path("update_order_status/<int:order_id>/", views.update_order_status, name='update_order_status'),
    
    # Payment processing
    path("process_payment/", views.process_payment, name='process_payment'),
    path("payment_callback/", views.payment_callback, name='payment_callback'),
    path("debug_payment/", views.debug_payment, name='debug_payment'),
    
    # Admin routes
    path("admin_home/", views.admin_home, name='admin_home'),
    path("admin_restaurants/", views.admin_restaurants, name='admin_restaurants'),
    path("admin_orders/", views.admin_orders, name='admin_orders'),
    path("admin_view_order/<int:order_id>/", views.admin_view_order, name='admin_view_order'),
    path("admin_customers/", views.admin_customers, name='admin_customers'),
    path("admin_view_customer/<int:customer_id>/", views.admin_view_customer, name='admin_view_customer'),
    path("admin_settings/", views.admin_settings, name='admin_settings'),
]
