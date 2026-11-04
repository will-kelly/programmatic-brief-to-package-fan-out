# Deploys

## Zero-downtime deploys {#zero-downtime}

By default, Render keeps the old instance serving traffic until the new one is healthy, so web services deploy without downtime. Services with an attached persistent disk are the exception: Render stops the old instance before starting the new one, so there is a short gap.
