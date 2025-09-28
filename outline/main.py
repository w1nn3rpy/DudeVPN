from outline_vpn.outline_vpn import OutlineVPN, OutlineKey

class OutlineConnection:
    def __init__(self, api_url, cert_sha256):
        self.api_url = api_url
        self.cert_sha256 = cert_sha256
        self.client = OutlineVPN(api_url=api_url, cert_sha256=cert_sha256)

    def get_keys(self) -> list:
        """
        key_id (str идентификатор айди, очень важный)
        name (str, имя ключа, иногда полезно, например, чтоб понимать какой ключ и под какое устройство или чей ключ)
        access_url (str, ключ для подключения к VPN)
        used_bytes (использованное количество байтов)
        data_limit (float лимит на использование данных)
        :return: list
        """
        return self.client.get_keys()

    def _find_key(self, *, key_id=None, access_url=None) -> OutlineKey|None:
        """
        Универсальный метод для поиска ключа по его id или access_url.
        :param key_id: Идентификатор ключа
        :param access_url: URL ключа
        :return: Объект OutlineKey, если найден
        """
        vpn_keys = self.get_keys()
        for key in vpn_keys:
            if key_id and key.key_id == key_id:
                return key
            if access_url and key.access_url == access_url:
                return key
        return None

    def get_key_from_id(self, key_id: str) -> str:
        key = self._find_key(key_id=key_id)
        return key.access_url if key else None

    def get_key_id_from_url(self, access_url: str) -> str:
        key = self._find_key(access_url=access_url)
        return key.key_id if key else None

    def create_new_key(self, key_id: str = None, name: str = None, data_limit_bytes: float = None) -> OutlineKey:
        """
        Создание нового ключа
        Возвращает ВСЕ ДАННЫЕ созданного ключа
        """
        return self.client.create_key(key_id=key_id, name=name, data_limit=data_limit_bytes)

    def delete_key_method(self, key_id: str) -> None:
        """
        Удаляет ключ
        """
        try:
            self.client.delete_key(key_id=key_id)
        except Exception as e:
            print(f'Ошибка в {__name__}: {e}')
