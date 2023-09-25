import subprocess
from typing import Dict, Optional
import yaml

from docker_manager import os_utils


class DockerManager:
    def __init__(self):
        pass

    @staticmethod
    def get_active_containers():
        cmd = "docker ps --format '{{.Names}}'"
        output = subprocess.check_output(cmd, shell=True)
        backtestings = [container for container in output.decode().split()]
        return backtestings

    @staticmethod
    def get_exited_containers():
        cmd = "docker ps --filter status=exited --format '{{.Names}}'"
        output = subprocess.check_output(cmd, shell=True)
        containers = output.decode().split()
        return containers

    @staticmethod
    def clean_exited_containers():
        cmd = "docker container prune --force"
        subprocess.Popen(cmd, shell=True)

    @staticmethod
    def is_docker_running():
        cmd = "docker ps"
        try:
            subprocess.check_output(cmd, shell=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_active_containers(self):
        containers = self.get_active_containers()
        for container in containers:
            cmd = f"docker stop {container}"
            subprocess.Popen(cmd, shell=True)

    def stop_container(self, container_name):
        cmd = f"docker stop {container_name}"
        subprocess.Popen(cmd, shell=True)

    def start_container(self, container_name):
        cmd = f"docker start {container_name}"
        subprocess.Popen(cmd, shell=True)

    def remove_container(self, container_name):
        cmd = f"docker rm {container_name}"
        subprocess.Popen(cmd, shell=True)

    def create_download_candles_container(self, candles_config: Dict, yml_path: str):
        os_utils.dump_dict_to_yaml(candles_config, yml_path)
        command = ["docker", "compose", "-p", "data_downloader", "-f",
                   "hummingbot_files/compose_files/data-downloader-compose.yml", "up", "-d"]
        subprocess.Popen(command)

    def create_broker(self):
        command = ["docker", "compose", "-p", "hummingbot-broker", "-f",
                   "hummingbot_files/compose_files/broker-compose.yml", "up", "-d", "--remove-orphans"]
        subprocess.Popen(command)

    def create_hummingbot_instance(self, instance_name: str,
                                   base_conf_folder: str,
                                   target_conf_folder: str,
                                   controllers_folder: Optional[str] = None,
                                   controllers_config_folder: Optional[str] = None,
                                   extra_environment_variables: Optional[list] = None,
                                   image: str = "hummingbot/hummingbot:latest"):
        if not os_utils.directory_exists(target_conf_folder):
            create_folder_command = ["mkdir", "-p", target_conf_folder]
            create_folder_task = subprocess.Popen(create_folder_command)
            create_folder_task.wait()
            command = ["cp", "-rf", base_conf_folder, target_conf_folder]
            copy_folder_task = subprocess.Popen(command)
            copy_folder_task.wait()
        if controllers_folder and controllers_config_folder:
            # Copy controllers folder
            command = ["cp", "-rf", controllers_folder, target_conf_folder]
            t1 = subprocess.Popen(command)
            t1.wait()
            # Copy controllers config folder
            command = ["cp", "-rf", controllers_config_folder, target_conf_folder]
            t2 = subprocess.Popen(command)
            t2.wait()
        conf_file_path = f"{target_conf_folder}/conf/conf_client.yml"
        config = os_utils.read_yaml_file(conf_file_path)
        config['instance_id'] = instance_name
        os_utils.dump_dict_to_yaml(config, conf_file_path)
        # TODO: Mount script folder for custom scripts
        create_container_command = ["docker", "run", "-it", "-d", "--log-opt", "max-size=10m", "--log-opt",
                                    "max-file=5",
                                    "--name", instance_name,
                                    "--network", "host",
                                    "-v", f"./{target_conf_folder}/conf:/home/hummingbot/conf",
                                    "-v", f"./{target_conf_folder}/conf/connectors:/home/hummingbot/conf/connectors",
                                    "-v", f"./{target_conf_folder}/conf/strategies:/home/hummingbot/conf/strategies",
                                    "-v", f"./{target_conf_folder}/logs:/home/hummingbot/logs",
                                    "-v", f"./{target_conf_folder}/data/:/home/hummingbot/data",
                                    "-v", f"./{target_conf_folder}/scripts:/home/hummingbot/scripts",
                                    "-v", f"./{target_conf_folder}/certs:/home/hummingbot/certs",
                                    "-v", f"./{controllers_folder}:/home/hummingbot/hummingbot/smart_components/controllers",
                                    "-v", f"./{controllers_config_folder}:/home/hummingbot/conf/controllers_config",
                                    "-e", "CONFIG_PASSWORD=a"]

        if extra_environment_variables:
            create_container_command.extend(extra_environment_variables)
        create_container_command.append(image)
        subprocess.Popen(create_container_command)
