# [Exabuster](https://zalo.github.io/Exabuster/)

Exabuster is the Github Actions version of [Buster](https://github.com/axitkhurana/buster), the brute-force static site generator for Ghost.  Exabuster is still a heavy work-in-progress!

The Exabuster Github Workflow crawls a locally constructed version of your Ghost website and pushes the acquired HTML, CSS, Javascript, and Media to the `gh-pages` branch of a Github repository, where Github can serve it directly.  

This means you can write blog posts in the polished Ghost CMS, and then publish and host them for free on the world-class Github Pages hosting system.

## Usage

While Exabuster is in Alpha, the setup process is:

 1. Find or create a local instance of your blog by following [these steps.](https://ghost.org/docs/install/local/)

 2. Copy the exabuster.py, .gitignore, static, and .github files or folders from the Exabuster repository to your blog's root directory.

 3. Edit the --new-domain variable in .github/workflows/main.yml to be your new expected Github pages domain.  This blog's was https://zalo.github.io/Exabuster. (Make sure not to include a trailing slash)

 4. Create a Github repository on your Blog's root directory and push your first commit.


From there, Exabuster should automatically handle building your blog via Github Actions, so wait a few minutes, and then check out your Github Pages domain!

## Credits

This script is heavily based off of and inspired by the original [Buster](https://github.com/axitkhurana/buster) static site generator by [axitkhurana](https://github.com/axitkhurana).