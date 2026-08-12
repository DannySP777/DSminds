from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import FeedbackForm
from .models import Post


def post_list(request):
    posts = Post.objects.filter(is_published=True)
    return render(request, "blog/list.html", {"posts": posts})


def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    return render(request, "blog/detail.html", {"post": post})


def about(request):
    return render(request, "pages/about.html")


def privacy(request):
    return render(request, "pages/privacy.html")


def disclaimer(request):
    return render(request, "pages/disclaimer.html")


def terms(request):
    return render(request, "pages/terms.html")


def contact(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Gracias! Recibimos tu mensaje.")
            return redirect("page-contact")
    else:
        form = FeedbackForm()

    return render(request, "pages/contact.html", {"form": form})
