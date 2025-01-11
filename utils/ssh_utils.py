import asyncssh
import re

async def execute_outline_server(host, user, password):
    """
    Asynchronous version of execute_outline_server using asyncssh.
    Connects to the server, installs Docker, and sets up the outline server.
    """
    # Убедитесь, что эта команда определена
    setup_outline_command = 'sudo bash -c "$(wget -qO- https://raw.githubusercontent.com/Jigsaw-Code/outline-server/master/src/server_manager/install_scripts/install_server.sh)"'

    try:
        print(f"[INFO] Connecting to {host} as {user}...")
        async with asyncssh.connect(
                host=host,
                username=user,
                password=password,
                known_hosts=None  # Отключение проверки ключей (как AutoAddPolicy в Paramiko)
        ) as conn:
            print("[INFO] SSH connection established.")

            # Установка Docker
            install_docker_command = 'curl -fsSL https://get.docker.com/ | sh'
            print(f"[INFO] Executing: {install_docker_command}")
            docker_result = await conn.run(install_docker_command, check=True)

            print(f"[INFO] Docker installation completed.")
            print(f"[STDOUT] {docker_result.stdout}")
            if docker_result.stderr:
                print(f"[STDERR] {docker_result.stderr}")

            # Выполнение команды для установки Outline Server
            print(f"[INFO] Executing outline setup command: {setup_outline_command}")
            outline_result = await conn.run(setup_outline_command, check=True)

            print(f"[INFO] Outline setup command completed.")
            print(f"[STDOUT] {outline_result.stdout}")
            if outline_result.stderr:
                print(f"[STDERR] {outline_result.stderr}")

            # Возврат результата
            return outline_result.stdout, outline_result.stderr

    except asyncssh.Error as e:
        print(f"[ERROR] SSH connection or command execution failed: {str(e)}")
        return None, str(e)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {str(e)}")
        return None, str(e)



def get_data_from_output(output: str):
    # Извлекаем данные с помощью регулярных выражений
    all_output = re.findall(r"\{.*?}", output, flags=re.DOTALL)
    api_url = re.search(r'"apiUrl":"(.*?)"', output).group(1)
    cert_sha256 = re.search(r'"certSha256":"(.*?)"', output).group(1)
    management_port = re.search(r'Management port (\d+)', output).group(1)
    access_key_port = re.search(r'Access key port (\d+)', output).group(1)

    return all_output, api_url, cert_sha256, int(management_port), int(access_key_port)