# Web services

A web service runs your app and gives it a public onrender.com URL.

## Port binding {#port-binding}

Your app must bind to host 0.0.0.0 on the port given in the PORT environment variable. The default value of PORT is 10000.

## Health checks {#health-checks}

You can set a health check path. During a deploy, Render waits for this path to return a successful response before routing traffic to the new instance.
