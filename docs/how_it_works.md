# How This Dashboard Works

Before contuing, reading [the Django glossary](https://docs.djangoproject.com/en/4.2/glossary/) may be helpful.

This application is built using [Django](https://djangoproject.com), a Python framework for rending database-backed websites. Specifically, it uses the Model-Template-View model, meaning that when a browser makes a request, the following steps happen:
- The request is received by server, and passes it to the appropriate view (eg. the type of page to be rendered)
- The view requests data from the model (eg. gets the specific data from the database tables)
- The model sends back the applicable information to the view
- The view passes the applicable data to the template
- The template fills in the data in the relevant positions, then passes it back to the view
- The view returns the finished HTML page to the user's browser.

All this happens on the server, and all a user sees is a rendered page with data. This process allows the page to be dynamically generated, rather than having to be statically updated.

## Application Structure

The dashboard is split into 4 main "apps":

- Dashboard
- API
- Archive
- Docs

Each app contains it's own models, views, and templates. Furthermore, each app can create scipts with command line interface (CLI) functionality.

The exact, technical details of each app can be found in the admin interface. The following is a human-readable explanation of how everything connects together.

### Dashboard

This is the primary app. It contains the models for each feed (a representation of the data stored in the [WZDx Feed Registry](https://datahub.transportation.gov/Roadways-and-Bridges/Work-Zone-Data-Exchange-WZDx-Feed-Registry/69qe-yiui/data_preview)), feed data, and feed statuses. These are routinely updated using cron jobs, or scripts that run at regular intervals. These update the feed model, query feed URLs to gather feed data, and check the status of these feeds.

The two primary views for this app are the "list view" and "detail view." The list view uses the feed model to create the general table with a quick overview of all feed information, and the detail view includes fine-grained details for each feed.

There is one template for each type of view.

In addition to this, the dashboard app also implements the "sendemail" script, which uses the data from the relevant models to send status emails.

### API

The API app uses a popular Django plugin, [Django REST Framework](https://www.django-rest-framework.org/), to set up useful REST APIs. These are useful for exposing specific data that can then be ingested by other apps or uses. For example, the API app exposes the details needed to create the interactive maps in the dashboard app.

### Archive

The archive app was made as a temporary stopgap measure to ensure feed data is routinely saved. It implements the "archivefeed" script, which saves information from the "feed data" model (in the dashboard app) separately in the archive model, allowing for continuous storage of feed data.

Similarly to the dashboard app, it implements a list and detail view.

### Docs

The docs app is what stores the documentation! Primarily, it stores each documentation page as an entry in a model, stored with page metadata and the page text (in Markdown format).

This app implements a generic "render docs" view, as well as an edit and delete view for every documentation page. It also exposes a "create docs" page.
