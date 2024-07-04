import requests

class ItemService:
    base_url = 'http://127.0.0.1:8000/testapp_api/shelfs/'

    @classmethod
    def get_items(cls):
        response = requests.get(cls.base_url)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    @classmethod
    def get_item(cls, item_id):
        """
        A method to retrieve a specific item by its ID.

        Args:
            cls: The class itself.
            item_id (int): The ID of the item to retrieve.

        Returns:
            dict or None: The JSON response containing the item details if successful, else None.
        """
        url = cls.base_url + str(item_id) + '/'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
