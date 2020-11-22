# league-history-collector
Collects fantasy league data.

# Setup
This project uses [`selenium`](https://selenium-python.readthedocs.io/). To more easily work across platforms and, more importantly, use WSL, I used [`docker-selenium`](https://github.com/SeleniumHQ/docker-selenium) to run Chrome in Docker for `selenium` to use.

```
docker run --rm -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome:4.0.0-alpha-7-20201119
```

This starts the driver on port 4444, which corresponds to the default URL of `http://localhost:4444/wd/hub` in the `Remote` `WebDriver` of Selenium.
