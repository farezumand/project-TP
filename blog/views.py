from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import BlogCategory, Post


def post_list(request):
    posts = (
        Post.objects
        .filter(is_active=True)
        .select_related('category')
    )

    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(title__icontains=query)

    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    featured = posts.filter(is_featured=True).first()
    regular_posts = posts.exclude(pk=featured.pk) if featured else posts

    categories = BlogCategory.objects.filter(is_active=True)
    popular = Post.objects.filter(is_active=True).order_by('-views', '-created_at')[:5]

    context = {
        'featured': featured,
        'posts': regular_posts,
        'categories': categories,
        'popular_posts': popular,
        'selected_category': category_slug or '',
        'query': query,
    }
    return render(request, 'blog/weblog.html', context)


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related('category'),
        slug=slug,
        is_active=True,
    )
    # افزایش بازدید به‌صورت اتمی در دیتابیس
    Post.objects.filter(pk=post.pk).update(views=F('views') + 1)

    related_posts = (
        Post.objects
        .filter(is_active=True, category=post.category)
        .exclude(pk=post.pk)[:4]
    )
    popular = Post.objects.filter(is_active=True).order_by('-views', '-created_at')[:5]

    context = {
        'post': post,
        'related_posts': related_posts,
        'popular_posts': popular,
    }
    return render(request, 'blog/takweblog.html', context)
