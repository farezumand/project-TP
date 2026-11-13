from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from shop.models import Product
from .models import Coupon, Order, OrderItem

CART_SESSION_KEY = 'cart'


def _get_cart(request):
    return request.session.get(CART_SESSION_KEY, {})


def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_list')
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = _get_cart(request)
    key = str(product.pk)
    current_qty = int(cart.get(key, 0))
    if product.stock <= current_qty:
        messages.warning(request, 'موجودی کافی از این کالا وجود ندارد.')
    else:
        cart[key] = current_qty + 1
        request.session[CART_SESSION_KEY] = cart
        request.session.modified = True
        messages.success(request, 'محصول به سبد خرید اضافه شد.')
    return redirect('product_list')


def cart_detail(request):
    cart = _get_cart(request)

    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        if action in ('increase', 'decrease', 'remove') and product_id:
            product = Product.objects.filter(pk=product_id, is_active=True).first()
            key = str(product_id)
            if action == 'remove' or product is None:
                cart.pop(key, None)
            elif action == 'increase':
                current_qty = int(cart.get(key, 0))
                if current_qty < product.stock:
                    cart[key] = current_qty + 1
                else:
                    messages.warning(request, 'بیشتر از موجودی انبار نمی‌توانید انتخاب کنید.')
            elif action == 'decrease':
                current_qty = int(cart.get(key, 0))
                if current_qty <= 1:
                    cart.pop(key, None)
                else:
                    cart[key] = current_qty - 1
            request.session[CART_SESSION_KEY] = cart
            request.session.modified = True
            return redirect('cart_detail')

        if action == 'apply_coupon':
            code = request.POST.get('coupon_code', '').strip().upper()
            coupon = Coupon.objects.filter(code__iexact=code, is_active=True).first()
            now = timezone.now()
            if coupon and (not coupon.valid_from or coupon.valid_from <= now) and (not coupon.valid_until or coupon.valid_until >= now):
                request.session['cart_coupon'] = coupon.code
                messages.success(request, 'کد تخفیف با موفقیت اعمال شد.')
            else:
                messages.error(request, 'کد تخفیف معتبر نیست یا مهلت آن تمام شده است.')
            return redirect('cart_detail')

        if action == 'remove_coupon':
            request.session.pop('cart_coupon', None)
            return redirect('cart_detail')

    products = Product.objects.filter(pk__in=cart.keys(), is_active=True).select_related('category', 'brand')
    cart_items = []
    subtotal = 0
    for product in products:
        quantity = int(cart.get(str(product.pk), 0))
        if quantity < 1:
            continue
        line_total = product.price * quantity
        subtotal += line_total
        cart_items.append({'product': product, 'quantity': quantity, 'line_total': line_total})

    coupon = None
    discount = 0
    coupon_code = request.session.get('cart_coupon', '')
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if coupon:
            now = timezone.now()
            if (coupon.valid_from and coupon.valid_from > now) or (coupon.valid_until and coupon.valid_until < now):
                coupon = None
        if coupon:
            discount = subtotal * coupon.discount_percent // 100
        else:
            request.session.pop('cart_coupon', None)

    context = {
        'cart_items': cart_items,
        'cart_count': sum(item['quantity'] for item in cart_items),
        'subtotal': subtotal,
        'discount': discount,
        'total': subtotal - discount,
        'coupon': coupon,
    }
    return render(request, 'cart/sabadkharid.html', context)


@transaction.atomic
def checkout(request):
    if request.method != 'POST':
        return redirect('cart_detail')

    selected_ids = request.POST.getlist('selected_items')
    cart = _get_cart(request)
    required_fields = ['customer_name', 'phone', 'city', 'address']
    if any(not request.POST.get(field, '').strip() for field in required_fields):
        messages.error(request, 'لطفاً همه اطلاعات ضروری مشتری را تکمیل کنید.')
        return redirect('cart_detail')
    if not selected_ids:
        messages.error(request, 'لطفاً حداقل یک کالا را برای سفارش انتخاب کنید.')
        return redirect('cart_detail')

    products = Product.objects.filter(pk__in=selected_ids, is_active=True)
    chosen = []
    subtotal = 0
    for product in products:
        quantity = int(cart.get(str(product.pk), 0))
        if quantity > 0:
            if quantity > product.stock:
                messages.error(request, f'موجودی «{product.name}» کافی نیست.')
                return redirect('cart_detail')
            chosen.append((product, quantity))
            subtotal += product.price * quantity

    if not chosen:
        messages.error(request, 'کالاهای انتخاب‌شده در سبد خرید موجود نیستند.')
        return redirect('cart_detail')

    coupon = None
    coupon_code = request.session.get('cart_coupon', '')
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        now = timezone.now()
        if coupon and ((coupon.valid_from and coupon.valid_from > now) or (coupon.valid_until and coupon.valid_until < now)):
            coupon = None
    discount = subtotal * coupon.discount_percent // 100 if coupon else 0
    order = Order.objects.create(
        customer_name=request.POST.get('customer_name', '').strip(),
        phone=request.POST.get('phone', '').strip(),
        city=request.POST.get('city', '').strip(),
        address=request.POST.get('address', '').strip(),
        postal_code=request.POST.get('postal_code', '').strip(),
        subtotal=subtotal,
        discount=discount,
        total=subtotal - discount,
        coupon_code=coupon.code if coupon else '',
    )
    # قفل ردیف محصولات در انبار و کسر موجودی (ضد ریس شرط در سفارش همزمان)
    locked_products = {
        p.pk: p
        for p in Product.objects.select_for_update().filter(
            pk__in=[product.pk for product, _ in chosen]
        )
    }
    for product, quantity in chosen:
        locked = locked_products[product.pk]
        if locked.stock < quantity:
            messages.error(request, f'موجودی «{locked.name}» همین لحظه تمام شد.')
            transaction.set_rollback(True)
            return redirect('cart_detail')
        locked.stock -= quantity
        locked.save(update_fields=['stock'])

    for product, quantity in chosen:
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            unit_price=product.price,
            quantity=quantity,
        )
        key = str(product.pk)
        cart.pop(key, None)

    request.session[CART_SESSION_KEY] = cart
    request.session.pop('cart_coupon', None)
    request.session.modified = True
    return render(request, 'cart/order_success.html', {'order': order})
