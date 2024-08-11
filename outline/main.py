from outline.config import client
from outline_vpn.outline_vpn import OutlineKey


def get_keys() -> list:
    """
    key_id (str идентификатор айди, очень важный)
    name (str, имя ключа, иногда полезно, например, чтоб понимать какой ключ и под какое устройство или чей ключ)
    access_url (str, ключ для подключения к VPN)
    used_bytes (использованное количество байтов)
    data_limit (float лимит на использование данных)
    :return: list
    """
    return client.get_keys()


vpn_keys = get_keys()

# for key in vpn_keys:
#     print(key)


def get_key_from_id(key_id: str) -> str:
    for key in vpn_keys:
        if key.key_id == key_id:
            return key.access_url


def create_new_key(key_id: str = None, name: str = None, data_limit_bytes: float = None) -> OutlineKey:
    """
    Создание нового ключа
    Возвращает ВСЕ ДАННЫЕ созданного ключа
    """
    return client.create_key(key_id=key_id, name=name, data_limit=data_limit_bytes)


def set_limit(key_id: str, limit: float = None) -> None:
    """
    Устанавливает ограничение трафика в байтах
    """
    return client.add_data_limit(key_id=key_id, limit_bytes=limit)


def delete_limit(key_id: str) -> None:
    """
    Снимает ограничение трафика
    """
    return client.delete_data_limit(key_id=key_id)


def delete_key(key_id: str) -> None:
    """
    Удаляет ключ
    """
    return client.delete_key(key_id=key_id)

