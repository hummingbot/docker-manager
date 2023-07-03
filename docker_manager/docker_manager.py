import os
import shutil
import subprocess
from typing import Dict
import docker
from docker.types import LogConfig

from docker_manager import os_utils


class DockerManager:
    def __init__(self):
        self.client = docker.from_env()

    def get_active_containers(self):
        containers = self.client.containers.list()
        container_names = [container.name for container in containers]
        return container_names

    def get_exited_containers(self):
        containers = self.client.containers.list(all=True, filters={'status': 'exited'})
        container_names = [container.name for container in containers]
        return container_names

    def clean_exited_containers(self):
        self.client.containers.prune()

    def stop_active_containers(self):
        containers = self.get_active_containers()
        for container in containers:
            container_obj = self.client.containers.get(container)
            container_obj.stop()

    def stop_container(self, container_name):
        container_obj = self.client.containers.get(container_name)
        container_obj.stop()

    def start_container(self, container_name):
        container_obj = self.client.containers.get(container_name)
        container_obj.start()

    def remove_container(self, container_name):
        container_obj = self.client.containers.get(container_name)
        container_obj.remove()

    def create_download_candles_container(self, candles_config: Dict, yml_path: str):
        os_utils.dump_dict_to_yaml(candles_config, yml_path)
        command = ["docker", "compose", "-p", "data_downloader", "-f",
                   "hummingbot_files/compose_files/data-downloader-compose.yml", "up", "-d"]
        subprocess.Popen(command)

    def create_broker(self):
        command = ["docker", "compose", "-p", "hummingbot-broker", "-f",
                   "hummingbot_files/compose_files/broker-compose.yml", "up", "-d", "--remove-orphans"]
        subprocess.Popen(command)

    def create_hummingbot_instance(self, instance_name, base_conf_folder, target_conf_folder):
        os.makedirs(target_conf_folder, exist_ok=True)
        shutil.copytree(base_conf_folder, target_conf_folder, dirs_exist_ok=True)
        conf_file_path = f"{target_conf_folder}/conf/conf_client.yml"
        config = os_utils.read_yaml_file(conf_file_path)
        config['instance_id'] = instance_name
        os_utils.dump_dict_to_yaml(config, conf_file_path)
        lc = LogConfig(config={
        'max-size': '10m',
        'max-file':5,
        })
        container = self.client.containers.run(
            "dardonacci/hummingbot:development",
            name=instance_name,
            network_mode="host",
            volumes={
                f"./{target_conf_folder}/conf": {'bind': '/home/hummingbot/conf', 'mode': 'rw'},
                f"./{target_conf_folder}/conf/connectors": {'bind': '/home/hummingbot/conf/connectors', 'mode': 'rw'},
                f"./{target_conf_folder}/conf/strategies": {'bind': '/home/hummingbot/conf/strategies', 'mode': 'rw'},
                f"./{target_conf_folder}/logs": {'bind': '/home/hummingbot/logs', 'mode': 'rw'},
                "./data/": {'bind': '/home/hummingbot/data', 'mode': 'rw'},
                f"./{target_conf_folder}/certs": {'bind': '/home/hummingbot/certs', 'mode': 'rw'},
            },
            environment=["CONFIG_PASSWORD=a"],
            detach=True,
            log_config = lc
        )