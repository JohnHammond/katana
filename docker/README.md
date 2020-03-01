# Katana Docker Image

## Building

```
$ docker build -t katana .
```

_NOTE_ - The build process takes 5-10 minutes on our development machines.
There are a lot of dependencies to to install and/or build. Be patient.

## Running Katana

The default command for the docker image is:

```
python -m katana -c /data/katana.ini -m \
	monitor=/data/targets,outdir=/data/results
```

We recommend running Katana with the following command:

```shell
$ docker run -v "$(CTF_DIRECTORY):/data" -it katana
```

Where `CTF_DIRECTORY` is a directory with a configuration file and a `targets`
directory. After Katana is started, it will automatically monitor the `targets`
directory for targets to queue or you can manually queue targets as normal at
the REPL. 

The smallest configuration file you can use could be `katana.ini` like so:

```
[manager]
flag-format=FLAG{.*?}
```

## Issues

The things that do not work when using the Docker container:

* Clipboard

	When Katana finds a flag, it will not be able to have it automatically
	copied into your clipboard.

* Notifications

	When Katana finds a flag, it will not be able to send you a desktop
	notification explaining that it solved a challenge.