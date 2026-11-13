
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(max_length=180, unique=True, verbose_name="شناسه انگلیسی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام برند")
    slug = models.SlugField(max_length=180, unique=True, verbose_name="شناسه انگلیسی")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "برند"
        verbose_name_plural = "برندها"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name="دسته‌بندی"
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="برند"
    )

    name = models.CharField(max_length=250, verbose_name="نام محصول")
    slug = models.SlugField(max_length=280, unique=True, verbose_name="شناسه انگلیسی")

    short_description = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="توضیح کوتاه"
    )
    description = models.TextField(blank=True, verbose_name="توضیحات کامل")

    price = models.PositiveBigIntegerField(
        default=0,
        verbose_name="قیمت به تومان"
    )

    stock = models.PositiveIntegerField(default=0, verbose_name="موجودی")

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True,
        verbose_name="تصویر اصلی"
    )

    is_active = models.BooleanField(default=True, verbose_name="نمایش در فروشگاه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
