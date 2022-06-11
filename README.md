[![codecov](https://codecov.io/gh/lynshi/league-history-collector/branch/main/graph/badge.svg?token=G65K6F476C)](https://codecov.io/gh/lynshi/league-history-collector) ![Build](https://github.com/lynshi/league-history-collector/workflows/Build/badge.svg)

# league-history-collector
Collects fantasy league data.

# Setup
This project uses [`selenium`](https://selenium-python.readthedocs.io/). To more easily work across platforms and, more importantly, use WSL, I used [`docker-selenium`](https://github.com/SeleniumHQ/docker-selenium) to run Chrome in Docker for `selenium` to use.

```bash
docker run -d -p 4444:4444 --shm-size="2g" selenium/standalone-chrome:4.2.1-20220531
```

This starts the driver on port 4444, which corresponds to the default URL of `http://localhost:4444/wd/hub` in the `Remote` `WebDriver` of Selenium.

For M1 Macs, use [docker-seleniarm](https://github.com/seleniumhq-community/docker-seleniarm) (`./build.sh arm64`) and
```bash
docker run --rm -it -p 4444:4444 -p 5900:5900 -p 7900:7900 --shm-size 3g local-seleniarm/standalone-chromium:latest
```

# Debugging
To view the browser as Selenium is working, you can use [noVNC](https://github.com/novnc/noVNC). Run `./utils/novnc_proxy --vnc localhost:5900` (assuming VNC is exposed on port 5900). The password is `secret`.
