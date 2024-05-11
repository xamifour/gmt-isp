import requests

from django.shortcuts import render
from django.views import View
from django.http import HttpResponse


class ItemListView(View):
    template_name = 'enduser/item_list.html'
    base_url = 'http://127.0.0.1:8000/testapp_api/shelfs/'

    def get(self, request):
        response = requests.get(self.base_url)
        if response.status_code == 200:
            items = response.json()
            return render(request, self.template_name, {'items': items})
        else:
            return HttpResponse(status=response.status_code)


class ItemDetailView(View):
    template_name = 'enduser/item_detail.html'
    base_url = 'http://127.0.0.1:8000/testapp_api/shelfs/'

    def get(self, request, item_id):
        url = self.base_url + str(item_id) + '/'
        response = requests.get(url)
        if response.status_code == 200:
            item = response.json()
            return render(request, self.template_name, {'item': item})
        else:
            return HttpResponse(status=response.status_code)


# from django.shortcuts import render

# from appsinn.enduser.api.services import ItemService

# def item_list(request):
#     items = ItemService.get_items()
#     return render(request, 'enduser/item_list.html', {'items': items})

# def item_detail(request, item_id):
#     item = ItemService.get_item(item_id)
#     return render(request, 'enduser/item_detail.html', {'item': item})
