# INSTALLING

## Installing uWSGI Service

The following instructions target Ubuntu 18.04 LTS

* Rename `uwsgi.dist.ini` to `uwsgi.ini`
* Copy `uwsgi.dist.service` to `/etc/systemd/system/<API Service Name>.service`
* Run:

```bash
    sudo systemctl start <API Service Name>
    sudo systemctl enable <API Service Name>
```

* Verify service status

```bash
    sudo systemctl status <API Service Name>
```

## Setting up NGINX to Serve Static Files

Instead of having uWSGI serve the static content, NGINX can be configured to
serve the files directly by including the following directives in the site's
configuration file.

```
	location /static/ {
		root <project_path>;
		autoindex off;
	}

	location = /favicon.ico {
		alias <project_path>/static/favicon.ico;
	}
```
