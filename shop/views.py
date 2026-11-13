from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render

from .models import Product, Category, Brand


def product_list(request):
    products = (
        Product.objects
        .filter(is_active=True)
        .select_related('category', 'brand')
    )

    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    stock = request.GET.get('stock')
    selected_sort = request.GET.get('sort', 'newest')

    if category_slug:
        products = products.filter(category__slug=category_slug)

    if brand_slug:
        products = products.filter(brand__slug=brand_slug)

    if min_price:
        try:
            products = products.filter(price__gte=int(min_price))
        except (TypeError, ValueError):
            min_price = ''

    if max_price:
        try:
            products = products.filter(price__lte=int(max_price))
        except (TypeError, ValueError):
            max_price = ''

    if stock == 'available':
        products = products.filter(stock__gt=0)
    elif stock == 'unavailable':
        products = products.filter(stock=0)

    if selected_sort == 'price_asc':
        products = products.order_by('price', '-created_at')
    elif selected_sort == 'price_desc':
        products = products.order_by('-price', '-created_at')
    else:
        selected_sort = 'newest'
        products = products.order_by('-created_at')

    categories = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    brands = Brand.objects.filter(is_active=True).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'brands': brands,
        'selected_category': category_slug,
        'selected_brand': brand_slug,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'selected_stock': stock or '',
        'selected_sort': selected_sort,
    }

    return render(request, 'shop/shop.html', context)
