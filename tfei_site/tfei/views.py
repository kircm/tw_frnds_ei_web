from django.shortcuts import render


def index(request):
    context = {}

    return render(request, 'tfei/index.html', context)


def main_v(request):
    context = {}

    return render(request, 'tfei/main.html', context)


def export_v(request):
    context = {}

    return render(request, 'tfei/export.html', context)


def import_v(request):
    context = {}

    return render(request, 'tfei/import.html', context)


def logout_v(request):
    context = {}

    return render(request, 'tfei/logout.html', context)

