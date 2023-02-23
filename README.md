Wazo plugin Hubspot
======================

## Info

This plugin gets contacts from Hubspot thanks to its API.

Highly based on wazo-dird-plugin-backend-odoo by alexis-via and sboily (https://github.com/sboily/wazo-dird-plugin-backend-odoo).

Works only with **Wazo >= 20.11**

### Roadmap

- [ ] CRM integration in dird (search, lookup, favorites)

May need to move from private app to marketplace app:

- [ ] CTI from CRM interface (https://github.com/HubSpot/calling-extensions-sdk)
- [ ] WebRTC integration in CRM interface
- [ ] Call events in object timeline
- [ ] Call records in object timeline

## How to install

⚠️ hubspot-api-client 7.4.0 needs to be installed beforehand, you can use `pip`.
Maybe in the future, we will be able to install it automatically.

⚠️ Be careful to precise "main" branch as wazo-plugind use "master" by default.

### Interface

Go to Wazo UI on plugins link.
In git tab add:

    https://github.com/ecole-hexagone/wazo-plugin-hubspot

Then click to install the plugin.

### API

Use wazo-plugind's API endpoint:

    https://<YOUR_WAZO_IP>/api/plugind/0.2/plugins

POST body:

    {
        "method": "git",
        "options": {
            "url": "https://github.com/ecole-hexagone/wazo-plugin-hubspot",
            "ref": "main"
        }
    }

### CLI (not tested yet, but seems to miss a way to pass `ref` attribute )

    apt-get install wazo-plugind-cli
    wazo-plugind-cli -c "install git https://github.com/ecole-hexagone/wazo-plugin-hubspot"

## How to configure

Use API or Wazo-platform UI and set the private app access token.

### How to obtain a private app access token

Create a private app in your Hubspot account with at least `crm.object.contacts.read` and `crm.object.companies.read`.  
Use the access token generated then.

More documentation on private app: https://developers.hubspot.com/docs/api/private-apps
