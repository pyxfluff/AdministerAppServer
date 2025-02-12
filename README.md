<div align = "center">
<img src="https://github.com/administer-org/app-server/blob/main/assets/adm.png?raw=true" width="128">

# App Server

[![administer-org - app-server](https://img.shields.io/static/v1?label=administer-org&message=app-server&color=green&logo=github)](https://github.com/administer-org/app-server "Go to GitHub repo") [![stars - app-server](https://img.shields.io/github/stars/administer-org/app-server?style=social)](https://github.com/administer-org/app-server) [![forks - app-server](https://img.shields.io/github/forks/administer-org/app-server?style=social)](https://github.com/administer-org/app-server)

[![GitHub tag](https://img.shields.io/github/tag/administer-org/app-server?include_prereleases=&sort=semver&color=green)](https://github.com/administer-org/app-server/releases/) [![License](https://img.shields.io/badge/License-AGPL--3.0-green)](#license) [![issues - app-server](https://img.shields.io/github/issues/administer-org/app-server)](https://github.com/administer-org/app-server/issues) [![Hits-of-Code](https://hitsofcode.com/github/administer-org/app-server?branch=main)](https://hitsofcode.com/github/administer-org/app-server/view?branch=main)

</div>


### What is it?

The App Server is a FastAPI/MongoDB program which stores apps for use in Administer and a website later on, there is no backend panel or anything. What you see is what you get.

### Installing a dev app server

We are working on improvements to this system (installation script, central config, ...) for a later date but this should hold you over for now.

- Install MongoDB, uv, and Python 3.13.
- Clone the repository and edit the `globals` section of `AOS/__init__.py` to fit your specific needs. You'll also need to generate a security key and set it in the SECRETS db.
- Run `uv venv`, enter the newly created enviornment with `source .venv/bin/activate`, and run `uv pip install -e . --force-reinstall`. 

... and you're done! You can now run `aos` to access the Marketplace Server CLI. To create new assets in the DB, use the `/app-config/upload` endpoint. For more information, read [the documentation]() 

## Central Server Privacy

*Last Modified: 1/18/25*

Administer is designed with privacy as a top priority. We only collect the data necessary to operate this service, and this data is never accessed by anyone other than the system itself. All information is securely stored in an internal MongoDB instance and is never read, shared, or sold by Administer staff. Specifically, we only collect your **Roblox Place ID** and the apps you install to ensure safety for the rating system.

To ensure platform safety, we may log requests if you attempt to misuse our API; for example, creating fake places, impersonating a game server, or engaging in other forms of abuse. In such cases, we will log the following information:

- Timestamp
- Basic IP details (country, ISP, IP, proxy information, state/region)
- Attempted Roblox ID
- User-Agent string

**Important:** This data is only collected if abusive behavior is detected. For legitimate usage, such as within Roblox game servers, no IP information is collected. Abusing the service will result in permanent blockage, and such decisions are typically final unless there is compelling evidence of error.

If you believe you were wrongly flagged and recieved a "This incidient will be reported" message in error, please [contact us](mailto:administer-team@notpyx.me) to resolve the issue and remove your information from our logs.

The only information we include by default is your Administer version for analytics. It is stored in aggregate and your Roblox Place ID is not associated with any data. For example, we **do** collect:

- Aggregate counts of every place in the database (for knowing how many users we have overall)
- Administer version data from every panel (for knowing how new versions are being adopted and if its safe to remove old AOS features)
- Individual place IDs and what apps you installed and have votes for (This is **never** read by any staff manually or automatically. Eventually we are looking to encrypt this data.)

We do **not collect**:

- How many times your individual game uses Administer
- The commands/apps you regularly use
- Your usage of Administer features, settings, apps, etc.
- Your game's admin/rank structure
- Any other information from your game or Administer

If we change this policy (for example opt-in detailed analytics, comments on apps, ...), you will be notified via the Discord server, panel (if it's significant), and other appropriate channels.

## Contributions

We welcome contributions as long as they are meaningful. Please ensure you are familiar with our code standards and libraries before making pull requests. For larger changes, you may want to [discuss a change in our Discord beforehand.](https://administer.notpyx.me/to/discord)


## License

All of Administer and your usage of it is governed under the GNU AGPL 3.0 license.

<small>Administer Team 2024-2025</small>
