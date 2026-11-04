# Blueprint YAML reference

## File location {#file-location}

A Blueprint is defined in a file named render.yaml. By default, Render looks for it at the root of your repository.

## Top-level fields {#top-level}

The top-level `services` list defines web services, private services, background workers, cron jobs, and Key Value instances. Each service needs a `type` and a `name`. Render Postgres databases are defined in the top-level `databases` list. Environment groups are defined under `envVarGroups`.

## Service fields {#service-fields}

Common service fields include `runtime`, `plan`, `region`, `buildCommand`, `startCommand`, `envVars`, `autoDeploy`, and `healthCheckPath`. A cron job also needs a `schedule`.
