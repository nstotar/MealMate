from django.contrib import admin
from .models import Customer, Restaurant, Review,MenuItem

# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['username','email','phone','address','userType']
    search_fields = ['username','email','phone','address']
    list_filter = ['username','email','phone','address']
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ['id','name','image_url','phone','cuisine','opening_hours','rating']
    search_fields = ['name','image_url','phone','cuisine','opening_hours','rating']
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'restaurant', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['customer__username', 'restaurant__name', 'comment']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'is_veg', 'is_available']
    list_filter = ['category', 'is_veg', 'is_available']
    search_fields = ['name', 'description']
