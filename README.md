## Python Nominet EPP Client API

This repository contains a Flask-based API that interacts with the Nominet EPP (Extensible Provisioning Protocol) server to manage domain
information and nameservers. The API uses a custom EPP library `Lib.EPPClient`  to communicate with the EPP server and the
connections are configured via the `config.json` file.

This system supports multiple tags, once connected the tag name is used in the API request to specify which tag you are working on.

This is a project created for myself but i've made it available for others to use, little to no support is provided as it's just a hobby project and almost certainly will have problems. Was purely
built as the Nominet WDM is a pain in the arse. Could be useful if you are a regular domain seller/auctioner to update nameservers and release domain
names.

I'd recommended running it somewhere and creating a wrapper to make the API calls, useful probably for bulk updates or renewals. 

### Current Features

* Set Nameservers (including ability to replace existing)
* Release domains to another tag
* Create domain to a specific tag using an exisiting contact ID
* Renew domains

### Planned Features

* Better formatting of Nominet EPP responses returned on the API
* Nominet Hello to keep connection alive (and reconnect if disconnected for any reason)

### Installation

Tested on Python 3.7

* Clone the repository to your server
* setup config.json (rename example.config.json and edit in your details, for api_key use a string which will be used in the call, for api_url i use 0.0.0.0 which seems to work)
* Install any requirements (flask etc)
* Setup any firewall rules that you need to make the API accessible from the web.
* Run the script (and wait for it to let you know it's running)

### Commands

#### Create

```Shell
curl -X POST http://server-address:5000/command/create -H "Content-Type: application/json" -H "API-Key: your_api_key_here" -d '{"username": "your_tag_here", "domain_name": "domain-here.co.uk", "reg_period": "reg_period_here", "contact_id": "nominet_contact_id"}'
```

#### Renew Domain

```Shell
curl -X POST http://server-address:5000/renewDomain -H "Content-Type: application/json" -H "API-Key: your_api_key_here" -d "{\"username\": \"your_tag_here\", \"domain_name\": \"domain-here.co.uk\", \"renewal_period\": \"period_year\"}"
```

#### Release

```Shell
curl -X POST http://server-address:5000/command/release -H "API-Key: your_api_key_here" ^ -H "Content-Type: application/json" ^ -d "{\"username\": \"your_tag_here\", \"domain_name\": \"domain-here.co.uk\", \"release_tag\": \"RELEASETAG\""}"
```

#### Update Nameservers 
(add keepNS : true if you want to keep the current NS intact)

```Shell
curl -X POST http://server-address:5000/setNS -H "API-Key: your_api_key_here" -H "Content-Type: application/json" -d "{\"username\": \"your_tag_here\", \"domain_name\": \"domain-here.co.uk\", \"nameservers\": [\"ns1.nameservers.co.uk.\", \"ns2.nameservers.co.uk.\"]}"
```