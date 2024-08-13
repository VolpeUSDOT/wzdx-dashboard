# Software Used in WZDx Dashboard

This project aims to have a variety of moving parts, which makes creating one unified system complex. Furthermore, throughout development, the lingering question of how to deploy it publicly/externally using the tools available at Volpe/DOT remains unanswered.

## What we're currently using
Early on, it was decided to use something already familiar to people and relatively well-known, to ensure that this project could be maintained long-term. As of writing, this project is being created in Python using [Django](https://www.djangoproject.com/) due to its dynamic rendering nature, ability to connect easily to a database and send emails, easy authentication integration, native geographic capabilities (through [GeoDjango](https://docs.djangoproject.com/en/4.2/ref/contrib/gis/)), and people's general familiarity with Python. As of writing, it is currently hosted on a virutal machine running [Red Hat Enterprise Linux (RHEL)](https://www.redhat.com/en/technologies/linux-platforms/enterprise-linux) and deployed on an [Nginx web server](https://nginx.org/en/) using [ASGI](https://asgi.readthedocs.io/en/latest/). It is using an internal [PostGIS database](https://postgis.net/), and the frontend was built using raw HTML templating and the [U.S. Web Design System](https://designsystem.digital.gov/).

It is currently deployed and available (internally) at [pathways1.volpe.dot.gov](http://pathways1.volpe.dot.gov/).

## What we've tried
This section includes my impression of various software after a bit of tinkering around. Please, *please* [reach out to me](mailto:diego.temkin@dot.gov) if I'm wrong about something or if you have any suggestions.

- [Shiny](https://shiny.posit.co/py/)
    - Deployment would be very easy using Shinylive (uses [Pyodide](https://pyodide.org/en/stable/) to run Python in WebAssembly), so we could theoretically deploy this on GitHub Pages
    - However, Pyodide unfortunately has many limitations, and many packages are unable to run on it (eg. [GDAL](https://gdal.org/), which limits any dynamic GIS analysis)
    - Although great for making quick prototypes and dashboards, making large complicated web apps in Shiny gets messy very quickly (from experience)
- [ArcGIS Online](https://www.esri.com/en-us/c/product/arcgis-online)
    - Many at DOT are very familiar with Esri's suite of products, and it includes a variety of tools to make web maps
    - DOT already owns a license to it
    - It has the ability to automatically query and update GeoJSON feeds
    - However, ArcGIS Online has many limitations for GeoJSON (eg. not allowing multiple Feature types to be rendered from the same GeoJSON, not interpretting complicated custom properties, etc.) that make it difficult to work with the WZDx specification
    - Scripting has to be done in a custom language called [ArcGIS Arcade](https://developers.arcgis.com/arcade/), which no one I've talked to seems to really know anything about...
- [PowerBI](https://www.microsoft.com/en-us/power-platform/products/power-bi)
    - Integrates with software commonly used at DOT (Microsoft 365, Teams, etc.)
    - Data visualization seems very powerful
    - Build on MS software so maintenance wouldn't be too much work in the future
    - The online version seems to be relatively simple when adding custom data, necessitating downloading the desktop version (which means anyone in the future would have to ask OCIO to install it for them)
    - Seems to be more tailored towards analytics rather than geospatial data

## What we haven't tried (yet)
If anyone has any recommendations for things to try out, let me know!

- [SharePoint Framework (SPFx)](https://learn.microsoft.com/en-us/sharepoint/dev/spfx/sharepoint-framework-overview)
    - Client-side JS for SharePoint sites, MS Teams, etc.
    - Would need a separately-developed backend
    - [Examples seem promising?](https://github.com/pnp/spfx-reference-scenarios/tree/main/samples/contoso-retail-demo/)
- [Commercial Cloud Infrastructure (DOT-managed Amazon Web Services, Microsoft Azure, Google Cloud)](https://usdot.sharepoint.com/sites/volpe-vnet-ProjectManagement/SitePages/Cloud-Computing-Resources.aspx#guide-to-computing-resources)
    - Would be used for deployment
    - The page on V-net with links to info on this leads to [a picture of a blueberry](https://cdn.hubblecontent.osi.office.net/m365content/publish/00979827-f716-4dc8-ba2d-0b32111020fd/179658541.jpg) and [google.com](https://google.com/)...
    - [Definitely possible](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python) to deploy a Python web app
- [cloud.gov](https://cloud.gov/)
    - An alternative to commercial cloud infrastructure
    - Cloud services managed by GSA
    - [Seems expensive](https://cloud.gov/pricing/) and I'm not sure if Volpe/DOT has access to it already
    - When I asked around, seems like it's not used very much...
