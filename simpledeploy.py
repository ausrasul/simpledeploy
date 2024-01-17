import os
import subprocess
import configparser
import json

def this_script_dir():
    return os.path.dirname(os.path.realpath(__file__))

def read_ini_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return {k: v for k, v in config.items()}

def read_config(filename):
    # reads json config file
    with open(filename, 'r') as f:
        config = json.load(f)
    return config

class Repo:
    def __init__(self, config_file):
        script_dir = this_script_dir()
        config_file = os.path.join(script_dir, config_file)
        config = read_config(config_file)
        
        self.dir = os.path.join(script_dir, config['repo']['dir'])
        self.url = config['repo']['url']
        self.mount_dir = config['repo']['mount_dir']
        self.cfg_file = config['repo']['cfg_file']

class Container:
    def __init__(self, cfg):
        self.name = cfg['name']
        self.image = cfg.get('image', 'ubuntu:latest')
        self.command = cfg.get('command')
        self.ports = cfg.get('ports', [])
        self.volumes = cfg.get('volumes', [])
        self.work_dir = cfg.get('work_dir')

    def _remove(self):
        try:
            subprocess.run(['podman', 'rm', '-f', self.name], check=True)
            print(f"Container {self.name} removed.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e.stderr}")
    def stop(self):
        try:
            subprocess.run(['podman', 'stop', self.name], check=True)
            print(f"Container {self.name} stopped.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e.stderr}")
        finally:
            self._remove()
    
    def start(self, podname):
        command = [
            'podman', 'run', '-d',
            '--name', self.name,
            '--pod', podname,
        ]
        for volume in self.volumes:
            command.extend(['-v', volume])
        if self.work_dir:
            command.extend(['-w', self.work_dir])
        command.append(self.image)
        if self.command:
            command.extend(['bash', '-c', self.command])
        print(command)
        subprocess.run(command, check=True)


class App:
    def __init__(self, repo):
        script_dir = this_script_dir()
        abs_file_name = os.path.join(script_dir, repo.dir, repo.cfg_file)
        config = read_config(abs_file_name)

        self.name = config['name']

        app = config.get('app', {})
        volumes = app.get('volumes',[])
        volumes.extend([
            f"{repo.dir}:{repo.mount_dir}"
        ])
        app['volumes'] = volumes
        app['work_dir'] = repo.mount_dir
        self.container = Container(app)

        services = config.get('services', [])
        self.services = []
        for service in services:
            self.services.append(Container(service))
    
    def _create_pod(self):
        command = ['podman', 'pod', 'create', '--name', self.name]
        for port in self.container.ports:
            command.extend(['-p', port])
        for service in self.services:
            for port in service.ports:
                command.extend(['-p', port])
        subprocess.run(command, check=True)
    def _remove_pod(self):
        command = ['podman', 'pod', 'rm', '-f', self.name]
        for _ in range(3):  # Retry the command 3 times
            try:
                subprocess.run(command, check=True, timeout=5)
                break  # Break the loop if the command succeeds
            except:
                continue  # Retry the command if it fails

    def start(self):
        self._create_pod()
        self._services_start()
        self.container.start(podname=self.name)
    def stop(self):
        self._remove_pod()
        self.container.stop()
        self._services_stop()
    def _services_start(self):
        for service in self.services:
            print(service)
            service.start(podname=self.name)
    def _services_stop(self):
        for service in self.services:
            service.stop()

def clone_repo_if_not_exist(repo_name, repo_dir):
    if not os.path.exists(repo_dir):
        # Clone the repo if it doesn't exist
        subprocess.run(['git', 'clone', repo_name, repo_dir], check=True)
        return True
    else:
        return False

def git_clone_or_pull(repo_name, repo_dir):
    # Change to the directory specified in the configuration file
    cloned = clone_repo_if_not_exist(repo_name, repo_dir)
    if cloned:
        return 1, 2
    else:
        os.chdir(repo_dir)
        prev_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
        subprocess.run(['git', 'pull'], check=True)
        this_hash = subprocess.run(['git', 'rev-parse', 'HEAD'], stdout=subprocess.PIPE, text=True).stdout.strip()
        return prev_hash,this_hash


def main():
    repo = Repo('config.json')
    prev_hash, this_hash = git_clone_or_pull(repo.url, repo.dir)

    os.chdir(repo.dir)
    print(prev_hash, this_hash)
    # Check if there are any new commits since the last run
    if prev_hash != this_hash:
        app = App(repo)
        app.stop()
        app.start()


if __name__ == '__main__':
    main()