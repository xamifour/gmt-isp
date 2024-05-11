from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import ListView

from .models import Project, Shelf


class ShelfListView(ListView):
    model = Shelf
    context_object_name = 'shelves'
    template_name = 'testing_app/shelf_list.html'

shelf_list = ShelfListView.as_view()


class ShelfView(View):
    """
    This test view allows to check the validity of the pk and the key, and receive shelf name
    Required query string parameters:
        * key
    """

    def get(self, request, pk):
        try:
            shelf = Shelf.objects.get(pk=pk)
        except Shelf.DoesNotExist:
            return JsonResponse({'detail': _('shelf not found')}, status=400)
        key = request.GET.get('key')
        if shelf.key != key:
            return JsonResponse({'detail': _('wrong key')}, status=403)
        return JsonResponse({'detail': _('ok'), 'name': shelf.name}, status=200)

shelf = ShelfView.as_view()


class ProjectListView(ListView):
    model = Project
    context_object_name = 'projects'
    template_name = 'testing_app/project_list.html'

project_list = ProjectListView.as_view()


class ReceiveProjectView(View):
    """
    This test view allows to check the validity of the pk and the key, and receive project name
    Required query string parameters:
        * key
    """

    def get(self, request, pk):
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return JsonResponse({'detail': _('project not found')}, status=400)
        key = request.GET.get('key')
        if project.key != key:
            return JsonResponse({'detail': _('wrong key')}, status=403)
        return JsonResponse({'detail': _('ok'), 'name': project.name}, status=200)


receive_project = ReceiveProjectView.as_view()
