from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db import IntegrityError, models
from django.db.models import Avg
from .models import Customer, Restaurant, Review, MenuItem, Order, OrderItem
from django.contrib.auth import logout as auth_logout
from decimal import Decimal
from django.http import JsonResponse
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import time

# Create your views here.
def index(request):
    print("Index page loaded")
    return render(request, 'index.html')

def open_login(request):
    # Clear any existing messages when opening the login page
    storage = messages.get_messages(request)
    for message in storage:
        # Iterate through messages to mark them as read
        pass  # This effectively clears the messages
    storage.used = True
    
    return render(request, 'login.html')

def open_signup(request):
    return render(request,'sign-up.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        mobile = request.POST['mobile']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        address = request.POST['address']
        userType = request.POST['userType']
        
        if password1 != password2:
            response = HttpResponse("<h1 style='color:red'>Password Mismatch</h1>")
            response['Refresh'] = '5;url=/signup/'  # Updated URL
            return response
        
        # Use filter().exists() instead of get() to check if username exists
        if Customer.objects.filter(username=username).exists():
            res = HttpResponse("<h1 style='color:red'>Username already exists. Please try to login.</h1>")
            res['Refresh'] = '2;url=/open_login/'  # Updated URL
            return res
        else:
            # Create new customer
            Customer.objects.create(
                username=username,
                password=password1,
                email=email,
                phone=mobile,
                address=address,
                userType=userType
            )
            # Set session to log in the user
            request.session['username'] = username
            messages.success(request, "Account created successfully! You are now logged in.")
            return redirect('customer_home')
    else:
        print("Sigup - failed")
        return render(request, 'sign-up.html')
    
def signin(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        try:
            customer = Customer.objects.get(username=username, password=password)
            # Store username in session
            request.session['username'] = username
            
            if  customer.userType == "admin":
                return render(request, 'admin/AdminHome.html')
            else:
                hotels = Restaurant.objects.all()
                return render(request, 'customerHome.html', {'rows': hotels})
        except Customer.DoesNotExist:
            res = HttpResponse("<h1 style='color:red; text-align:center'>Username or Password Mismatch.</h1>")
            res['Refresh'] = '2;url=/'  # Updated URL
            return res
    else:
        # Handle GET request - show the login page
        hotels = Restaurant.objects.all()
        return render(request, 'customerHome.html', {'rows': hotels})

def open_add_restaurant(request):
    return render(request,'add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        try:
            # Get data from the form
            name = request.POST['name']
            image_url = request.POST['image_url']
            phone = request.POST['phone']
            cuisine = request.POST['cuisine']
            opening_hours = request.POST['opening_hours']
            rating = request.POST['rating']

            # Create new restaurant
            restaurant = Restaurant.objects.create(
                name=name,
                image_url=image_url,
                phone=phone,
                cuisine=cuisine,
                opening_hours=opening_hours,
                rating=rating
            )
            
            messages.success(request, 'Restaurant added successfully!')
            return redirect('admin_restaurants')
            
        except Exception as e:
            messages.error(request, f'Error adding restaurant: {str(e)}')
            return redirect('open_add_restaurant')
    
    return render(request, 'add_restaurant.html')



def showRestaurants(request):
    restaurants = Restaurant.objects.all()
    
    # Get the username from the session
    userName = request.session.get('username')

    # Default to not admin if no user is logged in or user type cannot be determined
    is_admin = False 
    
    if userName:
        try:
            current_user = Customer.objects.get(username=userName)
            if current_user.userType == "admin":
                is_admin = True
        except Customer.DoesNotExist:
            # If username is in session but doesn't exist, treat as not logged in or not admin
            pass 
    
    if is_admin:
        return render(request, 'ShowRestaurants.html', {'restaurants': restaurants})
    else:
        # For regular customers or unauthenticated users, show the customer version
        return render(request, 'customer_restaurants.html', {'restaurants': restaurants})



def update_restaurant(request, restaurant_id):
    userName = request.session.get('username')
    if not userName:
        messages.error(request, "Please log in to perform this action.")
        return redirect('open_login') # Redirect to your login URL

    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to update restaurants.")
            return redirect('index') # Redirect to a non-admin page
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        try:
            restaurant.name = request.POST['name']
            restaurant.image_url = request.POST['image_url']
            restaurant.phone = request.POST['phone']
            restaurant.cuisine = request.POST['cuisine']
            restaurant.opening_hours = request.POST['opening_hours']
            
            try:
                restaurant.rating = float(request.POST['rating'])
            except ValueError:
                messages.error(request, 'Rating must be a valid number.')
                return render(request, 'update_restaurant.html', {'restaurant': restaurant})


            restaurant.save()
            messages.success(request, 'Restaurant updated successfully!')

            return redirect('admin_restaurants')
            
        except Exception as e:
            messages.error(request, f'Error updating restaurant: {str(e)}')

            return render(request, 'update_restaurant.html', {'restaurant': restaurant})

    return render(request, 'update_restaurant.html', {'restaurant': restaurant})



def view_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
    reviews = Review.objects.filter(restaurant=restaurant).select_related('customer').order_by('-created_at')
    
    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
        'reviews': reviews,
    }
    return render(request, 'menu.html', context)

def submit_review(request, restaurant_id):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            customer = Customer.objects.get(username=username)
            restaurant = get_object_or_404(Restaurant, id=restaurant_id)
            
            rating = int(request.POST.get('rating'))
            comment = request.POST.get('comment')

            # Create or update the review
            review, created = Review.objects.update_or_create(
                customer=customer,
                restaurant=restaurant,
                defaults={
                    'rating': rating,
                    'comment': comment
                }
            )

            # Update restaurant's average rating
            avg_rating = Review.objects.filter(restaurant=restaurant).aggregate(
                Avg('rating')
            )['rating__avg']
            
            restaurant.rating = round(avg_rating) if avg_rating else 5
            restaurant.save()

            messages.success(request, 'Thank you for your review!')
            
        except Customer.DoesNotExist:
            messages.error(request, 'Please log in to submit a review.')
        except IntegrityError:
            messages.error(request, 'You have already reviewed this restaurant.')
        except Exception as e:
            messages.error(request, f'Error submitting review: {str(e)}')
    
    # Redirect back to the restaurant menu page
    return redirect('view_menu', restaurant_id=restaurant_id)

def customer_home(request):
    hotels = Restaurant.objects.all()
    return render(request, 'customerHome.html', {'rows': hotels})




def delete_restaurant(request, restaurant_id):
    # Retrieve the username from the session
    userName = request.session.get('username')

    # 1. First, check if any user is logged in
    if not userName:
        messages.error(request, "Please log in to perform this action.")
        return redirect('open_login') # Redirect to your login URL

    # 2. Verify if the logged-in user is an admin
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to delete restaurants.")
            return redirect('index') # Redirect to a non-admin page
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    # If the code reaches here, the user is an authenticated admin.

    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == "POST":
        restaurant.delete()
        messages.success(request, f'Restaurant "{restaurant.name}" deleted successfully!')
        return redirect('admin_restaurants') # Always redirect to admin_restaurants after admin action
    else:
        # Since only admins can reach this point, always use the admin-specific template
        return render(request, 'admin/delete_restaurant_confirm.html', {'restaurant': restaurant})


def addMeuItem(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    
    if request.method == 'POST':
        try:
            # Get data from the form
            name = request.POST['name']
            description = request.POST['description']
            price = request.POST['price']
            category = request.POST['category']
            image_url = request.POST['image_url']
            is_veg = 'is_veg' in request.POST
            is_available = 'is_available' in request.POST

            # Create new menu item
            menu_item = MenuItem.objects.create(
                restaurant=restaurant,
                name=name,
                description=description,
                price=price,
                category=category,
                image_url=image_url,
                is_veg=is_veg,
                is_available=is_available
            )
            
            messages.success(request, f'Menu item "{name}" added successfully!')
            # Redirect to manage_menu instead of admin_home to display the message
            return redirect('manage_menu', restaurant_id=restaurant.id)
            
        except Exception as e:
            messages.error(request, f'Error adding menu item: {str(e)}')
            return render(request, 'add_menu_item.html', {'restaurant_id': restaurant_id})
    
    return render(request, 'add_menu_item.html', {'restaurant_id': restaurant_id})

def manage_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=restaurant).order_by('category', 'name')
    
    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
    }
    return render(request, 'manage_menu.html', context)

def update_menu_item(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    restaurant = menu_item.restaurant
    
    if request.method == 'POST':
        try:
            # Get data from the form
            menu_item.name = request.POST['name']
            menu_item.description = request.POST['description']
            menu_item.price = request.POST['price']
            menu_item.category = request.POST['category']
            menu_item.image_url = request.POST['image_url']
            menu_item.is_veg = 'is_veg' in request.POST
            menu_item.is_available = 'is_available' in request.POST
            
            # Save the updated menu item
            menu_item.save()
            
            messages.success(request, f'Menu item "{menu_item.name}" updated successfully!')
            return redirect('manage_menu', restaurant_id=restaurant.id)
            
        except Exception as e:
            messages.error(request, f'Error updating menu item: {str(e)}')
    
    context = {
        'menu_item': menu_item,
        'restaurant_id': restaurant.id,
    }
    return render(request, 'update_menu_item.html', context)

def delete_menu_item(request, item_id):
    menu_item = get_object_or_404(MenuItem, id=item_id)
    restaurant_id = menu_item.restaurant.id
    
    if request.method == 'POST':
        menu_item_name = menu_item.name
        menu_item.delete()
        messages.success(request, f'Menu item "{menu_item_name}" deleted successfully!')
        return redirect('manage_menu', restaurant_id=restaurant_id)
    
    context = {
        'menu_item': menu_item,
    }
    return render(request, 'delete_menu_item_confirm.html', context)

def logout(request):
    """
    Log out the user and redirect to the login page with a success message.
    """
    # Clear the username from session
    if 'username' in request.session:
        del request.session['username']
    
    # Flush the session to clear all session data
    request.session.flush()
    
    # Redirect to the login page with the correct URL name
    return redirect('open_login')  # Changed from 'open_login' to 'login'

def search_restaurants(request):
    query = request.GET.get('query', '')
    
    if query:
        # Search in restaurant names and cuisines
        restaurants = Restaurant.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(cuisine__icontains=query)
        ).distinct()
        
        # Search for menu items
        menu_items = MenuItem.objects.filter(
            models.Q(name__icontains=query) |
            models.Q(description__icontains=query)
        ).select_related('restaurant').distinct()
        
        # Get restaurants that have matching menu items
        restaurants_with_items = Restaurant.objects.filter(
            menu_items__in=menu_items
        ).distinct()
        
        # Combine both querysets
        all_restaurants = (restaurants | restaurants_with_items).distinct()
    else:
        all_restaurants = Restaurant.objects.all()
        menu_items = MenuItem.objects.none()
    
    context = {
        'restaurants': all_restaurants,
        'menu_items': menu_items,
        'query': query,
        'search_performed': bool(query)
    }
    
    return render(request, 'search_results.html', context)

def add_to_cart(request, menu_item_id):
    # Check if user is logged in
    if 'username' not in request.session:
        messages.error(request, "Please login to add items to cart")
        return redirect('open_login')
    
    if request.method == 'POST':
        try:
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)
            quantity = int(request.POST.get('quantity', 1))
            
            # Initialize cart if it doesn't exist
            if 'cart' not in request.session:
                request.session['cart'] = {'restaurant_id': menu_item.restaurant.id, 'items': {}}
            
            cart = request.session['cart']
            
            # Check if item is from the same restaurant
            if 'restaurant_id' in cart and cart['restaurant_id'] != menu_item.restaurant.id:
                messages.warning(request, "Your cart contains items from a different restaurant. Clear cart first.")
                return redirect('view_cart')
            
            # Add restaurant ID if not already set
            if 'restaurant_id' not in cart:
                cart['restaurant_id'] = menu_item.restaurant.id
            
            # Initialize items dict if it doesn't exist
            if 'items' not in cart:
                cart['items'] = {}
            
            # Add or update item in cart
            item_key = str(menu_item_id)
            if item_key in cart['items']:
                cart['items'][item_key]['quantity'] += quantity
            else:
                cart['items'][item_key] = {
                    'name': menu_item.name,
                    'price': str(menu_item.price),
                    'quantity': quantity,
                    'image_url': menu_item.image_url
                }
            
            # Save updated cart to session
            request.session['cart'] = cart
            request.session.modified = True
            
            messages.success(request, f"{menu_item.name} added to your cart.")
            return redirect('view_menu', restaurant_id=menu_item.restaurant.id)
            
        except Exception as e:
            messages.error(request, f"Error adding to cart: {str(e)}")
            return redirect('view_menu', restaurant_id=menu_item.restaurant.id)
    
    return redirect('customer_home')

def view_cart(request):
    """View the current cart contents"""
    # Check if user is logged in
    if 'username' not in request.session:
        messages.error(request, "Please login to view your cart")
        return redirect('open_login')
    
    cart = request.session.get('cart', {})
    
    # Calculate total
    total = Decimal('0.00')
    items = []
    
    restaurant = None
    if 'restaurant_id' in cart:
        try:
            restaurant = Restaurant.objects.get(id=cart['restaurant_id'])
        except Restaurant.DoesNotExist:
            # If restaurant doesn't exist anymore, clear the cart
            if 'cart' in request.session:
                del request.session['cart']
                request.session.modified = True
            messages.error(request, "Restaurant no longer exists. Your cart has been cleared.")
            return redirect('customer_home')
    
    if 'items' in cart:
        for item_id, item_data in cart['items'].items():
            item_total = Decimal(item_data['price']) * item_data['quantity']
            total += item_total
            items.append({
                'id': item_id,
                'name': item_data['name'],
                'price': item_data['price'],
                'quantity': item_data['quantity'],
                'image_url': item_data.get('image_url', ''),  # Use get() to handle missing keys
                'total': item_total
            })
    
    # Calculate delivery fee and tax
    delivery_fee = Decimal('40.00') if total > 0 else Decimal('0.00')  # Match the value in cart.html
    tax = total * Decimal('0.05')  # 5% tax to match cart.html
    
    # Calculate final total
    final_total = total + delivery_fee + tax
    
    context = {
        'items': items,
        'total': total,
        'delivery_fee': delivery_fee,
        'tax': tax,
        'final_total': final_total,
        'restaurant': restaurant
    }
    
    return render(request, 'cart.html', context)

def update_cart_item(request, item_id, action=None):
    """Update the quantity of an item in the cart"""
    if 'cart' not in request.session:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')
    
    cart = request.session['cart']
    
    if 'items' not in cart:
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')
    
    item_key = str(item_id)
    
    if item_key in cart['items']:
        # If action is provided directly (from URL), use it
        # Otherwise get it from POST data
        if action is None and request.method == 'POST':
            action = request.POST.get('action')
        
        if action == 'increase':
            cart['items'][item_key]['quantity'] += 1
        elif action == 'decrease':
            if cart['items'][item_key]['quantity'] > 1:
                cart['items'][item_key]['quantity'] -= 1
            else:
                del cart['items'][item_key]
        elif action == 'remove':
            del cart['items'][item_key]
        
        # If cart is empty except for restaurant_id, remove the cart
        if len(cart['items']) == 0:
            del request.session['cart']
        else:
            request.session['cart'] = cart
            
        request.session.modified = True
        messages.success(request, "Cart updated successfully.")
    
    return redirect('view_cart')

def clear_cart(request):
    """Clear all items from the cart"""
    # Check if user is logged in
    if 'username' not in request.session:
        messages.error(request, "Please login to manage your cart")
        return redirect('open_login')
    
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
        messages.success(request, "Your cart has been cleared.")
    
    return redirect('customer_home')

def force_clear_cart(request):
    """Force clear the cart (for debugging)"""
    if 'cart' in request.session:
        del request.session['cart']
        request.session.modified = True
        messages.success(request, "Cart has been forcefully cleared.")
    else:
        messages.info(request, "Cart was already empty.")
    
    return redirect('customer_home')

def checkout(request):
    """Process the checkout"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        # Check if cart is empty
        if not cart or 'restaurant_id' not in cart or 'items' not in cart or not cart['items']:
            messages.error(request, "Your cart is empty.")
            return redirect('view_cart')
        
        # Get customer
        username = request.session.get('username')
        if not username:
            messages.error(request, "Please log in to place an order.")
            return redirect('open_login')
        
        try:
            customer = Customer.objects.get(username=username)
            restaurant = Restaurant.objects.get(id=cart['restaurant_id'])
            
            # Calculate total
            total = Decimal('0.00')
            for item_id, item_data in cart['items'].items():
                total += Decimal(item_data['price']) * item_data['quantity']
            
            # Add delivery fee and tax
            delivery_fee = Decimal('2.99')
            tax = total * Decimal('0.08')  # 8% tax
            final_total = total + delivery_fee + tax
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                total_amount=final_total,
                delivery_address=request.POST.get('delivery_address', customer.address)
            )
            
            # Create order items
            for item_id, item_data in cart['items'].items():
                menu_item = MenuItem.objects.get(id=int(item_id))
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=Decimal(item_data['price'])
                )
            
            # Clear cart after successful order
            del request.session['cart']
            request.session.modified = True
            
            messages.success(request, f"Your order has been placed successfully! Order #{order.id}")
            return redirect('order_confirmation', order_id=order.id)
            
        except Customer.DoesNotExist:
            messages.error(request, "Customer account not found.")
            return redirect('open_login')
        except Exception as e:
            messages.error(request, f"Error placing order: {str(e)}")
            return redirect('view_cart')
    
    # GET request - show checkout form
    cart = request.session.get('cart', {})
    
    # Calculate total
    total = Decimal('0.00')
    items = []
    
    restaurant = None
    if 'restaurant_id' in cart:
        restaurant = get_object_or_404(Restaurant, id=cart['restaurant_id'])
    
    if 'items' in cart:
        for item_id, item_data in cart['items'].items():
            item_total = Decimal(item_data['price']) * item_data['quantity']
            total += item_total
            items.append({
                'id': item_id,
                'name': item_data['name'],
                'price': item_data['price'],
                'quantity': item_data['quantity'],
                'image_url': item_data.get('image_url', ''),  # Add image_url
                'total': item_total
            })
    
    # Calculate delivery fee and tax
    delivery_fee = Decimal('40.00') if total > 0 else Decimal('0.00')  # Match the value in checkout.html
    tax = total * Decimal('0.05')  # 5% tax to match checkout.html
    
    # Calculate final total
    final_total = total + delivery_fee + tax
    
    # Get customer address for pre-filling
    customer_address = ""
    username = request.session.get('username')
    if username:
        try:
            customer = Customer.objects.get(username=username)
            customer_address = customer.address
        except Customer.DoesNotExist:
            pass
    
    context = {
        'items': items,
        'total': total,
        'delivery_fee': delivery_fee,
        'tax': tax,
        'final_total': final_total,
        'restaurant': restaurant,
        'customer_address': customer_address
    }
    
    return render(request, 'checkout.html', context)

def order_confirmation(request, order_id):
    """Show order confirmation page"""
    try:
        order = get_object_or_404(Order, id=order_id)
        
        # Security check - only allow customer who placed the order to view it
        username = request.session.get('username')
        if not username or order.customer.username != username:
            messages.error(request, "You don't have permission to view this order.")
            return redirect('customer_home')
        
        # Get all order items
        order_items = order.items.all().select_related('menu_item')
        
        context = {
            'order': order,
            'items': order_items
        }
        
        return render(request, 'order_confirmation.html', context)
    except Exception as e:
        messages.error(request, f"Error displaying order: {str(e)}")
        return redirect('customer_home')

def my_orders(request):
    """Show all orders for the current customer"""
    # Check if user is logged in
    if 'username' not in request.session:
        messages.error(request, "Please login to view your orders")
        return redirect('_open_login')
    
    username = request.session.get('username')
    
    try:
        customer = Customer.objects.get(username=username)
        orders = Order.objects.filter(customer=customer).order_by('-created_at')
        
        context = {
            'orders': orders
        }
        
        return render(request, 'my_orders.html', context)
        
    except Customer.DoesNotExist:
        messages.error(request, "Customer account not found.")
        return redirect('open_login')

def admin_orders(request):
    """Display all orders for admin"""
    
    # Retrieve the username from the session
    userName = request.session.get('username')

    # 1. First, check if any user is logged in
    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login') # Redirect to your login URL

    # 2. Verify if the logged-in user is an admin
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index') # Redirect to a non-admin page
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    # If the code reaches here, the user is an authenticated admin.
    
    # Get all orders, newest first
    orders = Order.objects.all().order_by('-created_at')
    
    context = {
        'orders': orders
    }
    
    return render(request, 'admin/orders.html', context)


def admin_view_order(request, order_id):
    """Display details of a specific order for admin"""
    
    # Retrieve the username from the session
    userName = request.session.get('username')

    # 1. First, check if any user is logged in
    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('openlogin') # Redirect to your login URL

    # 2. Verify if the logged-in user is an admin
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index') # Redirect to a non-admin page
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('oppen_login')

    # If the code reaches here, the user is an authenticated admin.
    
    # Get the specific order and its items
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all() # Assuming 'items' is a related_name or ManyToMany field on Order

    context = {
        'order': order,
        'items': order_items
    }
    
    return render(request, 'admin/view_order.html', context)

def admin_customers(request):
    """Display all customers for admin"""
    
    # Retrieve the username from the session
    userName = request.session.get('username')

    # 1. First, check if any user is logged in
    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login')

    # 2. Verify if the logged-in user is an admin
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index')
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    # If the code reaches here, the user is an authenticated admin.
    
    # Get all customers, ordered by username
    customers = Customer.objects.all().order_by('username')
    
    context = {
        'customers': customers
    }
    
    return render(request, 'admin/customers.html', context)


def admin_view_customer(request, customer_id):
    """Display details of a specific customer for admin"""
    
    userName = request.session.get('username')

    # Ensure a user is logged in
    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login')

    # Verify the logged-in user has admin privileges
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index')
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    # Retrieve the specific customer and their orders
    customer = get_object_or_404(Customer, id=customer_id)
    customer_orders = Order.objects.filter(customer=customer).order_by('-created_at')
    
    context = {
        'customer': customer,
        'orders': customer_orders
    }
    
    return render(request, 'admin/view_customer.html', context)


def admin_settings(request):
    """Display and manage admin settings"""
    
    userName = request.session.get('username')

    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login') 
    # 2. Verify if the logged-in user is an admin
    try:
        current_user = Customer.objects.get(username=userName)
        if current_user.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index') # Redirect to a non-admin landing page
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')
    
    if request.method == 'POST':
 
        messages.success(request, "Settings updated successfully.")
      
        return redirect('admin_settings')
    
    context = {
     
    }
    
    return render(request, 'admin/settings.html', context)
   


def admin_restaurants(request):
    """Display all restaurants for admin management"""
    
    # Get the username from the session
    userName = request.session.get('username')

    # Basic check: Is there a user logged in?
    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login') # Redirect to your login URL

    # Verify if the logged-in user is an admin
    try:
        customer = Customer.objects.get(username=userName)
        if customer.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            return redirect('index') # Redirect to a non-admin page
            
    except Customer.DoesNotExist:
        # This handles cases where the username in the session doesn't exist in the DB
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    # If the code reaches here, the user is an authenticated admin.
    
    # Get all restaurants
    restaurants = Restaurant.objects.all().order_by('name')
    
    context = {
        'restaurants': restaurants
    }
    
    return render(request, 'admin/ShowRestaurants.html', context)




def admin_home(request):
    userName = request.session.get('username')

    if not userName:
        messages.error(request, "Please log in to access this page.")
        return redirect('open_login')

    try:
        customer = Customer.objects.get(username=userName)
        if customer.userType != "admin":
            messages.error(request, "You don't have permission to access this page.")
            print("Im gonna quit")
            return redirect('index')
            
    except Customer.DoesNotExist:
        messages.error(request, "Invalid user session. Please log in again.")
        return redirect('open_login')

    restaurant_count = Restaurant.objects.count()
    customer_count = Customer.objects.count()
    
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    recent_orders_count = Order.objects.count()
    
    recent_customers = Customer.objects.all().order_by('-id')[:5]
    
    context = {
        'restaurant_count': restaurant_count,
        'customer_count': customer_count,
        'recent_orders': recent_orders,
        'recent_orders_count': recent_orders_count,
        'recent_customers': recent_customers,
        'username':userName
    }
    
    return render(request, 'admin/AdminHome.html', context)

def update_order_status(request, order_id):
    """Update the status of an order"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        # Validate that the status is one of the allowed choices
        valid_statuses = [status[0] for status in Order.STATUS_CHOICES]
        if new_status in valid_statuses:
            order.status = new_status
            order.save()
            messages.success(request, f"Order #{order_id} status updated to {order.get_status_display()}")
        else:
            messages.error(request, "Invalid status value")
        
        # Redirect back to the order detail page
        return redirect('admin_view_order', order_id=order_id)
    
    # If not POST, redirect to the order list

def process_payment(request):
    """Process payment after confirming order"""
    if request.method == 'POST':
        # Get cart data from session
        cart = request.session.get('cart', {})
        
        # Check if cart is empty
        if not cart or 'items' not in cart or not cart['items']:
            messages.error(request, "Your cart is empty.")
            return redirect('view_cart')
        
        # Calculate total amount
        total = Decimal('0.00')
        for item_id, item_data in cart['items'].items():
            total += Decimal(item_data['price']) * item_data['quantity']
        
        # Add delivery fee and tax
        delivery_fee = Decimal('40.00')
        tax = total * Decimal('0.05')
        final_total = total + delivery_fee + tax
        
        # Convert to paise (Razorpay requires amount in smallest currency unit)
        amount_in_paise = int(final_total*100)
        
        # Get customer details
        username = request.session.get('username')
        if not username:
            messages.error(request, "Please log in to place an order.")
            return redirect('open_login')
        
        try:
            customer = Customer.objects.get(username=username)
            
            # Create Razorpay order
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'order_receipt_{username}_{int(time.time())}',
                'payment_capture': '1'  # Auto capture payment
            })
            
            # Store order details in session for verification after payment
            request.session['razorpay_order_id'] = razorpay_order['id']
            request.session['order_amount'] = amount_in_paise
            request.session['delivery_address'] = request.POST.get('delivery_address', customer.address)
            
            context = {
                'order_id': razorpay_order['id'],
                'order_amount': amount_in_paise/100,
                'currency': 'INR',
                'razorpay_key_id': settings.RAZORPAY_KEY_ID,
                'customer_name': customer.username,
                'customer_email': customer.email,
                'customer_phone': customer.phone,
                'callback_url': request.build_absolute_uri(reverse('payment_callback'))
            }
            
            return render(request, 'payment.html', context)
            
        except Customer.DoesNotExist:
            messages.error(request, "Customer account not found.")
            return redirect('open_login')
        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('view_cart')
    
    # If not POST, redirect to checkout
    return redirect('checkout')

@csrf_exempt
def payment_callback(request):
    """Handle the payment callback from Razorpay"""
    # Check both GET and POST for payment details
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id', '')
        order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
    else:
        payment_id = request.GET.get('razorpay_payment_id', '')
        order_id = request.GET.get('razorpay_order_id', '')
        signature = request.GET.get('razorpay_signature', '')
    
    if not payment_id or not order_id or not signature:
        messages.error(request, "Missing payment details")
        return redirect('checkout')
    
    try:
        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': order_id,
            'razorpay_signature': signature
        }
        
        # Verify the payment signature
        try:
            client.utility.verify_payment_signature(params_dict)
        except Exception as e:
            messages.error(request, f"Payment verification failed: {str(e)}")
            return redirect('checkout')
        
        # Get stored order details from session
        razorpay_order_id = request.session.get('razorpay_order_id')
        
        # Verify that the callback is for the same order
        if order_id != razorpay_order_id:
            messages.error(request, "Order ID mismatch. Payment verification failed.")
            return redirect('checkout')
        
        # Create order in database
        username = request.session.get('username')
        cart = request.session.get('cart', {})
        
        if not username or not cart:
            messages.error(request, "Session data missing. Please try again.")
            return redirect('checkout')
        
        try:
            customer = Customer.objects.get(username=username)
            restaurant = Restaurant.objects.get(id=cart['restaurant_id'])
            
            # Calculate total
            total = Decimal('0.00')
            for item_id, item_data in cart['items'].items():
                total += Decimal(item_data['price']) * item_data['quantity']
            
            delivery_fee = Decimal('40.00')
            tax = total * Decimal('0.05')
            final_total = total + delivery_fee + tax
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                total_amount=final_total,
                delivery_address=request.session.get('delivery_address', customer.address),
                payment_id=payment_id,
                payment_status='paid'
            )
            
            # Create order items
            for item_id, item_data in cart['items'].items():
                menu_item = MenuItem.objects.get(id=int(item_id))
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=Decimal(item_data['price'])
                )
            
            # Clear cart and payment data from session
            request.session['cart'] = {}
            request.session.pop('razorpay_order_id', None)
            request.session.pop('order_amount', None)
            request.session.pop('delivery_address', None)
            request.session.modified = True
            
            messages.success(request, f"Payment successful! Your order #{order.id} has been placed.")
            return redirect('order_confirmation', order_id=order.id)
            
        except Customer.DoesNotExist:
            messages.error(request, "Customer account not found.")
            return redirect('checkout')
        except Exception as e:
            messages.error(request, f"Error creating order: {str(e)}")
            return redirect('checkout')
            
    except Exception as e:
        messages.error(request, f"Error processing payment: {str(e)}")
    return render(request, 'debug_payment.html')

def check_cart(request):
    """Check the current cart contents (for debugging)"""
    cart = request.session.get('cart', {})
    
    context = {
        'cart': cart,
        'session_data': {
            'razorpay_order_id': request.session.get('razorpay_order_id'),
            'order_amount': request.session.get('order_amount'),
            'delivery_address': request.session.get('delivery_address'),
            'username': request.session.get('username'),
        }
    }
    
    return render(request, 'debug_cart.html', context)

def create_order(request):
    """Create a new order from cart items"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        # Check if cart is empty
        if not cart or 'restaurant_id' not in cart or 'items' not in cart or not cart['items']:
            messages.error(request, "Your cart is empty.")
            return redirect('view_cart')
        
        # Get customer
        username = request.session.get('username')
        if not username:
            messages.error(request, "Please log in to place an order.")
            return redirect('open_login')
        
        try:
            customer = Customer.objects.get(username=username)
            restaurant = Restaurant.objects.get(id=cart['restaurant_id'])
            
            # Calculate total
            total = Decimal('0.00')
            for item_id, item_data in cart['items'].items():
                total += Decimal(item_data['price']) * item_data['quantity']
            
            # Add delivery fee and tax
            delivery_fee = Decimal('40.00')
            tax = total * Decimal('0.05')
            final_total = total + delivery_fee + tax
            
            # Create order
            order = Order.objects.create(
                customer=customer,
                restaurant=restaurant,
                total_amount=final_total,
                delivery_address=request.POST.get('delivery_address', customer.address)
            )
            
            # Create order items
            for item_id, item_data in cart['items'].items():
                menu_item = MenuItem.objects.get(id=int(item_id))
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item_data['quantity'],
                    price=Decimal(item_data['price'])
                )
            
            # Clear cart after successful order
            request.session['cart'] = {}
            request.session.modified = True
            
            messages.success(request, f"Your order has been placed successfully! Order #{order.id}")
            return redirect('order_confirmation', order_id=order.id)
            
        except Customer.DoesNotExist:
            messages.error(request, "Customer account not found.")
            return redirect('open_login')
        except Exception as e:
            messages.error(request, f"Error placing order: {str(e)}")
            return redirect('view_cart')
    
    # If not POST, redirect to cart
    return redirect('view_cart')

def debug_payment(request):
    """Debug page for payment information"""
    # Get recent orders for debugging
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    recent_order_items = OrderItem.objects.filter(order__in=recent_orders).select_related('order', 'menu_item')
    
    # Get session data
    session_data = {
        'username': request.session.get('username'),
        'cart': request.session.get('cart'),
        'razorpay_order_id': request.session.get('razorpay_order_id'),
        'order_amount': request.session.get('order_amount'),
        'delivery_address': request.session.get('delivery_address'),
    }
    
    context = {
        'recent_orders': recent_orders,
        'recent_order_items': recent_order_items,
        'session_data': session_data
    }
    
    return render(request, 'debug_payment.html', context)
