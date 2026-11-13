from django.db import models


class BlogCategory(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام دسته‌بندی")
    slug = models.SlugField(max_length=180, unique=True, verbose_name="شناسه انگلیسی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "دسته‌بندی وبلاگ"
        verbose_name_plural = "دسته‌بندی‌های وبلاگ"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Post(models.Model):
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        verbose_name="دسته‌بندی",
    )
    title = models.CharField(max_length=250, verbose_name="عنوان مقاله")
    slug = models.SlugField(max_length=280, unique=True, verbose_name="شناسه انگلیسی")
    excerpt = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="چکیده (نمایش در لیست مقالات)",
    )
    content = models.TextField(verbose_name="متن کامل مقاله")
    image = models.ImageField(
        upload_to="blog/",
        blank=True,
        null=True,
        verbose_name="تصویر شاخص",
    )
    reading_time = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="زمان مطالعه (دقیقه)",
    )
    views = models.PositiveIntegerField(default=0, verbose_name="بازدیدها")
    is_featured = models.BooleanField(
        default=False,
        verbose_name="مقاله ویژه (بالای صفحه)",
    )
    is_active = models.BooleanField(default=True, verbose_name="منتشر شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ انتشار")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
