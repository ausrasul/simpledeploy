# SimpleDeploy
SimpleDeploy is a unique Continuous Integration/Continuous Deployment (CI/CD) solution tailored for individual developers.

It operates directly on the deployment server, bringing the build process to the code,
rather than the traditional method of bringing the code to the build process.

This approach simplifies the deployment pipeline and offers a streamlined, efficient workflow for developers.

The deployment server doesn't need to provide access for a CI/CD pipeline.

SimpleDeploy works with any Git source control provider, making it a versatile tool for various development environments.

              +------------+
              |  Git Repo  |
              +------------+
                    |
                    v
        +------------------------+
        |   Deployment Server    |
        |  Running SimpleDeploy  |
        |                        |
        |  +------------------+  |
        |  | Pull Latest Code |  |
        |  +------------------+  |
        |    on new | commits    |
        |           v            |
        |  +------------------+  |
        |  | Read Config File |  |
        |  +------------------+  |
        |           |            |
        |           v            |
        |  +------------------+  |
        |  | Execute Workflow |  |
        |  +------------------+  |
        |           |            |
        |           v            |
        |  +------------------+  |
        |  | Generate Report  |  |
        |  |        Or        |  |
        |  |  Serve content   |  |
        |  +------------------+  |
        +------------------------+


## Usage

  On the server where the deployment happens, clone this repository.

### Configure SimpleDeploy
  Configure the config.json file:

    {
        "repo": {
            "dir": "../open_math",
            "cfg_file": "./ci.json",
            "url": "https://github.com/ausrasul/open_math.git",
            "branch": "some-feature-branch-name",
            "git_auth": {
            "require_auth": false,
                "username": "ausrasul",
                "access_token": "12345678910"
            },
            "mount_dir": "/pipeline",
            "trigger": {
                "branch": "master",
                "tag": "open_math-v*.*.*"
            }
        }
    }


    dir: Where the code repo will be cloned.
         Relative directory from where SimpleDeploy is.
    cfg_file: the ci/cd config file, path relative to the repository.
    url: url to git repo.
    branch: default is "main", specify the branch that you want to simpledeploy to target for deployment.
    git_auth: if a private repo, set require_auth to true and provide the access token.
    mount_dir: Where in the podman container the repository will be mounted.
    trigger: WIP.

### Configure your project
  In your repository, create a json file (must be placed in "cfg_file" directory specified above) and configure it:

    {
        "volumes":[
            "redis_volume"
        ],
        "name": "open_math",
        "app": {
            "name": "open_math_container",
            "hostname": "open_math",
            "image": "node:18",
            "command": "node ./server.js",
            "env": [
                "NODE_ENV=production"
            ],
            "ports": [
                "8080:3001"
            ]
        },
        "services": [
            {
                "name": "my_redis",
                "image": "redis",
                "hostname": "redis",
                "volumes": [
                    "redis_volume:/data"
                ],
                "env": [
                    "myenv=production"
                ]
            }
        ]
    }

    volumes: list of volumes to be created.
    name: the podman pod's name.
    app:
        name: container name, must be unique per server.
        hostname: hostname (this is not supported yet, the pod's name is used instead)
        image: podman/docker image name and version
        command: command used as entry point.
        env: env.
        ports: ports to be published, unique per pod, should not conflict with ports from service.
    services: containers to be run and linked to the app container.

#### Longer command chain
You can also write longer command to run.

Instead of providing command as string ```command": "node ./server.js"```

You can provide it as a list of commands, each command must end with semicolon to be concatenated.

    "command": [
        "cd /simpledeploy/config;",
        "make;",
        "cd /simpledeploy/etc/;",
        "cp myconf myconf.bak;",
        "sed -i 's/conf_name$/conf_name2/g' ./conf;",
        "make;",
        "mv myconf.bak myconf;",
        "node ./server.js"
    ],
    
### Schedule SimpleDeploy to run in crontab
  example

    * * * * * /usr/bin/python3 /home/open_math/simpledeploy/simpledeploy.py >> /tmp/simpledeploy.log 2>&1

### Troubleshoot

A common issue is that podman will exit as soon as you logout.

To solve this, start podman with systemd, alternatively set enable-linger to the user that started podman.

    $ loginctl enable-linger [USER]

Another issue is podman requires fully qualified images if they are pulled from dockerhub
Add docker.io to the unqualified search registries in podman:
    $ vi /etc/containers/registries.conf

then add:

    unqualified-search-registries = ["docker.io"]

### Options

  Pull repository and run the pipeline even if there are no changes to the git history of the repo.
    $ python3 ./simpledeploy.py -d
    Or
    $ python3 ./simpledeploy.py --deploy-anyway

  Don't pull repository, just run the pipeline.
    $ python3 ./simpledeploy.py -r
    Or
    $ python3 ./simpledeploy.py -rerun-only
