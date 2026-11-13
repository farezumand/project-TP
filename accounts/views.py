import re

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


User = get_user_model()


def normalize_phone(value):
    """تبدیل ارقام فارسی/عربی به انگلیسی و اعتبارسنجی شماره موبایل ایران."""
    translation = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
    phone = (value or '').translate(translation)
    phone = re.sub(r'\D', '', phone)
    if len(phone) == 10 and phone.startswith('9'):
        phone = '0' + phone
    if not re.fullmatch(r'09\d{9}', phone):
        raise ValidationError('شماره موبایل باید به شکل ۰۹۱۲۳۴۵۶۷۸۹ وارد شود.')
    return phone


def login_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')

        try:
            phone = normalize_phone(request.POST.get('phone'))
        except ValidationError as error:
            messages.error(request, error.messages[0])
            return render(request, 'accounts/login.html')

        password = request.POST.get('password', '')

        if action == 'register':
            full_name = (request.POST.get('full_name') or '').strip()
            if len(full_name) < 2:
                messages.error(
                    request, 'لطفاً نام و نام خانوادگی خود را وارد کنید.')
                return render(request, 'accounts/login.html')
            if len(password) < 8:
                messages.error(request, 'رمز عبور باید حداقل ۸ کاراکتر باشد.')
                return render(request, 'accounts/login.html')
            if User.objects.filter(username=phone).exists():
                messages.error(
                    request, 'با این شماره موبایل قبلاً حساب کاربری ساخته شده است.')
                return render(request, 'accounts/login.html')

            user = User(username=phone, first_name=full_name)
            try:
                validate_password(password, user=user)
            except ValidationError as error:
                for message in error.messages:
                    messages.error(request, message)
                return render(request, 'accounts/login.html')

            user.set_password(password)
            user.save()
            login(request, user)
            messages.success(request, 'حساب کاربری شما با موفقیت ساخته شد.')
            return redirect('dashboard')

        if action == 'login':
            user = authenticate(request, username=phone, password=password)
            if user is None:
                messages.error(request, 'شماره موبایل یا رمز عبور صحیح نیست.')
                return render(request, 'accounts/login.html')

            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect('dashboard')

        messages.error(request, 'درخواست نامعتبر است. دوباره تلاش کنید.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required(login_url='login')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')
